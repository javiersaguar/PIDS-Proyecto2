"""Un solo trabajo de inferencia pendiente, con recuperación a CPU explícita."""
import json
import math
import threading
import time
import urllib.request
from pathlib import Path


def regla_auto(boxes, scores, width, height, umbral=0.95):
    """Índice de la caja válida que contiene la mira, tras reducirla un 20 %."""
    try:
        if not all(math.isfinite(float(v)) for v in (width, height, umbral)):
            return None
        if width <= 0 or height <= 0 or not 0 <= umbral <= 1:
            return None
        for i, (box, score) in enumerate(zip(boxes, scores)):
            if len(box) != 4 or not all(math.isfinite(float(v)) for v in (*box, score)):
                continue
            x1, y1, x2, y2 = box
            if score < umbral or score > 1 or x2 <= x1 or y2 <= y1:
                continue
            dx, dy = (x2 - x1) * .1, (y2 - y1) * .1
            if x1 + dx <= width / 2 <= x2 - dx and y1 + dy <= height / 2 <= y2 - dy:
                return i
    except (TypeError, ValueError):
        return None
    return None


class Detector(threading.Thread):
    """proveedor devuelve (RGB, monotonic); publicar recibe un dict con la imagen."""

    def __init__(self, proveedor, publicar, simulado=False, modelo_cpu=None):
        super().__init__(name='detector-mando', daemon=True)
        self.proveedor = proveedor
        self.publicar = publicar
        self.simulado = simulado
        self.parar = threading.Event()
        self.preferencia = 'gpu'
        self.modelo_cpu = Path(modelo_cpu or Path(__file__).resolve().parent.parent /
                               'models/faster_rcnn_v3/mando_pesos.pt')
        self._modelo = None
        self._probar_cpu = True
        self._gpu_desde = 0.0

    def cerrar(self):
        self.parar.set()
        if self.ident is not None:
            self.join(timeout=5)

    def configurar(self, config):
        self.preferencia = config.get('detector', 'gpu')

    def _cpu(self, image):
        from demo_utils import cargar_modelo, detectar
        if self._modelo is None:
            if not self._probar_cpu or not self.modelo_cpu.is_file():
                raise FileNotFoundError('Falta el checkpoint CPU faster_rcnn_v3: ' + str(self.modelo_cpu))
            self._probar_cpu = False
            self._modelo, _, _ = cargar_modelo('faster_rcnn_v3', str(self.modelo_cpu), use_gpu=False)
            import torch
            torch.set_num_threads(4)
        pred, ms = detectar(self._modelo, image)
        return dict(boxes=pred['boxes'].tolist(), scores=pred['scores'].tolist(), ms=ms)

    def _gpu(self, image):
        import cv2
        ok, jpeg = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                                [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise ValueError('No se pudo codificar la imagen para el detector')
        request = urllib.request.Request('http://127.0.0.1:8766/detectar', data=jpeg.tobytes(),
                                         headers={'Content-Type': 'image/jpeg'}, method='POST')
        with urllib.request.urlopen(request, timeout=2) as response:
            result = json.load(response)
        if len(result['boxes']) != len(result['scores']):
            raise ValueError('Respuesta de detección inválida')
        return result

    def run(self):
        ultimo = None
        while not self.parar.is_set():
            try:
                frame = self.proveedor()
                if frame is None:
                    self.parar.wait(.05)
                    continue
                image, instante = frame
                if instante == ultimo:
                    self.parar.wait(.02)
                    continue
                ultimo = instante
                aviso, origen = '', 'simulado'
                if self.simulado:
                    result = dict(boxes=[], scores=[], ms=0)
                    self.parar.wait(.05)
                else:
                    result = None
                    origen = 'cpu'
                    if self.preferencia == 'gpu' and time.monotonic() >= self._gpu_desde:
                        try:
                            result = self._gpu(image)
                            origen = 'gpu'
                        except Exception as error:
                            aviso = 'GPU no disponible. Alternativa CPU. ' + str(error)
                            self._gpu_desde = time.monotonic() + 5
                    if result is None:
                        result = self._cpu(image)
                result.update(width=image.shape[1], height=image.shape[0], image=image,
                              instante=instante, detector=origen, aviso=aviso)
                if not self.parar.is_set():
                    self.publicar(result)
            except Exception as error:
                if not self.parar.is_set():
                    self.publicar(dict(boxes=[], scores=[], ms=0, image=None, instante=0,
                                      width=0, height=0, detector='no disponible', aviso=str(error)))
                self.parar.wait(1)
