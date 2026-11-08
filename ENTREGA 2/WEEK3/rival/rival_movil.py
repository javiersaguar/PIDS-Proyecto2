"""Mueve el robot rival 2 despacio y en línea recta, en paralelo a nuestro robot en la rotonda.

Lo lanza Alejandro en su portátil, conectado al robot RIVAL (no al nuestro). El robot
espera quieto hasta recibir el aviso de la demo (UDP por la red del laboratorio) o hasta
que se pulse Enter; entonces avanza `--distancia` m a `--velocidad` m/s y se para.

    python rival/rival_movil.py                       # espera el aviso o Enter y avanza 0,75 m a 0,05 m/s
    python rival/rival_movil.py --modo enter          # solo con Enter
    python rival/rival_movil.py --sin-robot           # prueba de red: espera el aviso sin conectar el robot
    python rival/rival_movil.py --enviar 192.168.1.23 # (en NUESTRO portátil) envía un aviso de prueba

La conexión sale de rival/config_rival.json (copia de config_rival.ejemplo.json, que no
se sube a GitHub). Instrucciones completas en rival/README.md.

Seguridad: nunca pasa de 0,1 m/s, el robot se para solo si el script deja de mandar
órdenes (0,5 s) y Ctrl+C lo para en cualquier momento.
"""

import argparse
import json
import os
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import aviso  # noqa: E402

VELOCIDAD_MAX = 0.1          # m/s: el rival siempre va muy despacio
CONFIG = os.path.join(AQUI, 'config_rival.json')


def argumentos(argv=None):
    p = argparse.ArgumentParser(description='Robot rival en movimiento para la demo del grupo 2')
    p.add_argument('--distancia', type=float, default=0.75,
                   help='m que avanza (negativo: hacia atrás). Por defecto 0,75')
    p.add_argument('--velocidad', type=float, default=0.05,
                   help=f'm/s (como mucho {VELOCIDAD_MAX}). Por defecto 0,05')
    p.add_argument('--retraso', type=float, default=0.0, help='s que espera tras el aviso antes de arrancar')
    p.add_argument('--modo', choices=['aviso', 'enter', 'ya'], default='aviso',
                   help='aviso: arranca con el aviso de la demo o con Enter; enter: solo con Enter; '
                        'ya: cuenta atrás de 3 s y arranca')
    p.add_argument('--rival', default='rival 2', help='nombre del rival en el aviso (como en circuito.py)')
    p.add_argument('--puerto', type=int, default=None, help=f'puerto UDP del aviso (por defecto {aviso.PUERTO})')
    p.add_argument('--conexion', choices=['networking', 'wifi'], default=None,
                   help='por defecto, la de config_rival.json')
    p.add_argument('--sin-robot', action='store_true', help='no conectar el robot: solo probar el aviso')
    p.add_argument('--enviar', metavar='IP[:PUERTO]', default=None,
                   help='enviar un aviso de prueba a ese portátil y salir (no usa el robot)')
    return p.parse_args(argv)


def leer_config():
    if not os.path.isfile(CONFIG):
        return {}
    with open(CONFIG, encoding='utf-8') as f:
        return json.load(f)


def conectar(config, conexion):
    """Robot rival conectado. En networking se busca por su número de serie, nunca por serial_number.txt."""
    from robomaster import robot
    ep_robot = robot.Robot()
    if conexion == 'networking':
        serie = (config.get('serial') or '').strip()
        if not serie or serie.startswith('<'):
            raise SystemExit(f'Falta el número de serie del robot rival en {CONFIG}. Sin él el script podría '
                             'conectarse a otro robot de la red (por ejemplo, el nuestro).')
        print(f'Conectando por networking al robot que acaba en ...{serie[-4:]}')
        ep_robot.initialize(conn_type='sta', sn=serie)
    else:
        print('Conectando por wifi directo (el portátil tiene que estar en la wifi RMEP-... del robot rival)')
        ep_robot.initialize(conn_type='ap')
    return ep_robot


def esperar_salida(args, puerto):
    """Bloquea hasta el aviso de la demo o Enter (según --modo)."""
    if args.modo == 'ya':
        for i in (3, 2, 1):
            print(f'  {i}...')
            time.sleep(1)
        return 'cuenta atrás'
    pulsado = threading.Event()

    def leer_enter():
        try:
            input()
        except EOFError:
            return
        pulsado.set()

    threading.Thread(target=leer_enter, daemon=True).start()
    if args.modo == 'enter':
        print('Listo. Pulse Enter cuando nuestro robot empiece a retroceder en la rotonda.')
        while not pulsado.wait(0.2):
            pass
        return 'Enter'
    s = aviso.escuchar(puerto)
    try:
        print(f'Listo. Esperando el aviso de la demo en el puerto UDP {puerto} '
              '(o pulse Enter para arrancar a mano)...')
        while True:
            if pulsado.is_set():
                return 'Enter'
            ok, origen = aviso.recibir(s, args.rival)
            if ok:
                return f'aviso de {origen}'
    finally:
        s.close()


def avanzar(ep_robot, distancia, velocidad):
    """Avanza `distancia` m en línea recta a `velocidad` m/s con drive_speed, midiendo con la odometría.

    drive_speed va en m/s reales (chassis.move no baja de 0,5). Cada orden lleva un tiempo
    máximo de 0,5 s: si el script se cuelga, el robot se para solo. Sin odometría, avanza
    durante distancia / velocidad segundos.
    """
    chassis = ep_robot.chassis
    posicion = {}

    def al_medir(info):
        posicion['x'] = float(info[0])

    signo = 1 if distancia >= 0 else -1
    objetivo = abs(distancia)
    con_odometria = True
    try:
        chassis.sub_position(cs=0, freq=20, callback=al_medir)
    except Exception as e:
        print(f'[aviso] sin odometría ({e!r}): se avanza por tiempo')
        con_odometria = False
    fin = time.monotonic() + 2.0
    while con_odometria and 'x' not in posicion and time.monotonic() < fin:
        time.sleep(0.05)
    con_odometria = con_odometria and 'x' in posicion
    x0 = posicion.get('x', 0.0)
    inicio = time.monotonic()
    limite = inicio + 2 * objetivo / velocidad + 5
    try:
        while True:
            ahora = time.monotonic()
            hecho = abs(posicion['x'] - x0) if con_odometria else velocidad * (ahora - inicio)
            falta = objetivo - hecho
            if falta <= 0.01:
                break
            if ahora > limite:
                print(f'[aviso] no ha llegado a tiempo: lleva {hecho:.2f} de {objetivo:.2f} m; se para')
                break
            chassis.drive_speed(x=signo * velocidad, y=0, z=0, timeout=0.5)
            time.sleep(0.05)
    finally:
        chassis.drive_speed(x=0, y=0, z=0)
        time.sleep(0.3)
        if con_odometria:
            try:
                chassis.unsub_position()
            except Exception:
                pass
    hecho = abs(posicion['x'] - x0) if con_odometria else velocidad * (time.monotonic() - inicio)
    return hecho, time.monotonic() - inicio


def main(argv=None):
    args = argumentos(argv)
    config = leer_config()
    puerto = args.puerto or int(config.get('puerto', aviso.PUERTO))
    if args.enviar:
        destino = args.enviar if ':' in args.enviar else f'{args.enviar}:{puerto}'
        aviso.enviar(destino, args.rival)
        print(f'Aviso de prueba de «{args.rival}» enviado a {destino}')
        return 0
    velocidad = min(abs(args.velocidad), VELOCIDAD_MAX)
    if velocidad != abs(args.velocidad):
        print(f'[aviso] velocidad limitada a {VELOCIDAD_MAX} m/s')
    if velocidad <= 0:
        raise SystemExit('La velocidad tiene que ser mayor que 0')
    print(f'Movimiento: {args.distancia:+.2f} m a {velocidad:.2f} m/s '
          f'(unos {abs(args.distancia) / velocidad:.0f} s)')

    if args.sin_robot:
        motivo = esperar_salida(args, puerto)
        print(f'Salida por {motivo}. Prueba sin robot: no se mueve nada.')
        return 0

    conexion = args.conexion or config.get('conexion', 'networking')
    ep_robot = conectar(config, conexion)
    try:
        bateria = {}
        try:
            ep_robot.battery.sub_battery_info(freq=1, callback=lambda p: bateria.setdefault('p', p))
            time.sleep(1.2)
            ep_robot.battery.unsub_battery_info()
        except Exception:
            pass
        if 'p' in bateria:
            print(f'Batería del rival: {bateria["p"]}%')
            if bateria['p'] < 15:
                print('[aviso] batería baja: puede no completar el movimiento')
        motivo = esperar_salida(args, puerto)
        if args.retraso > 0:
            print(f'Salida por {motivo}: arranca en {args.retraso:.1f} s')
            time.sleep(args.retraso)
        print(f'Salida por {motivo}: avanzando...')
        hecho, tiempo = avanzar(ep_robot, args.distancia, velocidad)
        print(f'Hecho: {hecho:.2f} m en {tiempo:.1f} s')
    except KeyboardInterrupt:
        print('Detenido con Ctrl+C')
    finally:
        try:
            ep_robot.chassis.drive_speed(x=0, y=0, z=0)
        except Exception:
            pass
        ep_robot.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
