import csv
import json
import os
import pickle
import queue
import random
import socket
import threading
import time
import types
import warnings

import cv2
import numpy as np
import torch
from robomaster import robot, blaster, camera, led
from torchvision.models import detection
import torchvision.transforms.v2 as transforms
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Tuple, Union, Any

# torchvision avisa de que ToTensor() está obsoleto; el resultado es el mismo
warnings.filterwarnings('ignore', message=r'The transform `ToTensor\(\)` is deprecated')


def connect(connection='networking', auto=True):
    """Connect to the RoboMaster and return the robot object.

    Run connect.py once and scan the QR code so the robot joins your network.
    In 'networking' mode the robot is found by the serial number saved in
    'serial_number.txt' (created by connect.py).
    :param connection: 'networking' (router), 'wifi' (direct Wi-Fi) or 'usb'.
    :param auto: con 'networking', pasar a wifi directo si falta serial_number.txt o el
                 portátil está en la wifi del robot. False respeta el modo pedido.
    :return: ep_robot, a connected RoboMaster object.
    """
    conn_types = {'networking': 'sta', 'wifi': 'ap', 'usb': 'rndis'}

    # serial_number.txt se busca en la carpeta actual y junto a este fichero
    ruta = 'serial_number.txt'
    if not os.path.isfile(ruta):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serial_number.txt')
    # Sin serial_number.txt (no se ha usado connect.py) se conecta por wifi directo al robot.
    # Con él, si el portátil está en la wifi del propio robot (IP 192.168.2.x), también: en esa
    # red no hay router y el modo networking no lo encuentra.
    if connection == 'networking' and auto:
        if not os.path.isfile(ruta):
            connection = 'wifi'
        elif hasattr(robot, '__file__'):
            ip = ip_hacia('192.168.2.1')
            if ip is not None and ip.startswith('192.168.2.'):
                print(f'El portátil está en la wifi del robot ({ip}): se usa wifi directo y no serial_number.txt')
                connection = 'wifi'
    print(f'Conexion: {connection}')

    # In networking mode the robot is identified by its serial number
    serial_number = None
    if connection == 'networking':
        with open(ruta, 'r') as f:
            serial_number = f.read().strip()

    # En wifi directo el robot es 192.168.2.1: el portátil tiene que estar en su red.
    # Se comprueba antes de conectar (solo con el SDK real, no con el simulado).
    if connection == 'wifi' and hasattr(robot, '__file__'):
        ip = ip_hacia('192.168.2.1')
        if ip is not None and not ip.startswith('192.168.2.'):
            raise ConnectionError(f'el portátil no está en la wifi del robot (su IP es {ip}). Conéctese a la '
                                  'red RMEP-... del robot y vuelva a lanzar el script')

    # Start the connection
    ep_robot = robot.Robot()
    try:
        ep_robot.initialize(conn_type=conn_types[connection], sn=serial_number)
    except Exception as e:
        # El SDK falla con errores poco claros (incluso un TypeError) si no encuentra el robot
        raise ConnectionError(f'no se puede conectar con el robot en modo {connection} ({e!r}). Compruebe que '
                              'está encendido, con la pestaña de conexión en ese modo, y que el portátil está '
                              'en su red') from None
    return ep_robot


def ip_hacia(destino):
    """IP local que usaría el portátil para llegar a `destino` (no envía nada), o None."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((destino, 20020))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return None


def new_history() -> dict:
    """Empty training history: losses per epoch, best validation loss and last finished epoch."""
    return {'train_loss': [], 'valid_loss': [], 'lr': [], 'best_value': np.inf, 'current_epoch': 0}


class _UnpicklerNumpy1(pickle.Unpickler):
    """Lee con numpy 1.x objetos guardados con numpy 2.x, que movió numpy.core a numpy._core."""

    def find_class(self, module, name):
        if module == 'numpy._core' or module.startswith('numpy._core.'):
            module = 'numpy.core' + module[len('numpy._core'):]
        return super().find_class(module, name)


_PICKLE_NUMPY1 = types.SimpleNamespace(__name__='pickle', Unpickler=_UnpicklerNumpy1, load=pickle.load)


def torch_load_cpu(path: str) -> Any:
    """Load a checkpoint onto the CPU (works even if it was saved on a GPU)."""
    # El checkpoint guarda también el estado de numpy y random: desde PyTorch 2.6 hace falta weights_only=False
    try:
        return torch.load(path, map_location='cpu', weights_only=False)
    except ModuleNotFoundError as e:
        # Guardado en JupyterHub con numpy 2 y leído en el laboratorio (Python 3.8, numpy 1.x)
        if 'numpy._core' not in str(e):
            raise
        return torch.load(path, map_location='cpu', weights_only=False, pickle_module=_PICKLE_NUMPY1)


def load_checkpoint(path: str, model: Any, device: torch.device, optimizer: torch.optim = None) -> Tuple[Any, Any, dict]:
    """Load model weights, optimizer and RNG state from a checkpoint (to resume training or to test)."""
    checkpoint = torch_load_cpu(path)

    # Model weights
    model.load_state_dict({**model.state_dict(), **checkpoint.get('model', {})})

    # Random-number-generator state (single device: no multi-GPU here)
    if 'rng_state' in checkpoint:
        torch.set_rng_state(checkpoint['rng_state'])
    if torch.cuda.is_available() and checkpoint.get('cuda_rng_state') is not None:
        torch.cuda.set_rng_state(checkpoint['cuda_rng_state'])
    if 'numpy_rng_state' in checkpoint:
        np.random.set_state(checkpoint['numpy_rng_state'])
    if 'python_rng_state' in checkpoint:
        random.setstate(checkpoint['python_rng_state'])

    # Optimizer state (only needed to resume training)
    if optimizer is not None and 'optimizer' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer'])
        for state in optimizer.state.values():
            for k, v in state.items():
                if torch.is_tensor(v):
                    state[k] = v.to(device)

    history = checkpoint.get('history', new_history())
    return model, optimizer, history


def torchvision_model(model_name: str, pretrained: bool = False, num_classes: int = 2) -> Any:
    """Build a torchvision detection model and adapt its head to `num_classes` (0=background, 1=object)."""
    model_dict = {
        'faster_rcnn_v1': detection.fasterrcnn_resnet50_fpn,
        'faster_rcnn_v2': detection.fasterrcnn_resnet50_fpn_v2,
        'faster_rcnn_v3': detection.fasterrcnn_mobilenet_v3_large_fpn,
        'retinanet_v1': detection.retinanet_resnet50_fpn,
        'retinanet_v2': detection.retinanet_resnet50_fpn_v2,
        'ssd_v1': detection.ssd300_vgg16,
        'ssd_v2': detection.ssdlite320_mobilenet_v3_large,
    }
    assert model_name in model_dict, f"Unknown model '{model_name}'. Choose one of: {list(model_dict)}"

    # Load the architecture (optionally with COCO pre-trained weights)
    model = model_dict[model_name](weights='COCO_V1' if pretrained else None)

    # Replace the classification head so it predicts OUR number of classes
    if 'faster_rcnn' in model_name:
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = detection.faster_rcnn.FastRCNNPredictor(in_features, num_classes)
    elif 'retinanet' in model_name:
        in_features = model.head.classification_head.cls_logits.in_channels
        num_anchors = model.head.classification_head.num_anchors
        model.head.classification_head = detection.retinanet.RetinaNetClassificationHead(in_features, num_anchors, num_classes)
    elif model_name == 'ssd_v1':
        in_features = [module.in_channels for module in model.head.classification_head.module_list]
        num_anchors = model.anchor_generator.num_anchors_per_location()
        model.head.classification_head = detection.ssd.SSDClassificationHead(in_features, num_anchors, num_classes)
    elif model_name == 'ssd_v2':
        in_features = [module[0][0].in_channels for module in model.head.classification_head.module_list]
        num_anchors = model.anchor_generator.num_anchors_per_location()
        model.head.classification_head = detection.ssd.SSDClassificationHead(in_features, num_anchors, num_classes)
    return model


def get_model(model_name: str, model_path: str = '', num_classes: int = 2, lr_data: list = None,
              pretrained: bool = False, use_gpu: bool = False) -> Tuple[Any, Any, dict, torch.device]:
    """Create the model (and optimizer) and, if a checkpoint exists at `model_path`, resume from it."""
    device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
    model = torchvision_model(model_name, pretrained, num_classes).to(device)

    # Optimizer (only when training, i.e. when learning-rate settings are given)
    if lr_data:
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=lr_data[0], momentum=lr_data[1], weight_decay=lr_data[2])
    else:
        optimizer = None

    # Resume from a checkpoint if one is found
    if os.path.isfile(model_path):
        model, optimizer, history = load_checkpoint(model_path, model, device, optimizer)
        print(f"Resumed from '{model_path}' (epoch {history['current_epoch']}).")
    else:
        history = new_history()
        print(f"No checkpoint at '{model_path}'. Starting from scratch.")
    return model, optimizer, history, device


def get_transform(resize_shape: Union[tuple, None] = None) -> transforms.Compose:
    """Turn an image into a float tensor in [0, 1]. Detection models normalise internally, so we do NOT normalise here."""
    t = [transforms.ToTensor()]
    if resize_shape:
        t.append(transforms.Resize(resize_shape, antialias=True))
    return transforms.Compose(t)


def resize_boxes(boxes: Any, resize_shape: tuple, image_shape: tuple) -> Any:
    """Rescale [x_min, y_min, x_max, y_max] boxes when the image is resized (height, width)."""
    scale_h, scale_w = resize_shape[0] / image_shape[0], resize_shape[1] / image_shape[1]
    boxes[:, [0, 2]] *= scale_w
    boxes[:, [1, 3]] *= scale_h
    return boxes


def predict(ep_robot, model, resize_shape=None):
    """Capture one camera frame, run the detector on it and return the results.

    Handles the whole inference pipeline: frame capture, BGR->RGB, pre-processing
    (get_transform), model inference and post-processing (predictions moved to
    CPU/NumPy and boxes scaled back to the original image size).
    :param ep_robot: connected RoboMaster object (see connect()).
    :param model: trained detection model (see get_model()).
    :param resize_shape: (height, width) to resize the image for the model, or None.
    :return: (image, prediction) — the original-size RGB image and a dict of NumPy
             arrays 'boxes' (N, 4 as [x_min, y_min, x_max, y_max]), 'scores' (N,), 'labels' (N,).
    """
    # Grab one frame from the robot camera
    ep_camera = ep_robot.camera
    ep_camera.start_video_stream(display=False)
    image = ep_camera.read_cv2_image()              # BGR image, shape (height, width, 3)
    ep_camera.stop_video_stream()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # RGB image, shape (height, width, 3)

    # Make predictions
    device = next(model.parameters()).device
    transform = get_transform(resize_shape)
    model.eval()
    with torch.no_grad():
        output = model([transform(image).to(device)])[0]

    # Bring the predictions to CPU/NumPy so they are easy to work with
    prediction = {key: value.detach().cpu().numpy() for key, value in output.items()}

    # Scale predictions back to the original image size if resize was applied
    if resize_shape is not None:
        prediction['boxes'] = resize_boxes(prediction['boxes'], image.shape[:2], resize_shape)

    return image, prediction


def auto_aim(image, box) -> float:
    """Yaw angle (degrees) from the image centre to the centre of a detected box.

    Rotating the gimbal by this angle brings the target to the middle of the view.
    :param image: image the box was detected on, shape (height, width, 3).
    :param box: detected box as [x_min, y_min, x_max, y_max].
    :return: alpha, yaw angle in degrees (negative = left, positive = right).
    """
    height, width = image.shape[:2]

    # Horizontal offset (pixels) between the box centre and the image centre
    box_center_x = (box[0] + box[2]) / 2
    offset = box_center_x - width / 2

    # Turn that pixel offset into an angle using the camera geometry. arctan is
    # an odd function, so the sign of `offset` already tells left from right.
    focal = width / (2 * np.tan(np.pi / 3))                 # ~120º field-of-view lens
    alpha = np.rad2deg(np.arctan(offset / focal)) * 90 / 120  # measured FOV is closer to 90º
    return alpha


def auto_pitch(image, box, altura=0.5) -> float:
    """Pitch (grados) desde el centro de la imagen hasta un punto de la caja; > 0 si está por encima.

    Misma geometría que auto_aim, en vertical. `altura` elige el punto de la caja al que
    se apunta: 0 el borde superior, 0,5 el centro y 1 el borde inferior.
    """
    height, width = image.shape[:2]
    y = box[1] + altura * (box[3] - box[1])
    offset = height / 2 - y
    focal = width / (2 * np.tan(np.pi / 3))
    return float(np.rad2deg(np.arctan(offset / focal)) * 90 / 120)


def tamano_angular(image, box) -> Tuple[float, float]:
    """Ancho y alto de la caja en grados, con la misma geometría que auto_aim."""
    ancho = auto_aim(image, [box[2], 0, box[2], 0]) - auto_aim(image, [box[0], 0, box[0], 0])
    alto = auto_pitch(image, box, 0.0) - auto_pitch(image, box, 1.0)
    return float(abs(ancho)), float(abs(alto))


def plot_predictions(image, prediction, target_id, score_threshold=0.5, path='predictions'):
    """Draw the predicted boxes (above score_threshold) on the image and save it.

    Same plotting style as week2's test.ipynb, but it saves one figure per
    target (file name = target id) instead of showing it, since the demo runs
    as a script and not in a notebook.
    :param image: RGB image the predictions were computed on.
    :param prediction: dict with NumPy arrays 'boxes' (N, 4) and 'scores' (N,).
    :param target_id: identifier of the target; used as the output file name.
    :param score_threshold: minimum confidence to draw a box.
    :param path: folder where the figures are saved (created if it does not exist).
    """
    boxes = prediction['boxes']
    scores = prediction['scores']

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(image)
    ax.axis('off')
    ax.set_title(f'Target {target_id}')
    for (x_min, y_min, x_max, y_max), score in zip(boxes, scores):
        if score < score_threshold:
            continue
        ax.add_patch(Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                               linewidth=2, edgecolor='lime', facecolor='none'))
        ax.text(x_min, y_min - 5, f'{score:.2f}', color='white', fontsize=10,
                bbox=dict(facecolor='black', alpha=0.6, pad=1))
    os.makedirs(path, exist_ok=True)
    fig.savefig(os.path.join(path, f'{target_id}.png'), bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# Añadidos del grupo 2 para la demo del Bloque 3
# =============================================================================

# El enunciado prohíbe subir la velocidad del robot: estos son los valores por
# defecto del SDK y se usan como máximo en todos los movimientos.
VEL_XY_MAX = 0.5        # m/s, chasis
VEL_Z_MAX = 30          # º/s, giro del chasis
VEL_GIMBAL_MAX = 30     # º/s, gimbal (pitch y yaw)

COLORES_LED = {
    'moviendo': (0, 0, 255),
    'buscando': (255, 160, 0),
    'apuntando': (255, 60, 0),
    'disparando': (255, 0, 0),
    'hecho': (0, 255, 0),
    'nada': (120, 0, 255),
    'obstaculo': (255, 255, 0),
    'fin': (0, 255, 120),
    'apagado': (0, 0, 0),
}


def limitar(valor, maximo):
    """Recorta una velocidad a [-maximo, maximo] conservando el signo."""
    return max(-maximo, min(maximo, valor))


def buscar_modelo(ruta):
    """Devuelve la primera ruta existente del checkpoint entre las candidatas habituales.

    En el laboratorio el script se lanza desde /home/PIDS/robomaster; en el
    repositorio, desde esta carpeta o desde la raíz. Se prueba la ruta tal cual,
    relativa a esta carpeta y relativa a la raíz del repositorio.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    candidatas = [ruta, os.path.join(aqui, ruta), os.path.join(aqui, '..', '..', ruta)]
    for c in candidatas:
        if os.path.isfile(c):
            return os.path.abspath(c)
    raise FileNotFoundError(f'No se encuentra el modelo en ninguna de estas rutas: {candidatas}')


def cargar_modelo(model_name, ruta, use_gpu=True):
    """Carga el detector entrenado y comprueba que los pesos se han leído de verdad.

    load_checkpoint() ignora en silencio un checkpoint sin la clave 'model', y
    entonces la cabeza quedaría con pesos aleatorios: aquí se comprueba.
    """
    ruta = buscar_modelo(ruta)
    checkpoint = torch_load_cpu(ruta)
    assert 'model' in checkpoint, f"El checkpoint {ruta} no tiene la clave 'model'"
    faltan = set(torchvision_model(model_name, False, 2).state_dict()) - set(checkpoint['model'])
    assert not faltan, f'Al checkpoint le faltan {len(faltan)} pesos de {model_name}, por ejemplo {sorted(faltan)[:3]}'
    del checkpoint
    model, _, history, device = get_model(model_name=model_name, model_path=ruta, num_classes=2,
                                          lr_data=None, pretrained=False, use_gpu=use_gpu)
    model.eval()
    if device.type == 'cpu':
        torch.set_num_threads(os.cpu_count() or 1)
    return model, device, history


def detectar(model, image, resize_shape=None):
    """Aplica el detector a una imagen RGB ya capturada.

    Es la segunda mitad de predict(): separada para poder capturar con la
    cámara abierta todo el recorrido y para medir el tiempo de inferencia.
    :return: (prediction, ms) con las mismas claves que predict().
    """
    device = next(model.parameters()).device
    transform = get_transform(resize_shape)
    inicio = time.perf_counter()
    with torch.no_grad():
        output = model([transform(image).to(device)])[0]
    if device.type == 'cuda':
        torch.cuda.synchronize()
    ms = (time.perf_counter() - inicio) * 1000
    prediction = {key: value.detach().cpu().numpy() for key, value in output.items()}
    if resize_shape is not None:
        prediction['boxes'] = resize_boxes(prediction['boxes'], image.shape[:2], resize_shape)
    return prediction, ms


def calentar(model, resize_shape=None, forma=(720, 1280, 3)):
    """Primera inferencia en vacío: la primera llamada es mucho más lenta que las siguientes."""
    _, ms = detectar(model, np.zeros(forma, dtype=np.uint8), resize_shape)
    return ms


class Camara:
    """Cámara del robot con el vídeo abierto durante toda la demo.

    predict() abre y cierra el vídeo en cada captura, lo que tarda y puede
    devolver un fotograma antiguo. Aquí se abre una vez y se lee siempre el
    fotograma más reciente, tras esperar a que el gimbal se quede quieto.
    """

    def __init__(self, ep_robot, espera=0.5):
        self.ep_camera = ep_robot.camera
        self.espera = espera
        self.ep_camera.start_video_stream(display=False, resolution=camera.STREAM_720P)
        time.sleep(1.0)

    def capturar(self, espera=None):
        """Fotograma más reciente en RGB. `espera` (s) deja quieta la imagen; 0 al seguir a un robot."""
        espera = self.espera if espera is None else espera
        if espera > 0:
            time.sleep(espera)
        try:
            image = self.ep_camera.read_cv2_image(timeout=3, strategy='newest')
        except TypeError:
            image = self.ep_camera.read_cv2_image(timeout=3)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def cerrar(self):
        self.ep_camera.stop_video_stream()


def seleccionar(prediction, umbral):
    """Detecciones con confianza >= umbral, de mayor a menor confianza: lista de (caja, confianza)."""
    orden = np.argsort(-prediction['scores'])
    return [(prediction['boxes'][i], float(prediction['scores'][i])) for i in orden
            if prediction['scores'][i] >= umbral]


def mas_centrada(image, objetivos):
    """De una lista de (caja, confianza), la que está más cerca del centro horizontal."""
    return min(objetivos, key=lambda o: abs(auto_aim(image, o[0])))


def es_nuevo(angulo, ya_atacados, tolerancia):
    """True si ningún objetivo ya atacado en esta parada está a menos de `tolerancia` grados."""
    return all(abs(angulo - a) > tolerancia for a in ya_atacados)


def disparar(ep_robot, veces, pausa=0.3):
    """Dispara `veces` tiros de infrarrojo, de uno en uno para no saturar el blaster."""
    for _ in range(veces):
        ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1)
        time.sleep(pausa)


def dibujar_evidencia(image, prediction, umbral, ruta, titulo, min_score=0.3, objetivo=None, guardar=True):
    """Guarda la imagen con las cajas predichas y su confianza dibujadas encima.

    Verde: confianza >= umbral (se acepta). Naranja: entre min_score y el umbral
    (se descarta, pero se dibuja para poder analizarlo en la memoria). La caja
    `objetivo`, si se da, es aquella a la que se dispara y se marca con una cruz.
    Con guardar=False solo se dibuja y se devuelve (Registro la escribe en otro hilo).
    """
    salida = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    for (x0, y0, x1, y1), score in zip(prediction['boxes'], prediction['scores']):
        if score < min_score:
            continue
        color = (0, 200, 0) if score >= umbral else (0, 140, 255)
        cv2.rectangle(salida, (int(x0), int(y0)), (int(x1), int(y1)), color, 3)
        etiqueta = f'robot {score:.2f}'
        (w, h), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        y_txt = max(int(y0) - 6, h + 40)
        cv2.rectangle(salida, (int(x0), y_txt - h - 6), (int(x0) + w + 6, y_txt + 4), color, -1)
        cv2.putText(salida, etiqueta, (int(x0) + 3, y_txt), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    if objetivo is not None:
        cx, cy = int((objetivo[0] + objetivo[2]) / 2), int((objetivo[1] + objetivo[3]) / 2)
        cv2.drawMarker(salida, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 40, 3)
    alto, ancho = salida.shape[:2]
    cv2.line(salida, (ancho // 2, 34), (ancho // 2, alto), (200, 200, 200), 1)
    cv2.rectangle(salida, (0, 0), (ancho, 34), (0, 0, 0), -1)
    cv2.putText(salida, titulo, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if guardar:
        os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
        cv2.imwrite(ruta, salida)
    return salida


class Registro:
    """Carpeta de evidencias de una ejecución: imágenes, registro.csv y resumen.json.

    Cada imagen a la que se aplica el detector se guarda dos veces: tal cual
    (para analizarla o anotarla después) y con las cajas dibujadas. Los JPEG se
    escriben en un hilo aparte para no frenar el seguimiento de un robot, que
    analiza varias imágenes por segundo; cerrar() espera a que estén todos escritos.
    """

    CAMPOS = ['n', 'momento', 'parada', 'fase', 'yaw', 'pitch', 'ms_inferencia', 'n_cajas_0_3',
              'n_aceptadas', 'confianzas', 'cajas', 'objetivo_yaw', 'distancia_m', 'disparos', 'imagen']

    def __init__(self, carpeta='evidencias', umbral=0.5, mostrar=False):
        self.mostrar = mostrar   # ver cada imagen analizada en una ventana
        base = os.path.join(carpeta, time.strftime('%Y%m%d_%H%M%S'))
        self.carpeta, i = base, 2
        while os.path.exists(self.carpeta):   # dos ejecuciones en el mismo segundo
            self.carpeta, i = f'{base}_{i}', i + 1
        os.makedirs(os.path.join(self.carpeta, 'originales'), exist_ok=True)
        self.umbral = umbral
        self.n = 0
        self.filas = []
        self.f = open(os.path.join(self.carpeta, 'registro.csv'), 'w', newline='', encoding='utf-8')
        self.w = csv.DictWriter(self.f, fieldnames=self.CAMPOS)
        self.w.writeheader()
        self._cola = queue.Queue()
        self._escritor = threading.Thread(target=self._escribir, daemon=True)
        self._escritor.start()

    def _escribir(self):
        while True:
            tarea = self._cola.get()
            if tarea is None:
                return
            ruta, imagen_bgr = tarea
            try:
                cv2.imwrite(ruta, imagen_bgr)
            except Exception as e:   # una evidencia perdida no detiene la demo
                print(f'[aviso] no se pudo guardar {ruta}: {e!r}')

    def imagen(self, image, prediction, ms, parada, fase, yaw, pitch, objetivo=None, objetivo_yaw=None, disparos=0,
               distancia=None):
        """Guarda una imagen analizada y su fila del registro; devuelve el nombre del fichero."""
        self.n += 1
        nombre = f'{self.n:03d}_{parada}_{fase}_yaw{yaw:+.0f}.jpg'
        self._cola.put((os.path.join(self.carpeta, 'originales', nombre), cv2.cvtColor(image, cv2.COLOR_RGB2BGR)))
        titulo = f'{self.n:03d} {parada} {fase} yaw {yaw:+.1f} | umbral {self.umbral:.2f} | {ms:.0f} ms'
        ruta = os.path.join(self.carpeta, nombre)
        dibujada = dibujar_evidencia(image, prediction, self.umbral, ruta, titulo, objetivo=objetivo, guardar=False)
        self._cola.put((ruta, dibujada))
        if self.mostrar:
            self.ver(dibujada)
        scores = prediction['scores']
        visibles = scores >= 0.3
        fila = {
            'n': self.n, 'momento': time.strftime('%H:%M:%S'), 'parada': parada, 'fase': fase,
            'yaw': round(yaw, 1), 'pitch': round(pitch, 1), 'ms_inferencia': round(ms, 1),
            'n_cajas_0_3': int(visibles.sum()), 'n_aceptadas': int((scores >= self.umbral).sum()),
            'confianzas': ' '.join(f'{s:.3f}' for s in scores[visibles]),
            'cajas': json.dumps([[round(float(v), 1) for v in b] for b in prediction['boxes'][visibles]]),
            'objetivo_yaw': '' if objetivo_yaw is None else round(objetivo_yaw, 1),
            'distancia_m': '' if distancia is None else round(distancia, 2),
            'disparos': disparos, 'imagen': nombre,
        }
        self.w.writerow(fila)
        self.f.flush()
        self.filas.append(fila)
        return nombre

    def ver(self, imagen_bgr, ancho=960):
        """Muestra la imagen con sus cajas en una ventana, sin parar la demo."""
        try:
            alto = int(imagen_bgr.shape[0] * ancho / imagen_bgr.shape[1])
            cv2.imshow('PIDS - detecciones', cv2.resize(imagen_bgr, (ancho, alto)))
            cv2.waitKey(1)
        except cv2.error as e:
            print(f'[aviso] no se puede abrir la ventana de imágenes: {e}')
            self.mostrar = False

    def cerrar(self, resumen):
        self._cola.put(None)
        self._escritor.join(timeout=120)
        self.f.close()
        if self.mostrar:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass
        with open(os.path.join(self.carpeta, 'resumen.json'), 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=1)


def liberar_cerrojo_sdk(ep_robot, error):
    """Arregla un fallo del SDK tras rechazar una acción.

    En robomaster/action.py, send_action lanza «Robot is already performing ...»
    sin soltar su cerrojo (threading.Lock). La siguiente orden y el aviso de fin
    de la acción en curso se quedan esperándolo para siempre y el robot deja de
    responder. Solo se suelta justo después de ese error.
    """
    if 'already performing' not in str(error):
        return
    cerrojo = getattr(getattr(ep_robot, '_action_dispatcher', None), '_in_progress_mutex', None)
    if cerrojo is not None and cerrojo.locked():
        try:
            cerrojo.release()
        except RuntimeError:
            pass


def ejecutar_accion(ep_robot, crear, timeout, que, durante=None):
    """Lanza una acción del SDK y espera a que acabe, como mucho `timeout` segundos.

    wait_for_completed() sin tiempo máximo espera para siempre si el robot no
    responde (batería baja, conexión perdida): aquí se convierte en un error que
    detiene la demo de forma segura.

    Con `durante`, mientras la acción no ha acabado se llama a durante() una y otra
    vez (por ejemplo, para analizar imágenes con el chasis en marcha).
    """
    try:
        accion = crear()
    except Exception as e:
        liberar_cerrojo_sdk(ep_robot, e)
        raise RuntimeError(f'{que}: {e}')
    if durante is not None:
        limite = time.monotonic() + timeout
        while not getattr(accion, 'is_completed', True) and time.monotonic() < limite:
            durante()
    if not accion.wait_for_completed(timeout=timeout):
        raise RuntimeError(f'{que}: no ha terminado en {timeout:.0f} s (¿batería baja o robot desconectado?)')


class Odometria:
    """Posición del chasis (x adelante, y derecha, en m) respecto a donde estaba al crearla.

    Usa chassis.sub_position(cs=0). Si el SDK no la da, `activa` es False.
    """

    def __init__(self, chassis, freq=20):
        self.chassis, self.ultima = chassis, None
        try:
            self.activa = chassis.sub_position(cs=0, freq=freq, callback=self._leer) is not False
        except Exception as e:
            print(f'[aviso] sin odometría del chasis: {e!r}')
            self.activa = False

    def _leer(self, info):
        self.ultima = tuple(float(v) for v in info[:3])

    def esperar(self, maximo=2.0, dormir=time.sleep, reloj=time.monotonic):
        """Primera lectura (o None si no llega en `maximo` s)."""
        fin = reloj() + maximo
        while self.activa and self.ultima is None and reloj() < fin:
            dormir(0.05)
        return self.ultima

    def cerrar(self):
        if self.activa:
            try:
                self.chassis.unsub_position()
            except Exception:   # el SDK falla si no ha llegado ninguna lectura
                pass
            self.activa = False


def avanzar(ep_robot, x, y, velocidad, que='chasis', dormir=time.sleep, reloj=time.monotonic):
    """Avanza (x, y) metros sin girar con drive_speed, a `velocidad` m/s reales, midiendo con la odometría.

    chassis.move no sirve para ir rápido: el SDK no acepta menos de 0,5 y no convierte
    la velocidad a m/s reales (en el laboratorio, 0,5 dio unos 0,06 m/s). drive_speed sí
    va en m/s. Se frena en los últimos centímetros y se para a 1 cm del destino. drive_speed lleva
    un tiempo máximo de 0,5 s: si el programa deja de mandar órdenes, el robot se para solo.

    :return: (x, y) recorridos según la odometría, o None si no hay odometría (entonces
             no se mueve y hay que usar chassis.move).
    """
    distancia = (x * x + y * y) ** 0.5
    velocidad = limitar(velocidad, VEL_XY_MAX)
    odometria = Odometria(ep_robot.chassis)
    if odometria.esperar(dormir=dormir, reloj=reloj) is None:
        odometria.cerrar()
        return None
    x0, y0 = odometria.ultima[:2]
    ux, uy = x / distancia, y / distancia
    maximo = 2 * distancia / max(velocidad, 0.05) + 5
    limite = reloj() + maximo
    try:
        while True:
            px, py = odometria.ultima[0] - x0, odometria.ultima[1] - y0
            falta = (x - px) * ux + (y - py) * uy        # lo que queda a lo largo de la dirección pedida
            if falta <= 0.01:
                break
            if reloj() > limite:
                raise RuntimeError(f'{que}: no ha llegado en {maximo:.0f} s (lleva {distancia - falta:.2f} de '
                                   f'{distancia:.2f} m; ¿batería baja u obstáculo?)')
            # rampa de frenada: 3 m/s por metro que falta (a 0,5 m/s empieza a frenar a 17 cm), sin bajar de 0,08
            v = min(velocidad, max(0.08, 3.0 * falta))
            # corrige la deriva lateral respecto a la línea recta
            lateral = -(px * uy - py * ux)
            vx, vy = v * ux + 1.5 * lateral * uy, v * uy - 1.5 * lateral * ux
            norma = (vx * vx + vy * vy) ** 0.5
            if norma > VEL_XY_MAX:                         # nunca más de la velocidad máxima
                vx, vy = vx * VEL_XY_MAX / norma, vy * VEL_XY_MAX / norma
            ep_robot.chassis.drive_speed(x=vx, y=vy, z=0, timeout=0.5)
            dormir(0.05)
    finally:
        try:
            ep_robot.chassis.drive_speed(x=0, y=0, z=0)
        except Exception:
            pass
        dormir(0.3)   # última lectura con el robot ya parado
        final = odometria.ultima
        odometria.cerrar()
    return final[0] - x0, final[1] - y0


def mover_chasis(ep_robot, x, y, z, v_xy, v_z, que='chasis', durante=None, odometria=True):
    """Mueve el chasis (x adelante, y derecha, z giro a la izquierda) sin pasar de las velocidades máximas.

    Los avances sin giro van con avanzar() (velocidad real en m/s); los giros, los
    movimientos que mezclan avance y giro, los que llevan `durante` (vigilancia) o si no
    hay odometría, con chassis.move.
    :return: (x, y) medidos por la odometría en los avances, o None.
    """
    v_xy, v_z = limitar(v_xy, VEL_XY_MAX), limitar(v_z, VEL_Z_MAX)
    if odometria and (x or y) and not z and durante is None:
        medido = avanzar(ep_robot, x, y, v_xy, que)
        if medido is not None:
            return medido
        print('[aviso] sin odometría: el avance va con chassis.move, mucho más lento')
    # chassis.move: el SDK sube a 0,5 cualquier xy_speed menor, pero no son m/s reales
    tiempo = (x * x + y * y) ** 0.5 / 0.06 + abs(z) / v_z if (x or y) else abs(z) / v_z
    ejecutar_accion(ep_robot, lambda: ep_robot.chassis.move(x=x, y=y, z=z, xy_speed=v_xy, z_speed=v_z),
                    timeout=2 * tiempo + 5, que=que, durante=durante)
    return None


class Senales:
    """LED y sonido según el estado de la demo. Un fallo aquí nunca detiene la demo.

    El SDK solo admite un sonido a la vez: si el anterior sigue sonando, el
    nuevo se omite en lugar de enviarlo (ver liberar_cerrojo_sdk).
    """

    def __init__(self, ep_robot, sonidos=None, activo=True):
        self.ep_robot = ep_robot
        self.sonidos = sonidos or {}
        self.activo = activo
        self._accion = None   # último sonido o audio enviado

    def ocupado(self):
        return self._accion is not None and not getattr(self._accion, 'is_completed', True)

    def esperar_sonido(self, maximo):
        """Espera, como mucho `maximo` segundos, a que termine el sonido en curso."""
        fin = time.time() + maximo
        while self.ocupado() and time.time() < fin:
            time.sleep(0.1)

    def _reproducir(self, lanzar, que):
        """Envía el sonido si no hay otro sonando. Devuelve True si se ha enviado."""
        if self.ocupado():
            return False
        try:
            self._accion = lanzar()
            return self._accion is not None
        except Exception as e:
            liberar_cerrojo_sdk(self.ep_robot, e)
            print(f'[aviso] {que}: {e}')
            return False

    def estado(self, nombre, parpadeo=False):
        if not self.activo:
            return
        r, g, b = COLORES_LED[nombre]
        efecto = led.EFFECT_FLASH if parpadeo else led.EFFECT_ON
        try:
            self.ep_robot.led.set_led(comp=led.COMP_ALL, r=r, g=g, b=b, effect=efecto)
        except Exception as e:
            print(f'[aviso] LED: {e}')

    def sonido(self, nombre):
        if not self.activo or self.sonidos.get(nombre) is None:
            return
        self._reproducir(lambda: self.ep_robot.play_sound(self.sonidos[nombre], 1), 'sonido')

    def audio(self, fichero):
        """Reproduce un .wav (mono, 48 kHz) en el altavoz del robot sin esperar a que termine.

        El SDK sube el fichero al robot en cada llamada. Devuelve True si se ha enviado.
        """
        if not self.activo or not fichero or not os.path.isfile(fichero):
            return False
        return self._reproducir(lambda: self.ep_robot.play_audio(fichero), 'audio')


def nivel_bateria(ep_robot, espera=3.0):
    """Lee una vez el porcentaje de batería (None si no llega en `espera` segundos).

    Espera a la primera lectura antes de cancelar la suscripción: si se cancela
    antes, el SDK falla (dds.py, del_subject_info: AttributeError en `_task`).
    Un fallo al cancelar nunca detiene la demo.
    """
    lectura = {}

    def guardar(percent, *args):
        lectura['pct'] = percent

    try:
        ep_robot.battery.sub_battery_info(5, guardar)
    except Exception as e:
        print(f'[aviso] batería: {e}')
        return None
    fin = time.time() + espera
    while 'pct' not in lectura and time.time() < fin:
        time.sleep(0.1)
    try:
        ep_robot.battery.unsub_battery_info()
    except Exception as e:
        print(f'[aviso] batería, al cancelar la lectura: {e!r}')
    return lectura.get('pct')


def reloj_del_robot(ep_robot):
    """Reloj (s) para medir tiempos: el robot simulado lleva el suyo, con tiempo simulado."""
    try:
        reloj = vars(ep_robot).get('reloj')
    except TypeError:
        reloj = None
    return reloj if callable(reloj) else time.monotonic


# --- Fase 2: barrido continuo y memoria de robots atacados --------------------------

def distancia_estimada(image, box, altura_robot):
    """Distancia (m) al robot a partir del alto aparente de su caja y de su altura real.

    Es aproximada: depende de que la caja abarque el robot entero (las antenas y la
    torreta cuentan) y del modelo de cámara de auto_aim. Se calibra con ALTURA_ROBOT.
    """
    _, alto = tamano_angular(image, box)
    if alto <= 0.1:
        return None
    return float(altura_robot / (2 * np.tan(np.deg2rad(alto) / 2)))


def mover_pose(pose, x, y, z):
    """Posición del chasis tras move(x, y, z), a partir de `pose` = (X, Y, rumbo).

    Coordenadas del circuito: X hacia el frente inicial del robot, Y a su izquierda
    y rumbo en grados hacia la izquierda (como z). El chasis se traslada con el rumbo
    de partida y después gira; en las paradas conviene no mezclar giro y avance.
    """
    px, py, rumbo = pose
    r = np.deg2rad(rumbo)
    # y > 0 es a la derecha del robot, es decir, -Y en estas coordenadas
    px += x * np.cos(r) + y * np.sin(r)
    py += x * np.sin(r) - y * np.cos(r)
    return float(px), float(py), float(rumbo + z)


def punto_en_circuito(pose, yaw, distancia):
    """Punto del circuito a `distancia` m en la dirección del yaw del gimbal (> 0 a la derecha)."""
    px, py, rumbo = pose
    b = np.deg2rad(rumbo - yaw)
    return float(px + distancia * np.cos(b)), float(py + distancia * np.sin(b))


def ruta_barrido(barrido, campo_vision):
    """Puntos de giro de un barrido continuo que cubre los mismos ángulos que la lista `barrido`.

    Empieza en barrido[0], va al extremo más cercano (si están igual de lejos, al que
    aparece antes en la lista) y luego al otro. Si la lista cubre 360º (con el campo de
    visión útil), los extremos se dejan en ±(360 - campo_vision)/2, que basta para
    verlo todo sin girar de más.
    """
    inicio, bajo, alto = barrido[0], min(barrido), max(barrido)
    alto_primero = barrido.index(alto) < barrido.index(bajo)
    if alto - bajo + campo_vision >= 360:
        bajo, alto = -(360 - campo_vision) / 2, (360 - campo_vision) / 2
    if abs(abs(alto - inicio) - abs(bajo - inicio)) > 1e-9:
        alto_primero = abs(alto - inicio) < abs(bajo - inicio)
    extremos = [alto, bajo] if alto_primero else [bajo, alto]
    return [inicio] + [e for e in extremos if abs(e - inicio) > 0.5]


class Memoria:
    """Robots ya atacados (y detecciones que no se pudieron fijar), en coordenadas del circuito.

    El ángulo de una detección es preciso, pero su distancia (por el alto de la caja) no.
    Por eso la tolerancia es una elipse alrededor de la detección: `radio` m de lado y
    `radio + error_distancia * distancia` m a lo largo de la línea de visión desde el robot.
    Una detección dentro de la elipse de un robot anotado es ese mismo robot.

    Los rivales se mueven y son todos iguales: un robot atacado que se ha desplazado más
    del radio se tomará por uno nuevo y se le volverá a atacar. Es preferible a no disparar
    a un robot nuevo que pase cerca. Los descartes (detecciones que no se pudieron fijar) se
    olvidan a los `tiempo_descarte` s, para volver a intentarlo.
    """

    def __init__(self, radio=0.35, error_distancia=0.25, tiempo_memoria=None, tiempo_descarte=3.0):
        self.radio, self.error_distancia = radio, error_distancia
        self.tiempo_memoria, self.tiempo_descarte = tiempo_memoria, tiempo_descarte
        self.entradas = []   # dict(x, y, t, distancia, tipo, parada)

    def anotar(self, punto, t, distancia, tipo='atacado', parada=''):
        if punto is None:
            return
        self.entradas.append(dict(x=round(punto[0], 2), y=round(punto[1], 2), t=round(t, 2),
                                  distancia=None if distancia is None else round(distancia, 2),
                                  tipo=tipo, parada=parada))

    def conocido(self, punto, t, distancia=None, origen=None, tipos=None):
        """La entrada que coincide con `punto` (visto desde `origen`) en el instante `t`, o None.

        `tipos` limita la búsqueda a esos tipos de entrada (p. ej. solo 'descartado').
        """
        if punto is None:
            return None
        visual = None
        if origen is not None:
            v = np.array(punto, dtype=float) - np.array(origen, dtype=float)
            if np.hypot(*v) > 1e-6:
                visual = v / np.hypot(*v)
        for e in self.entradas:
            if tipos is not None and e['tipo'] not in tipos:
                continue
            limite = self.tiempo_descarte if e['tipo'] == 'descartado' else self.tiempo_memoria
            if limite is not None and t - e['t'] > limite:
                continue
            dif = np.array([e['x'] - punto[0], e['y'] - punto[1]])
            largo = self.radio + self.error_distancia * max(distancia or 0.0, e['distancia'] or 0.0)
            if visual is None:
                dentro = np.hypot(*dif) <= largo
            else:
                radial = float(dif @ visual)
                lateral = float(dif[0] * visual[1] - dif[1] * visual[0])
                dentro = (radial / largo) ** 2 + (lateral / self.radio) ** 2 <= 1
            if dentro:
                return e
        return None

    def atacados(self):
        return [e for e in self.entradas if e['tipo'] == 'atacado']
