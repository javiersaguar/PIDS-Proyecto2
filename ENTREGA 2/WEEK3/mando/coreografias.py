"""Coreografías muestreadas a 20 Hz, sin esperas ni llamadas al robot.

Las posiciones de torreta son consignas absolutas. El Conductor las sigue a
como mucho 30 grados/s y ejecuta el chasis en FREE. Al acabar o cancelar debe
parar y centrar. Los recorridos se validan por integración antes de usarlos.
La sincronía y la deriva en el suelo requieren medición en el laboratorio.

Risa usa 1,5 grados a 3 Hz para respetar el límite angular. Waka reserva tres
segundos al giro de 45 grados y su vuelta. Super Estrella conserva los gestos
20/-20 de la torreta y 20/-40/20 del chasis de Demo.baile, con pasos interrumpibles.
"""
import math


CATALOGO = {
    'moonwalk': {'duracion': 48 * 60 / 117, 'bpm': 117},
    'waka': {'duracion': 11.681, 'bpm': 127},
    'superestrella': {'duracion': 27.131, 'bpm': 0},
    'risa': {'duracion': 3.15, 'bpm': 180},
}
BLANCO = (255, 255, 255)
COLORES = [(255, 255, 255), (255, 40, 150), (255, 220, 0), (30, 100, 255)]
FIESTA = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0),
          (0, 255, 255), (0, 0, 255), (255, 0, 255)]


def _triangulo(fase):
    return 1.0 - abs(2.0 * fase - 1.0)


def _pasos_moonwalk(t, local, sentido, s):
    tiempo = 60 / 117
    fase = local % tiempo
    s['vx'] = sentido * .25 * math.sin(math.pi * fase / .35) ** 2 if fase < .35 else 0.0
    s['pitch'] = -15 + 7 * _triangulo(fase / tiempo)
    s['color'] = COLORES[int(t / tiempo) % len(COLORES)]


def _moonwalk(t, salida):
    compas = 4 * 60 / 117
    salida['pitch'] = -15.0
    if t < compas:
        salida['pitch'] = -15 * min(1.0, t / .6)
    elif t < 3 * compas:
        _pasos_moonwalk(t, t - compas, -1, salida)
    elif t < 6 * compas:
        salida['yaw'] = 180 * (t - 3 * compas) / (3 * compas)
        salida['color'] = BLANCO if int(t * 10) % 2 else (0, 0, 0)
    elif t < 8 * compas:
        salida['yaw'] = 180.0
        _pasos_moonwalk(t, t - 6 * compas, 1, salida)
    elif t < 11 * compas:
        salida['yaw'] = 180 * (1 - (t - 8 * compas) / (3 * compas))
    else:
        fase = t - 11 * compas
        salida['pitch'] = -15 + 35 * fase / 1.25 if fase < 1.25 else 20 * (12 * compas - t) / (compas - 1.25)


def _waka(t, salida):
    periodo = 2 * 60 / 127
    contoneo = 9 * periodo
    if t < contoneo:
        fase = (t % periodo) / periodo
        salida['vy'] = .2 * math.sin(2 * math.pi * fase)
        salida['yaw'] = -4 * math.sin(2 * math.pi * fase)
        salida['pitch'] = 8 * _triangulo(fase)
        salida['color'] = [(0, 180, 70), (255, 220, 0), (255, 0, 0), (0, 80, 255)][int(t * 127 / 60) % 4]
    elif t >= CATALOGO['waka']['duracion'] - 3:
        salida['z'] = 30 if t < CATALOGO['waka']['duracion'] - 1.5 else -30
        salida['color'] = (255, 220, 0)


def _superestrella(t, salida):
    # Un ciclo termina en su rumbo original antes de repetirlo.
    ciclo = 16 / 3
    if t >= 5 * ciclo:
        return
    fase = t % ciclo
    salida['color'] = FIESTA[int(t * 10) % len(FIESTA)]
    if fase < 2 / 3:
        salida['yaw'], salida['pitch'] = fase * 30, fase * 15
    elif fase < 2:
        salida['yaw'] = 20 - (fase - 2 / 3) * 30
        salida['pitch'] = 10 - (fase - 2 / 3) * 11.25
    elif fase < 8 / 3:
        salida['yaw'] = -20 + (fase - 2) * 30
        salida['pitch'] = -5 + (fase - 2) * 7.5
    elif fase < 10 / 3:
        salida['z'] = 30
    elif fase < 14 / 3:
        salida['z'] = -30
    else:
        salida['z'] = 30


def _risa(t, salida):
    salida['color'] = (255, 220, 0) if int(t * 10) % 2 else (0, 0, 0)
    if t < 2:
        salida['pitch'] = 1.5 * math.sin(6 * math.pi * t)
        salida['z'] = 6 * math.pi * math.cos(6 * math.pi * t)
    elif t < 2.4:
        salida['pitch'] = -10 * (t - 2) / .4
    else:
        salida['pitch'] = -10 * (CATALOGO['risa']['duracion'] - t) / .75


BAILES = {'moonwalk': _moonwalk, 'waka': _waka,
          'superestrella': _superestrella, 'risa': _risa}


def muestra(nombre, tiempo):
    """Consigna instantánea. Fuera del baile devuelve reposo con LED apagados."""
    duracion = CATALOGO[nombre]['duracion']
    if not math.isfinite(tiempo):
        raise ValueError('El tiempo del baile debe ser finito')
    salida = dict(vx=0.0, vy=0.0, z=0.0, yaw=0.0, pitch=0.0, color=(0, 0, 0))
    if 0 <= tiempo < duracion:
        salida['color'] = BLANCO
        BAILES[nombre](tiempo, salida)
    return salida


obtener = muestra


def validar(nombre, paso=.01):
    """Comprueba velocidades, pendientes de torreta y el recorrido en coordenadas mundo.

    Devuelve la excursión y la pose final del modelo cinemático. La deriva real
    de las ruedas y la respuesta de la torreta quedan pendientes de laboratorio.
    """
    duracion = CATALOGO[nombre]['duracion']
    x, y, rumbo = 0.0, 0.0, 0.0
    xmin = xmax = ymin = ymax = 0.0
    anterior = muestra(nombre, 0)
    t = 0.0
    while t < duracion:
        dt = min(paso, duracion - t)
        actual = muestra(nombre, t + dt / 2)
        if math.hypot(actual['vx'], actual['vy']) > .5 or abs(actual['z']) > 30:
            raise ValueError('El baile supera la velocidad permitida')
        siguiente = muestra(nombre, t + dt)
        for eje in ('yaw', 'pitch'):
            if abs(siguiente[eje] - anterior[eje]) > 30 * dt + 1e-6:
                raise ValueError('El baile supera la velocidad de la torreta')
        angulo = math.radians(rumbo + actual['z'] * dt / 2)
        x += (actual['vx'] * math.cos(angulo) + actual['vy'] * math.sin(angulo)) * dt
        y += (actual['vx'] * math.sin(angulo) - actual['vy'] * math.cos(angulo)) * dt
        rumbo += actual['z'] * dt
        xmin, xmax = min(xmin, x), max(xmax, x)
        ymin, ymax = min(ymin, y), max(ymax, y)
        anterior = siguiente
        t += dt
    if xmax - xmin > 1 or ymax - ymin > 1:
        raise ValueError('El baile sale del cuadrado de un metro')
    if math.hypot(x, y) > .01 or abs(rumbo) > 1:
        raise ValueError('El baile no vuelve al origen en el modelo')
    return dict(x=x, y=y, rumbo=rumbo, ancho=xmax-xmin, alto=ymax-ymin)

