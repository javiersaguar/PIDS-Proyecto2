"""Demo del Bloque 3 con el detector en la GPU y la CPU de respaldo.

Es la misma demo que demo.py (mismo circuito, misma configuración de circuito.py y mismas
opciones), pero las imágenes se analizan en un proceso aparte que usa la GPU:

- demo.py corre en .venv (Python 3.8, el único que admite el SDK del robot) con PyTorch para
  CPU, porque el PyTorch de Python 3.8 no admite la RTX 5070 del portátil (unos 2,3 s por imagen);
- este script arranca mando/detector_gpu.py con .venv-gpu (Python 3.11 y CUDA 12.8), con el
  mismo modelo, y le manda cada imagen por 127.0.0.1 (unos 0,1 s por imagen).

El mismo .venv-gpu sirve en el portátil (RTX 5070) y en los ordenadores del laboratorio
(RTX 3060); al arrancar se indica qué GPU se usa y queda en resumen.json.

Si la GPU no está disponible o el detector deja de responder, se usa el modelo en CPU como
en demo.py, sin parar la demo. demo.py no cambia: si este script da problemas, basta con
volver a lanzar demo.py.

    python demo_gpu.py                      # demo completa, con GPU si la hay
    python demo_gpu.py --simulacion         # sin robot, con las imágenes de test
    python demo_gpu.py --solo-cpu           # igual que demo.py (para comparar)
    python demo_gpu.py --sin-mover --sin-disparar --paradas P1

Admite todas las opciones de demo.py. El registro de cada imagen (registro.csv) guarda en
ms_inferencia el tiempo total, ida y vuelta incluida, y resumen.json dice qué se ha usado.
"""

import argparse
import atexit
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)

PYTHON_GPU = os.path.join(AQUI, '.venv-gpu', 'Scripts' if os.name == 'nt' else 'bin',
                          'python.exe' if os.name == 'nt' else 'python')
SERVIDOR_GPU = os.path.join(AQUI, 'mando', 'detector_gpu.py')
# Puerto distinto del 8766 del mando, para no usar por error un detector con otro modelo
PUERTO = 8767
ESPERA_ARRANQUE = 60     # s para cargar el modelo en la GPU
ESPERA_RESPUESTA = 3     # s por imagen; en la GPU tarda unos 0,1 s
FALLOS_SEGUIDOS = 3      # tras estos fallos seguidos, el resto de la demo va en CPU
CALIDAD_JPEG = 95        # el vídeo del robot ya llega comprimido; con 95 la diferencia es mínima


def opciones_propias(argv):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--solo-cpu', action='store_true', help='no usar la GPU (igual que demo.py)')
    p.add_argument('--puerto-gpu', type=int, default=PUERTO, help='puerto local del detector GPU')
    p.add_argument('--simulacion', nargs='?', const=os.path.join(AQUI, '..', '..', 'ENTREGA 1', 'WEEK2',
                   'DATOS_ASIGNATURA', 'data_test'), default=None)
    propias, resto = p.parse_known_args(argv)
    # --simulacion también es de demo.py: se le vuelve a pasar
    if propias.simulacion is not None:
        resto = resto + ['--simulacion', propias.simulacion]
    return propias, resto


def cerrar_arbol(proceso):
    """Termina un proceso y sus hijos.

    En Windows, .venv-gpu/Scripts/python.exe es un lanzador que arranca el Python real como
    proceso hijo: terminar solo el lanzador dejaba el detector vivo ocupando el puerto.
    """
    if proceso is None or proceso.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proceso.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        proceso.terminate()
    try:
        proceso.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proceso.kill()


def info_detector(puerto):
    """Lo que dice de sí mismo el detector que escucha en `puerto` (/info), o None."""
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{puerto}/info', timeout=2) as r:
            return json.load(r)
    except Exception:  # noqa: BLE001: otro programa, o un detector antiguo sin /info
        return None


def mismo_modelo(info, arquitectura, ruta):
    """True si el detector abierto carga el mismo checkpoint y la misma arquitectura."""
    if not info or info.get('arquitectura') != arquitectura:
        return False
    def normal(r):
        return os.path.normcase(os.path.abspath(os.path.join(AQUI, r)))
    return normal(info.get('modelo', '')) == normal(ruta)


def escuchando(puerto):
    try:
        with socket.create_connection(('127.0.0.1', puerto), timeout=0.2):
            return True
    except OSError:
        return False


class DetectorGPU:
    """Proceso mando/detector_gpu.py: lo arranca, le manda imágenes y lo cierra al salir."""

    def __init__(self, arquitectura, ruta, puerto):
        self.puerto, self.proceso, self.log = puerto, None, None
        self.url = f'http://127.0.0.1:{puerto}/detectar'
        self.listo = False
        self.motivo = ''
        self.nombre = ''
        if arquitectura not in ('faster_rcnn_v2', 'faster_rcnn_v3'):
            self.motivo = f'detector_gpu.py no carga la arquitectura {arquitectura}'
        elif not os.path.isfile(PYTHON_GPU):
            self.motivo = f'no existe {PYTHON_GPU} (ver mando/README.md)'
        elif escuchando(puerto):
            # Un detector de una demo anterior que se quedó abierto: si es el mismo modelo, se usa
            info = info_detector(puerto)
            if mismo_modelo(info, arquitectura, ruta):
                self.listo = True
                self.nombre = info.get('gpu') or ''
                print(f'Detector GPU ya abierto en el puerto {puerto} (proceso {info.get("pid")}): se reutiliza',
                      flush=True)
            elif info:
                self.motivo = (f'el puerto {puerto} lo usa un detector con otro modelo '
                               f'({info.get("arquitectura")}, {info.get("modelo")}); usa --puerto-gpu')
            else:
                self.motivo = f'el puerto {puerto} ya está ocupado; cierra ese proceso o usa --puerto-gpu'
        else:
            self._arrancar(arquitectura, ruta)
        self.arrancada = self.listo

    def _arrancar(self, arquitectura, ruta):
        carpeta = os.path.join(AQUI, 'evidencias', 'detector')
        os.makedirs(carpeta, exist_ok=True)
        self.log = os.path.join(carpeta, time.strftime('gpu_demo_%Y%m%d_%H%M%S.log'))
        print(f'Cargando el detector en la GPU (registro en {self.log})...', flush=True)
        with open(self.log, 'wb') as log:
            self.proceso = subprocess.Popen(
                [PYTHON_GPU, SERVIDOR_GPU, '--modelo', ruta, '--arquitectura', arquitectura,
                 '--puerto', str(self.puerto)],
                cwd=AQUI, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        atexit.register(self.cerrar)
        fin = time.monotonic() + ESPERA_ARRANQUE
        while time.monotonic() < fin:
            if self.proceso.poll() is not None:
                self.motivo = f'el detector GPU terminó al arrancar (código {self.proceso.returncode}); ver {self.log}'
                return
            if escuchando(self.puerto):
                self.listo = True
                self.nombre = self._nombre_gpu()
                return
            time.sleep(0.2)
        self.motivo = f'el detector GPU no respondió en {ESPERA_ARRANQUE} s; ver {self.log}'
        self.cerrar()

    def _nombre_gpu(self):
        """Nombre de la GPU que el detector escribe en su registro al arrancar."""
        try:
            with open(self.log, encoding='utf-8', errors='replace') as f:
                for linea in f:
                    if linea.startswith('GPU:'):
                        return linea[4:].strip()
        except OSError:
            pass
        return ''

    def detectar(self, image):
        """Imagen RGB → (prediction, ms) con las mismas claves que demo_utils.detectar."""
        import cv2
        import numpy as np
        inicio = time.perf_counter()
        ok, jpeg = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                                [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG])
        if not ok:
            raise ValueError('no se pudo codificar la imagen')
        peticion = urllib.request.Request(self.url, data=jpeg.tobytes(), method='POST',
                                          headers={'Content-Type': 'image/jpeg'})
        with urllib.request.urlopen(peticion, timeout=ESPERA_RESPUESTA) as respuesta:
            r = json.load(respuesta)
        if (r['width'], r['height']) != (image.shape[1], image.shape[0]) or len(r['boxes']) != len(r['scores']):
            raise ValueError('respuesta del detector GPU inconsistente')
        cajas = np.asarray(r['boxes'], dtype=np.float32).reshape(-1, 4)
        puntos = np.asarray(r['scores'], dtype=np.float32)
        prediction = dict(boxes=cajas, scores=puntos, labels=np.ones(len(puntos), dtype=np.int64))
        return prediction, (time.perf_counter() - inicio) * 1000

    def cerrar(self):
        cerrar_arbol(self.proceso)
        self.listo = False


class Detectar:
    """Sustituye a detectar() en demo.py: GPU si responde y, si no, el modelo en CPU."""

    def __init__(self, gpu, detectar_cpu):
        self.gpu, self.cpu = gpu, detectar_cpu
        self.fallos = 0
        self.cuenta = dict(gpu=0, cpu=0, fallos_gpu=0)
        self.cerrojo = threading.Lock()

    def __call__(self, model, image, resize_shape=None):
        if self.gpu is not None and self.gpu.listo:
            try:
                resultado = self.gpu.detectar(image)
                with self.cerrojo:
                    self.fallos = 0
                    self.cuenta['gpu'] += 1
                return resultado
            except Exception as e:  # noqa: BLE001: cualquier fallo de la GPU pasa a la CPU
                with self.cerrojo:
                    self.fallos += 1
                    self.cuenta['fallos_gpu'] += 1
                    print(f'[aviso] detector GPU: {e}. Esta imagen se analiza en CPU', flush=True)
                    if self.fallos >= FALLOS_SEGUIDOS and self.gpu.listo:
                        print(f'[aviso] {FALLOS_SEGUIDOS} fallos seguidos: el resto de la demo va en CPU', flush=True)
                        self.gpu.listo = False
        with self.cerrojo:
            self.cuenta['cpu'] += 1
        return self.cpu(model, image, resize_shape)


def main(argv=None):
    propias, resto = opciones_propias(sys.argv[1:] if argv is None else argv)
    # Como en demo.py: el robot simulado se instala antes de importar el SDK
    if propias.simulacion is not None:
        import simulacion
        simulacion.instalar(propias.simulacion)
    import demo
    import circuito as C

    args = demo.argumentos(resto)
    arquitectura = args.arquitectura or C.MODELO
    ruta = args.modelo or C.RUTA_MODELO
    gpu = None
    if propias.solo_cpu:
        print('Detector en CPU (--solo-cpu)')
    else:
        gpu = DetectorGPU(arquitectura, ruta, propias.puerto_gpu)
        if gpu.listo:
            print(f'Detector en la GPU {gpu.nombre or "(sin nombre)"}: {arquitectura}, {ruta}. '
                  'La CPU queda de respaldo.')
        else:
            print(f'[aviso] Sin GPU ({gpu.motivo}). La demo va en CPU, como demo.py.')
    sustituto = Detectar(gpu, demo.detectar)
    demo.detectar = sustituto
    try:
        resultado = demo.main(resto)
    finally:
        if gpu is not None:
            gpu.cerrar()
        print('Imágenes analizadas: {gpu} en GPU, {cpu} en CPU ({fallos_gpu} fallos de la GPU)'.format(**sustituto.cuenta))
    if resultado is not None and getattr(resultado, 'registro', None) is not None:
        anotar_resumen(resultado.registro.carpeta, sustituto.cuenta, gpu)
    return resultado


def anotar_resumen(carpeta, cuenta, gpu):
    """Añade a resumen.json qué detector se ha usado."""
    ruta = os.path.join(carpeta, 'resumen.json')
    try:
        with open(ruta, encoding='utf-8') as f:
            resumen = json.load(f)
        resumen['detector'] = dict(cuenta, gpu_arrancada=bool(gpu and gpu.arrancada),
                                   nombre_gpu=(gpu.nombre if gpu else ''),
                                   motivo_sin_gpu=(gpu.motivo if gpu else 'opción --solo-cpu'))
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
    except (OSError, ValueError):
        pass


if __name__ == '__main__':
    main()
