"""Recorrido de la demo a partir de medidas tomadas sobre el plano del circuito.

En lugar de escribir a mano los movimientos relativos de cada parada, se dan los
puntos del plano en metros y aquí se calculan los giros y avances del chasis y los
ángulos del barrido de la torreta.

Coordenadas del plano (como el boceto, visto desde arriba):
- origen: punto de salida de nuestro robot (la esquina de arriba a la izquierda);
- x: metros hacia la derecha del boceto; y: metros hacia abajo del boceto;
- rumbos en grados: 0 hacia la derecha, 90 hacia abajo, 180 hacia la izquierda y
  -90 hacia arriba. Un rumbo mayor es girar en el sentido de las agujas del reloj,
  igual que un yaw mayor de la torreta.
"""

import math


def movimiento(m):
    """(x, y, z, opciones) de un movimiento de PARADAS: una tupla (x, y, z) o un dict.

    El dict admite x, y, z y opciones: velocidad (m/s de ese avance) y atacar (yaw de la
    torreta, en grados, hacia el que se busca un rival y se le dispara durante el avance).
    """
    if isinstance(m, dict):
        opciones = {k: v for k, v in m.items() if k not in ('x', 'y', 'z')}
        return float(m.get('x', 0)), float(m.get('y', 0)), float(m.get('z', 0)), opciones
    x, y, z = m
    return x, y, z, {}


def aplicar(punto, rumbo, x, y, z):
    """Punto del plano y rumbo tras un movimiento relativo del chasis (x adelante, y derecha, z izquierda)."""
    r = math.radians(rumbo)
    px = punto[0] + x * math.cos(r) + y * math.cos(r + math.pi / 2)
    py = punto[1] + x * math.sin(r) + y * math.sin(r + math.pi / 2)
    return (round(px, 3), round(py, 3)), rumbo - z


def rival_relativo(rival, punto, rumbo):
    """Un rival de circuito.RIVALES visto desde el chasis, en `punto` del plano y con `rumbo`.

    :return: dict con yaw (grados hacia los que queda, > 0 a la derecha), distancia (m) y
             velocidad (vx, vy) del rival en m/s y en ejes del chasis (x adelante, y derecha);
             (0, 0) si está quieto. Si tiene `hasta` y `velocidad`, se mueve de `punto` hacia `hasta`.
    """
    r = math.radians(rumbo)
    dx, dy = rival['punto'][0] - punto[0], rival['punto'][1] - punto[1]
    vx = vy = 0.0
    if rival.get('hasta') is not None and rival.get('velocidad'):
        hx, hy = rival['hasta'][0] - rival['punto'][0], rival['hasta'][1] - rival['punto'][1]
        largo = math.hypot(hx, hy)
        if largo > 0:
            v_x, v_y = rival['velocidad'] * hx / largo, rival['velocidad'] * hy / largo
            vx, vy = v_x * math.cos(r) + v_y * math.sin(r), -v_x * math.sin(r) + v_y * math.cos(r)
    adelante, derecha = dx * math.cos(r) + dy * math.sin(r), -dx * math.sin(r) + dy * math.cos(r)
    return dict(yaw=math.degrees(math.atan2(derecha, adelante)), distancia=math.hypot(dx, dy),
                velocidad=(vx, vy))


def normalizar(angulo):
    """Ángulo equivalente en (-180, 180]."""
    a = (angulo + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def rumbo_hacia(desde, hasta):
    """Rumbo en el plano (grados) para ir de `desde` a `hasta`."""
    return math.degrees(math.atan2(hasta[1] - desde[1], hasta[0] - desde[0]))


def tramo(desde, hasta, rumbo, girar=True):
    """Movimientos (x, y, z) del chasis para ir de `desde` a `hasta` con el chasis en `rumbo`.

    girar=True: gira hacia el destino y avanza recto. girar=False: se desplaza en
    diagonal sin girar (las ruedas mecanum lo permiten), lo que evita el error de
    los giros. Devuelve (movimientos, rumbo final del chasis).
    """
    dx, dy = hasta[0] - desde[0], hasta[1] - desde[1]
    distancia = math.hypot(dx, dy)
    if distancia < 0.01:
        return [], rumbo
    destino = rumbo_hacia(desde, hasta)
    if girar:
        movimientos = []
        giro = normalizar(destino - rumbo)
        if abs(giro) > 0.5:
            movimientos.append((0, 0, round(-giro, 1)))   # z > 0 gira a la izquierda
        movimientos.append((round(distancia, 3), 0, 0))
        return movimientos, destino
    relativo = math.radians(destino - rumbo)
    return [(round(distancia * math.cos(relativo), 3), round(distancia * math.sin(relativo), 3), 0)], rumbo


def girar_hacia(rumbo, nuevo):
    """Giro en el sitio hasta el rumbo `nuevo`: (movimientos, rumbo final)."""
    giro = normalizar(nuevo - rumbo)
    return ([(0, 0, round(-giro, 1))] if abs(giro) > 0.5 else []), nuevo


def barrido_hacia(punto, rumbo, rivales, abanico=30):
    """Yaws de la torreta para mirar a cada rival desde `punto`, con el chasis en `rumbo`.

    Por cada rival, su dirección y otra a cada lado (±abanico), por si se ha movido
    o el chasis no ha quedado exactamente donde se esperaba.
    """
    yaws = []
    for rival in rivales:
        centro = normalizar(rumbo_hacia(punto, rival) - rumbo)
        for yaw in (centro, centro - abanico, centro + abanico):
            yaw = round(max(-240.0, min(240.0, yaw)), 1)
            if all(abs(yaw - y) > 5 for y in yaws):
                yaws.append(yaw)
    return yaws


def paradas_desde_plano(rumbo_inicial, paradas, girar=True, abanico=30, barrido_sin_rivales=None):
    """Lista PARADAS de circuito.py a partir de las paradas medidas en el plano.

    Cada parada es un dict con:
    - nombre;
    - punto: (x, y) donde se para el robot; o en su lugar
    - movimientos: lista de movimientos relativos del chasis, tuplas (x, y, z) o dicts
      con velocidad y atacar (ver movimiento()), para tramos que se describen así;
    - por: puntos intermedios opcionales, para rodear obstáculos;
    - mirar: rumbo del chasis al llegar (opcional; si no, el del último tramo);
    - rivales: puntos opcionales donde se espera un rival; el barrido mira hacia ellos;
    - barrido, pitch, objetivos: opcionales. Sin barrido ni rivales se usa
      `barrido_sin_rivales`; barrido=[] no barre al llegar. objetivos es por defecto el
      número de rivales (None si no se conocen, y entonces se barre entero).
    """
    if barrido_sin_rivales is None:
        barrido_sin_rivales = [0, 60, 120, 180, -120, -60]
    actual, rumbo, salida = (0.0, 0.0), float(rumbo_inicial), []
    for p in paradas:
        movimientos = []
        for m in p.get('movimientos', []):
            x, y, z, _ = movimiento(m)
            actual, rumbo = aplicar(actual, rumbo, x, y, z)
            movimientos.append(m)
        puntos = list(p.get('por', [])) + ([p['punto']] if 'punto' in p else [])
        for punto in puntos:
            nuevos, rumbo = tramo(actual, punto, rumbo, girar)
            movimientos += nuevos
            actual = punto
        if p.get('mirar') is not None:
            nuevos, rumbo = girar_hacia(rumbo, p['mirar'])
            movimientos += nuevos
        rivales = p.get('rivales') or []
        if 'barrido' in p:
            barrido = list(p['barrido'])
        else:
            barrido = barrido_hacia(actual, rumbo, rivales, abanico) if rivales else list(barrido_sin_rivales)
        objetivos = p.get('objetivos', len(rivales) if rivales else None)
        salida.append(dict(nombre=p['nombre'], movimientos=movimientos, barrido=barrido,
                           pitch=p.get('pitch', 0), objetivos=objetivos,
                           punto=tuple(actual), rumbo=round(normalizar(rumbo), 1)))
    return salida


def describir(paradas):
    """Texto con los movimientos y barridos calculados, para revisarlos antes de la prueba."""
    lineas = []
    for p in paradas:
        lineas.append(f"{p['nombre']}: punto {p.get('punto')} rumbo {p.get('rumbo')}  objetivos {p['objetivos']}")
        for m in p['movimientos']:
            x, y, z, opciones = movimiento(m)
            extra = ''.join(f'  {k}={v}' for k, v in opciones.items())
            lineas.append(f'    x={x:+.2f} m  y={y:+.2f} m  z={z:+.0f} grados{extra}')
        lineas.append(f"    barrido {p['barrido']}")
    return '\n'.join(lineas)


if __name__ == '__main__':
    import circuito
    print(describir(circuito.PARADAS))
