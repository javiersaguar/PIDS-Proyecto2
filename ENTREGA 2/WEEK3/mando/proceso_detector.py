"""Arranque del detector local con propiedad y limpieza del proceso creado."""
import os
import socket
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
WEEK3 = BASE.parent


def disponible():
    try:
        with socket.create_connection(('127.0.0.1', 8766), timeout=.1):
            return True
    except OSError:
        return False


def cerrar(proceso):
    if proceso is not None and proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=5)


def iniciar():
    if disponible():
        return None
    interprete = WEEK3/'.venv-gpu/Scripts/python.exe'
    if not interprete.is_file():
        return None
    try:
        resultado = subprocess.run(
            [str(interprete), '-I', '-c', 'import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)'],
            capture_output=True, timeout=20)
        if resultado.returncode:
            return None
    except (OSError, subprocess.TimeoutExpired):
        return None
    carpeta = WEEK3/'evidencias'/'detector'
    carpeta.mkdir(parents=True, exist_ok=True)
    registro = carpeta/('gpu_%s_%s.log' % (time.strftime('%Y%m%d_%H%M%S'), time.time_ns()))
    print('Cargando detector GPU. Registro en ' + str(registro), flush=True)
    with registro.open('wb') as log:
        proceso = subprocess.Popen([str(interprete), str(BASE/'detector_gpu.py')],
                                   cwd=str(WEEK3), stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    fin=time.monotonic()+45
    try:
        while proceso.poll() is None and time.monotonic()<fin:
            if disponible():
                return proceso
            time.sleep(.1)
    except BaseException:
        cerrar(proceso)
        raise
    cerrar(proceso)
    print('GPU no disponible. Se usa CPU. Consulta ' + str(registro), flush=True)
    return None
