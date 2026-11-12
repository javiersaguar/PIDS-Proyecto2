"""Aviso por la red local para que el robot rival empiece a moverse en el momento justo.

La demo (demo.py --aviso-rival IP) lo envía al empezar el ataque en marcha de la
rotonda; rival_movil.py lo espera en el portátil que maneja el robot rival. Es un
mensaje UDP con JSON. Solo usa la biblioteca estándar, para que el kit del rival no
necesite torch.
"""

import json
import socket
import time

PUERTO = 50555
TIPO = 'pids-grupo2-rival'


def destino(texto):
    """'IP' o 'IP:PUERTO' -> (ip, puerto)."""
    ip, _, puerto = texto.partition(':')
    return ip.strip(), int(puerto) if puerto else PUERTO


def enviar(texto_destino, rival, repeticiones=3):
    """Envía el aviso de salida del `rival` a 'IP[:PUERTO]'. Se repite por si se pierde un paquete.

    Una IP terminada en .255 (o 255.255.255.255) es de difusión: llega a todos los
    portátiles de la red, si la red lo permite.
    """
    ip, puerto = destino(texto_destino)
    mensaje = json.dumps({'tipo': TIPO, 'rival': rival, 'hora': time.time()}).encode('utf-8')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if ip.endswith('.255'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for i in range(repeticiones):
            s.sendto(mensaje, (ip, puerto))
            if i < repeticiones - 1:
                time.sleep(0.05)
    finally:
        s.close()


def escuchar(puerto=PUERTO):
    """Socket UDP abierto en `puerto` para recibir avisos (con timeout corto, para poder cortar con Ctrl+C)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', puerto))
    s.settimeout(0.2)
    return s


def recibir(s, rival):
    """Lee un paquete del socket: (True, ip de origen) si es el aviso de `rival`; (False, None) si no."""
    try:
        datos, origen = s.recvfrom(2048)
    except socket.timeout:
        return False, None
    try:
        mensaje = json.loads(datos.decode('utf-8'))
    except ValueError:
        return False, None
    if mensaje.get('tipo') == TIPO and mensaje.get('rival') == rival:
        return True, origen[0]
    return False, None
