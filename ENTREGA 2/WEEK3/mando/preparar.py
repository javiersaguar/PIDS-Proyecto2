"""Comprobaciones locales antes de conectar al robot. No conecta ni mueve hardware."""
import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
WEEK3 = BASE.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(WEEK3))


def comprobar():
    from audio_robot import NOMBRES, CARPETA, comprobar_audio
    from conductor import configuracion, leer_config
    from coreografias import CATALOGO, validar
    resultados = []
    def revisar(nombre, operacion, obligatorio=True):
        try:
            detalle = operacion()
            resultados.append(dict(nombre=nombre, correcto=True, obligatorio=obligatorio,
                                   detalle=str(detalle)))
        except Exception as error:
            resultados.append(dict(nombre=nombre, correcto=False, obligatorio=obligatorio,
                                   detalle=str(error)))
    revisar('Python del servidor', lambda: version_servidor())
    revisar('SDK y servidor web', lambda: paquetes())
    revisar('Configuración', lambda: configuracion(leer_config()))
    for nombre in NOMBRES:
        revisar('WAV ' + nombre, lambda n=nombre: '%.3f s' % comprobar_audio(
            CARPETA/('mando_'+n+'_robot.wav')))
    for nombre in CATALOGO:
        revisar('Coreografía ' + nombre, lambda n=nombre: validar(n))
    revisar('Checkpoint CPU', pesos_cpu)
    revisar('GPU opcional', gpu, obligatorio=False)
    return resultados


def version_servidor():
    if sys.version_info[:2] != (3, 8):
        raise RuntimeError('Ejecuta con .venv/Scripts/python.exe (Python 3.8)')
    return sys.version.split()[0]


def paquetes():
    versiones = {p: importlib.metadata.version(p) for p in ('robomaster','aiohttp','torch','torchvision')}
    from robomaster import protocol
    proto = protocol.ProtoPlaySound()
    proto._play_ctrl = 0
    assert len(proto.pack_req()) == 10 and proto.pack_req()[6] == 0
    return versiones


def pesos_cpu():
    import torch
    ruta = WEEK3/'models/faster_rcnn_v3/mando_pesos.pt'
    contenido = torch.load(str(ruta), map_location='cpu', weights_only=True)
    if 'model' not in contenido or not contenido['model']:
        raise ValueError('Checkpoint sin pesos')
    return str(len(contenido['model'])) + ' tensores, lectura restringida'


def gpu():
    interprete = WEEK3/'.venv-gpu/Scripts/python.exe'
    r = subprocess.run([str(interprete), '-I', '-c',
                        'import torch; print(torch.__version__); assert torch.cuda.is_available()'],
                       capture_output=True, text=True, timeout=15)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or 'CUDA no disponible, se usará CPU')
    return r.stdout.strip()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    salida = comprobar()
    if a.json:
        print(json.dumps(salida,ensure_ascii=False,indent=2))
    else:
        for r in salida:
            etiqueta = 'OK' if r['correcto'] else ('ERROR' if r['obligatorio'] else 'AVISO')
            print('[%s] %s: %s' % (etiqueta, r['nombre'], r['detalle']))
    sys.exit(1 if any(r['obligatorio'] and not r['correcto'] for r in salida) else 0)
