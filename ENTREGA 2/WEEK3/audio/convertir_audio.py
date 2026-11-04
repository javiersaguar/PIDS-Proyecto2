"""Convierte un audio (mp3, m4a, wav...) al formato que reproduce el robot.

El SDK solo reproduce WAV mono de 16 bits a 48 kHz (robot.play_audio). Uso:

    python audio/convertir_audio.py ENTRADA SALIDA.wav [--inicio 45] [--duracion 25] [--volumen 1.0]

Recorta desde `--inicio` (segundos) durante `--duracion` segundos, con un
fundido de salida de 1 s, y normaliza el volumen. Necesita ffmpeg; se usa el de
`imageio-ffmpeg` (pip install imageio-ffmpeg) o, si no está, el del sistema.

Los audios propios con derechos de autor (canciones, sonidos de juegos) van en
audio/propios/, que no se sube a GitHub.
"""

import argparse
import shutil
import subprocess
import sys


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ruta = shutil.which('ffmpeg')
        if ruta is None:
            sys.exit('Hace falta ffmpeg: pip install imageio-ffmpeg')
        return ruta


def convertir(entrada, salida, inicio=0.0, duracion=None, volumen=1.0):
    filtros = ['loudnorm=I=-14:TP=-1', f'volume={volumen}']
    if duracion:
        filtros.append(f'afade=t=out:st={max(duracion - 1, 0)}:d=1')
    orden = [ffmpeg(), '-y', '-hide_banner', '-loglevel', 'error', '-ss', str(inicio), '-i', entrada]
    if duracion:
        orden += ['-t', str(duracion)]
    orden += ['-af', ','.join(filtros), '-ac', '1', '-ar', '48000', '-sample_fmt', 's16', salida]
    subprocess.run(orden, check=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Convierte un audio al formato del robot (WAV mono 48 kHz)')
    p.add_argument('entrada')
    p.add_argument('salida')
    p.add_argument('--inicio', type=float, default=0.0, help='segundo desde el que se recorta')
    p.add_argument('--duracion', type=float, default=None, help='segundos que se conservan')
    p.add_argument('--volumen', type=float, default=1.0, help='multiplicador de volumen tras normalizar')
    a = p.parse_args()
    convertir(a.entrada, a.salida, a.inicio, a.duracion, a.volumen)
    print(f'Creado {a.salida} (WAV mono, 16 bits, 48 kHz)')
