"""Prepara un aviso de voz (p. ej. «enemy spotted») para el altavoz del robot.

Quita el silencio del principio y del final, sube el volumen con saturación suave
(como preparar_disparo.py, pero con menos ganancia para que la voz se entienda) y
deja un silencio corto delante, porque el altavoz se come el principio de los audios.
Guarda un WAV mono de 48 kHz.

    python audio/preparar_voz.py audio/propios/enemy_spotted.mp3 audio/propios/enemy_spotted.wav
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preparar_disparo import FRECUENCIA, guardar, leer, recortar_silencio, rms_db, subir_volumen  # noqa: E402

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Aviso de voz para el altavoz del robot')
    p.add_argument('entrada')
    p.add_argument('salida')
    p.add_argument('--silencio', type=float, default=0.3, help='s de silencio inicial')
    p.add_argument('--ganancia', type=float, default=5.0, help='dB extra con saturación suave')
    a = p.parse_args()
    voz = subir_volumen(recortar_silencio(leer(a.entrada)), a.ganancia)
    y = np.concatenate([np.zeros(int(a.silencio * FRECUENCIA)), voz])
    guardar(a.salida, y)
    print(f'Creado {a.salida}: {len(y) / FRECUENCIA:.2f} s, RMS {rms_db(y):.1f} dBFS')
