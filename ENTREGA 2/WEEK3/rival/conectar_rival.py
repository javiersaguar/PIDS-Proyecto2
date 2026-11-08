"""Conecta el robot rival a la wifi del laboratorio (modo networking) con un código QR.

Hace lo mismo que connect.py, pero con los datos de rival/config_rival.json y sin tocar
serial_number.txt, que es el de nuestro robot. Solo hace falta una vez por sesión.

    python rival/conectar_rival.py

Antes: pestaña de conexión del robot rival en el icono del router y botón rojo pulsado.
Después, se apunta la cámara del robot al QR que se abre (rival/qrcode.png).
"""

import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(AQUI, 'config_rival.json')


def main():
    if not os.path.isfile(CONFIG):
        raise SystemExit(f'Falta {CONFIG}: copie config_rival.ejemplo.json con ese nombre y rellénelo')
    with open(CONFIG, encoding='utf-8') as f:
        config = json.load(f)
    if any(not config.get(k) or str(config[k]).startswith('<') for k in ('ssid', 'password')):
        raise SystemExit('Falta la wifi del laboratorio (ssid y password) en config_rival.json')

    from robomaster import conn
    from MyQR import myqr
    from PIL import Image

    helper = conn.ConnectionHelper()
    info = helper.build_qrcode_string(ssid=config['ssid'], password=config['password'])
    myqr.run(words=info, save_name='qrcode.png', save_dir=AQUI)   # qrcode.png no se sube: lleva la contraseña
    Image.open(os.path.join(AQUI, 'qrcode.png')).show()
    print('Apunte la cámara del robot rival al QR. Esperando la conexión...')
    time.sleep(5)
    if helper.wait_for_connection():
        print('Conectado. Ya se puede lanzar rival/rival_movil.py')
        return 0
    print('No se ha conectado: revise la wifi en config_rival.json y vuelva a intentarlo')
    return 1


if __name__ == '__main__':
    sys.exit(main())
