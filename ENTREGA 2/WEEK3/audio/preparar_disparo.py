"""Prepara el sonido de disparo para el altavoz del robot: más fuerte y en ráfaga.

El SDK no permite subir el volumen del altavoz, así que se sube en el propio audio.
A partir de un disparo (cualquier formato que lea ffmpeg) crea dos WAV mono de 48 kHz:

- SALIDA_fuerte.wav: un disparo con volumen alto y un silencio corto delante. El
  altavoz del robot tarda un poco en arrancar y se come el principio de los audios;
  un disparo de 0,2 s cabe entero en ese hueco y no se oye.
- SALIDA_rafaga.wav: el mismo silencio y `--disparos` disparos cada `--cada` s. La
  demo lo reproduce una sola vez y dispara a ese mismo ritmo, en lugar de subir y
  reproducir un audio en cada disparo.

    python audio/preparar_disparo.py audio/propios/scar.wav audio/propios/scar

crea audio/propios/scar_fuerte.wav y audio/propios/scar_rafaga.wav. Los valores por
defecto coinciden con circuito.py (DISPAROS_POR_ROBOT, INTERVALO_DISPARO y
SILENCIO_AUDIO_DISPARO); si se cambian allí, hay que cambiarlos también aquí.
"""

import argparse
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convertir_audio import ffmpeg  # noqa: E402

FRECUENCIA = 48000


def leer(entrada):
    """Audio de `entrada` como muestras float mono a 48 kHz (decodificado con ffmpeg)."""
    orden = [ffmpeg(), '-hide_banner', '-loglevel', 'error', '-i', entrada, '-ac', '1', '-ar', str(FRECUENCIA),
             '-f', 's16le', '-']
    datos = subprocess.run(orden, check=True, stdout=subprocess.PIPE).stdout
    return np.frombuffer(datos, dtype=np.int16).astype(np.float64) / 32768


def recortar_silencio(x, umbral_db=-45):
    """Quita el silencio del principio y del final."""
    umbral = 10 ** (umbral_db / 20)
    fuertes = np.flatnonzero(np.abs(x) > umbral)
    return x[fuertes[0]:fuertes[-1] + 1] if fuertes.size else x


def subir_volumen(x, ganancia_db=8.0, pico_db=-0.5):
    """Normaliza al pico y añade `ganancia_db` con saturación suave (tanh), sin recortar."""
    x = x / max(np.abs(x).max(), 1e-9)
    g = 10 ** (ganancia_db / 20)
    y = np.tanh(g * x) / np.tanh(g)
    return y * 10 ** (pico_db / 20)


def guardar(ruta, x):
    os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FRECUENCIA)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def preparar(entrada, salida, disparos=12, cada=0.3, silencio=0.3, ganancia_db=8.0):
    disparo = subir_volumen(recortar_silencio(leer(entrada)), ganancia_db)
    hueco = np.zeros(int(silencio * FRECUENCIA))
    fuerte = np.concatenate([hueco, disparo])

    paso = int(round(cada * FRECUENCIA))
    rafaga = np.zeros(len(hueco) + paso * (disparos - 1) + len(disparo))
    for i in range(disparos):
        inicio = len(hueco) + i * paso
        rafaga[inicio:inicio + len(disparo)] += disparo   # si el disparo dura más que `cada`, se solapan
    rafaga *= min(1.0, 10 ** (-0.5 / 20) / max(np.abs(rafaga).max(), 1e-9))

    for nombre, x in (('fuerte', fuerte), ('rafaga', rafaga)):
        ruta = f'{salida}_{nombre}.wav'
        guardar(ruta, x)
        print(f'Creado {ruta}: {len(x) / FRECUENCIA:.2f} s, RMS {rms_db(x):.1f} dBFS')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Disparo fuerte y ráfaga para el altavoz del robot')
    p.add_argument('entrada', help='audio de un disparo')
    p.add_argument('salida', help='prefijo de salida, p. ej. audio/propios/scar')
    p.add_argument('--disparos', type=int, default=12, help='disparos de la ráfaga (DISPAROS_POR_ROBOT)')
    p.add_argument('--cada', type=float, default=0.3, help='s entre disparos (INTERVALO_DISPARO)')
    p.add_argument('--silencio', type=float, default=0.3, help='s de silencio inicial (SILENCIO_AUDIO_DISPARO)')
    p.add_argument('--ganancia', type=float, default=8.0, help='dB extra con saturación suave; más, más fuerte')
    a = p.parse_args()
    preparar(a.entrada, a.salida, a.disparos, a.cada, a.silencio, a.ganancia)
