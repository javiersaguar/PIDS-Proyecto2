"""Prueba del recorrido movimiento a movimiento, sin modelo, sin barrido y sin disparar.

    python probar_recorrido.py              lista los movimientos de circuito.PLANO (no conecta)
    python probar_recorrido.py --paso 1     ejecuta solo el movimiento 1
    python probar_recorrido.py --paso 2-4   ejecuta del 2 al 4, seguidos

Los movimientos son relativos: el paso N empieza donde ha acabado el N-1, así que se
deja el robot donde quedó (o se coloca a mano en la salida de ese paso). Antes de
moverse pide Enter. Al acabar, compara lo pedido con la odometría del robot y deja
anotar la medida real con cinta métrica. Todo se guarda en evidencias/recorrido.csv.

Ctrl+C para el chasis y cierra la conexión.
"""

import argparse
import csv
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import circuito as C  # noqa: E402
from demo_utils import VEL_XY_MAX, VEL_Z_MAX, connect, limitar, mover_chasis, nivel_bateria  # noqa: E402

CSV = os.path.join(AQUI, 'evidencias', 'recorrido.csv')
CAMPOS = ['momento', 'paso', 'parada', 'x', 'y', 'z', 'odometria_x', 'odometria_y', 'segundos', 'medida_real',
          'nota']


def movimientos():
    """Lista numerada (desde 1) de (parada, x, y, z) de circuito.PARADAS."""
    return [(p['nombre'], x, y, z) for p in C.PARADAS for x, y, z in p['movimientos']]


def rango(texto, total):
    if '-' in texto:
        a, b = (int(v) for v in texto.split('-', 1))
    else:
        a = b = int(texto)
    if not 1 <= a <= b <= total:
        raise SystemExit(f'Pasos fuera de rango: hay {total} movimientos (1-{total})')
    return range(a, b + 1)


def ejecutar(ep_robot, n, parada, x, y, z, confirmar=True):
    v_xy, v_z = limitar(C.VELOCIDAD_XY, VEL_XY_MAX), limitar(C.VELOCIDAD_Z, VEL_Z_MAX)
    estimado = (x * x + y * y) ** 0.5 / v_xy + abs(z) / v_z
    print(f'Paso {n} ({parada}): x={x:+.2f} m  y={y:+.2f} m  z={z:+.0f} grados  '
          f'(unos {estimado:.1f} s a {v_xy:.2f} m/s y {v_z:.0f} grados/s)')
    if confirmar:
        input('  Enter para moverse (Ctrl+C para cancelar)... ')
    inicio, medido, error = time.time(), None, ''
    try:
        medido = mover_chasis(ep_robot, x, y, z, C.VELOCIDAD_XY, C.VELOCIDAD_Z, que=f'chasis (paso {n})',
                              odometria=getattr(C, 'AVANCE_CON_ODOMETRIA', True))
    except RuntimeError as e:
        error = str(e)
        print(f'  [error] {e}')
    segundos = time.time() - inicio
    if medido is not None:
        print(f'  Odometría: x={medido[0]:+.3f} m  y={medido[1]:+.3f} m en {segundos:.1f} s '
              f'({(medido[0] ** 2 + medido[1] ** 2) ** 0.5 / max(segundos, 0.1):.2f} m/s de media; '
              f'error x {medido[0] - x:+.3f} m, y {medido[1] - y:+.3f} m)')
    elif not error:
        print(f'  Hecho en {segundos:.1f} s')
    real = input('  Medida real con cinta (m o grados; Enter para omitir): ').strip() if confirmar else ''
    nota = input('  Nota (Enter para omitir): ').strip() if confirmar else ''
    return dict(momento=time.strftime('%Y-%m-%d %H:%M:%S'), paso=n, parada=parada, x=x, y=y, z=z,
                odometria_x='' if medido is None else round(medido[0], 3),
                odometria_y='' if medido is None else round(medido[1], 3),
                segundos=round(segundos, 1), medida_real=real.replace(',', '.'),
                nota='; '.join(t for t in (error, nota) if t))


def guardar(fila):
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    nuevo = not os.path.isfile(CSV)
    with open(CSV, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def main(argv=None):
    p = argparse.ArgumentParser(description='Prueba del recorrido movimiento a movimiento')
    p.add_argument('--paso', default=None, help='movimiento N, o rango N-M, a ejecutar')
    p.add_argument('--sin-confirmar', action='store_true', help='no pedir Enter ni la medida real')
    p.add_argument('--conexion', choices=['auto', 'wifi', 'networking'], default='auto')
    args = p.parse_args(argv)

    lista = movimientos()
    print('Movimientos de circuito.PLANO (relativos: x adelante, y derecha, z giro a la izquierda):')
    for n, (parada, x, y, z) in enumerate(lista, 1):
        print(f'  {n}. {parada}: x={x:+.2f} m  y={y:+.2f} m  z={z:+.0f} grados')
    if args.paso is None:
        print('\nPara ejecutar uno: python probar_recorrido.py --paso 1')
        return

    pasos = rango(args.paso, len(lista))
    ep_robot = connect('networking') if args.conexion == 'auto' else connect(args.conexion, auto=False)
    try:
        bateria = nivel_bateria(ep_robot)
        print(f'Batería: {bateria}%')
        if bateria is not None and bateria < C.BATERIA_CRITICA:
            raise SystemExit(f'Batería por debajo del {C.BATERIA_CRITICA}%: cárguela antes de probar')
        for n in pasos:
            parada, x, y, z = lista[n - 1]
            fila = ejecutar(ep_robot, n, parada, x, y, z, confirmar=not args.sin_confirmar)
            guardar(fila)
            if fila['nota'].startswith('chasis'):
                break   # error del chasis: no seguir con los siguientes pasos
        print(f'\nAnotado en {CSV}')
    except KeyboardInterrupt:
        print('\nCancelado: se para el chasis')
    finally:
        try:
            ep_robot.chassis.drive_speed(x=0, y=0, z=0)
        except Exception:
            pass
        ep_robot.close()


if __name__ == '__main__':
    main()
