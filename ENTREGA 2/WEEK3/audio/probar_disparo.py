"""Reproduce en el robot los audios de disparo, uno tras otro, para compararlos.

    python audio/probar_disparo.py                      (desde ENTREGA 2/WEEK3)
    python audio/probar_disparo.py OTRO.wav ...         (otros ficheros)

Por defecto: la SCAR original, la fuerte y la ráfaga de audio/propios/ (las crea
audio/preparar_disparo.py). Si la original no se oye y la fuerte sí, el altavoz se
comía el principio del audio o le faltaba volumen.
"""

import os
import sys
import time

WEEK3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WEEK3)
from demo_utils import connect  # noqa: E402

FICHEROS = ['audio/propios/scar.wav', 'audio/propios/scar_fuerte.wav', 'audio/propios/scar_rafaga.wav']

if __name__ == '__main__':
    ficheros = sys.argv[1:] or [os.path.join(WEEK3, f) for f in FICHEROS]
    ep_robot = connect('networking')
    try:
        for fichero in ficheros:
            if not os.path.isfile(fichero):
                print(f'No existe {fichero}')
                continue
            print(f'Suena {os.path.basename(fichero)}')
            accion = ep_robot.play_audio(fichero)
            if accion is not None:
                accion.wait_for_completed(timeout=15)
            time.sleep(1.5)
    finally:
        ep_robot.close()
