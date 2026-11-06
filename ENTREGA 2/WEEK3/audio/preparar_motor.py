"""Ajusta un sonido de motor a la duración de la primera recta del circuito.

El sonido de F1 que usamos (10 s) tiene tres partes: el coche se acerca (0-2,4 s,
sube el volumen y el tono), pasa por delante (2,5-3,5 s, el tono cae) y se aleja con
el tono constante hasta apagarse (3,5-10 s). Para que dure lo mismo que la recta se
conservan el principio hasta `--corte` (llegada y paso) y el final (se aleja y se
apaga), unidos con un fundido cruzado en la parte de tono constante. Así el coche
pasa a mitad de la recta y el sonido se apaga cuando el robot se para. Después se
sube el volumen (como en preparar_disparo.py) y se guarda en WAV mono de 48 kHz.

    python audio/preparar_motor.py audio/propios/f1.mp3 audio/propios/f1_recta.wav

Por defecto, la duración es la del primer movimiento de circuito.PARADAS con el
perfil de demo_utils.avanzar (a VELOCIDAD_XY, frenando al final), más `--arranque`.
"""

import argparse
import math
import os
import sys

import numpy as np

AUDIO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AUDIO)
sys.path.insert(1, os.path.dirname(AUDIO))
from preparar_disparo import FRECUENCIA, guardar, leer, recortar_silencio, rms_db, subir_volumen  # noqa: E402


def duracion_avance(distancia, velocidad, minima=0.08, frenada=3.0, parada=0.01):
    """Segundos que tarda demo_utils.avanzar en recorrer `distancia` m sin contar el arranque.

    avanzar manda v = min(velocidad, max(minima, frenada * lo_que_falta)) y para a `parada` m.
    """
    d_frenada, d_minima = velocidad / frenada, minima / frenada
    if distancia <= d_frenada:
        return distancia / velocidad
    return ((distancia - d_frenada) / velocidad + math.log(d_frenada / d_minima) / frenada
            + max(0.0, d_minima - parada) / minima)


def duracion_primera_recta():
    import circuito as C
    from recorrido import movimiento
    x, y, _, opciones = movimiento(C.PARADAS[0]['movimientos'][0])
    v = opciones.get('velocidad') or C.VELOCIDAD_XY
    return duracion_avance((x * x + y * y) ** 0.5, v), (x * x + y * y) ** 0.5, v


def ajustar(x, duracion, corte, fundido):
    """Principio hasta `corte` + final, con un fundido cruzado de `fundido` s, hasta `duracion` s."""
    n, nc, nf = int(duracion * FRECUENCIA), int(corte * FRECUENCIA), int(fundido * FRECUENCIA)
    if len(x) <= n:
        return x
    if n <= nc + nf:
        # Más corta que la llegada y el paso: se toma el principio y se apaga
        y = x[:n].copy()
        y[-nf:] *= np.linspace(1, 0, nf)
        return y
    cola = x[len(x) - (n - nc):]                  # el final, empezando nf muestras antes del empalme
    a = np.sqrt(np.linspace(1, 0, nf))            # fundido de igual potencia
    b = np.sqrt(np.linspace(0, 1, nf))
    empalme = x[nc:nc + nf] * a + cola[:nf] * b
    return np.concatenate([x[:nc], empalme, cola[nf:]])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Sonido de motor con la duración de la primera recta')
    p.add_argument('entrada')
    p.add_argument('salida')
    p.add_argument('--duracion', type=float, default=None, help='s; por defecto, los de la primera recta')
    p.add_argument('--arranque', type=float, default=0.2, help='s que tarda el chasis en coger velocidad')
    p.add_argument('--corte', type=float, default=4.0, help='s del principio que se conservan (llegada y paso)')
    p.add_argument('--fundido', type=float, default=0.4, help='s del fundido cruzado')
    p.add_argument('--ganancia', type=float, default=6.0, help='dB extra con saturación suave')
    a = p.parse_args()
    if a.duracion is None:
        t, d, v = duracion_primera_recta()
        a.duracion = t + a.arranque
        print(f'Primera recta: {d:.2f} m a {v:.2f} m/s, {t:.2f} s + {a.arranque:.2f} s de arranque')
    x = recortar_silencio(leer(a.entrada))
    y = subir_volumen(ajustar(x, a.duracion, a.corte, a.fundido), a.ganancia)
    guardar(a.salida, y)
    print(f'Creado {a.salida}: {len(y) / FRECUENCIA:.2f} s (original {len(x) / FRECUENCIA:.2f} s), '
          f'RMS {rms_db(y):.1f} dBFS')
