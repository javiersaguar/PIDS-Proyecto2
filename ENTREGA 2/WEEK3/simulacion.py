"""Robot simulado para probar demo.py sin el RoboMaster.

Sustituye el paquete `robomaster` por uno falso con las mismas llamadas que usa la
demo. La cámara devuelve imágenes de una carpeta (por ejemplo, data_test) y cada
orden se apunta en `acciones`, de modo que se puede comprobar el recorrido y
que ninguna velocidad supera la del SDK. Uso:

    python demo.py --simulacion          # imágenes de DATOS_ASIGNATURA/data_test
    python demo.py --simulacion CARPETA

Solo sirve para probar la lógica: no simula la geometría del circuito.
"""

import glob
import math
import os
import sys
import time
import types

import cv2

# Velocidades por defecto del SDK: el enunciado prohíbe superarlas
MAX_XY, MAX_Z, MAX_GIMBAL = 0.5, 30, 30

CARPETA_IMAGENES = None   # se fija con instalar()
RETARDO = 0.0             # segundos de espera simulada por acción
PASO_IMAGEN = 0.1         # segundos simulados que pasan en cada lectura de la cámara
BATERIA = 87              # % que devuelve la batería simulada


class Accion:
    is_completed = True

    def __init__(self, robot, tipo, **datos):
        robot.acciones.append(dict(tipo=tipo, **datos))

    def wait_for_completed(self, timeout=None):
        time.sleep(RETARDO)
        return True


class AccionMovimiento(Accion):
    """Movimiento del chasis: acaba cuando pasa su duración en tiempo simulado."""

    def __init__(self, robot, fin, tipo, **datos):
        super().__init__(robot, tipo, **datos)
        self.r, self.fin = robot, fin

    @property
    def is_completed(self):
        return self.r.t >= self.fin - 1e-9

    def wait_for_completed(self, timeout=None):
        if self.r.t < self.fin:
            self.r.avanzar(self.fin - self.r.t)
        return True


def _comprobar(nombre, valor, maximo):
    if valor is not None and abs(valor) > maximo + 1e-9:
        raise AssertionError(f'{nombre}={valor} supera la velocidad máxima permitida ({maximo})')


class Chasis:
    def __init__(self, r):
        self.r = r

    def move(self, x=0, y=0, z=0, xy_speed=0.5, z_speed=30):
        _comprobar('xy_speed', xy_speed, MAX_XY)
        _comprobar('z_speed', z_speed, MAX_Z)
        # La posición avanza con el tiempo simulado (traslación y luego giro) hasta acabar
        duracion = (x * x + y * y) ** 0.5 / max(xy_speed, 1e-6) + abs(z) / max(z_speed, 1e-6)
        inicio = self.r.pose
        r = math.radians(inicio[2])
        fin = (inicio[0] + x * math.cos(r) + y * math.sin(r), inicio[1] + x * math.sin(r) - y * math.cos(r),
               inicio[2] + z)
        self.r.movimiento = dict(t0=self.r.t, t1=self.r.t + duracion, inicio=inicio, fin=fin)
        return AccionMovimiento(self.r, self.r.t + duracion, 'chasis.move', x=x, y=y, z=z, xy_speed=xy_speed,
                                z_speed=z_speed)

    def drive_speed(self, x=0, y=0, z=0, timeout=None):
        _comprobar('x', x, MAX_XY)
        _comprobar('y', y, MAX_XY)
        _comprobar('z', z, MAX_Z)
        return Accion(self.r, 'chasis.drive_speed', x=x, y=y, z=z)


class Gimbal:
    """Gimbal con su ángulo. Con drive_speed gira a velocidad constante mientras pasa el
    tiempo simulado; move, moveto y recenter cortan esa velocidad y consumen el tiempo del giro."""

    def __init__(self, r):
        self.r = r
        self.yaw = 0.0
        self.pitch = 0.0
        self.v_yaw = self.v_pitch = 0.0
        self._callback = None

    def _avisar(self):
        if self._callback is not None:
            self._callback((self.pitch, self.yaw, self.pitch, self.yaw))

    def avanzar(self, dt):
        if self.v_yaw or self.v_pitch:
            self.yaw += self.v_yaw * dt
            self.pitch = max(-20.0, min(35.0, self.pitch + self.v_pitch * dt))
            self._avisar()

    def _girar(self, d_yaw, d_pitch, velocidad):
        self.v_yaw = self.v_pitch = 0.0
        self.r.avanzar(max(abs(d_yaw), abs(d_pitch)) / max(velocidad, 1e-6))
        self.yaw += d_yaw
        self.pitch += d_pitch
        self._avisar()

    def move(self, pitch=0, yaw=0, pitch_speed=30, yaw_speed=30):
        _comprobar('pitch_speed', pitch_speed, MAX_GIMBAL)
        _comprobar('yaw_speed', yaw_speed, MAX_GIMBAL)
        self._girar(yaw, pitch, min(pitch_speed, yaw_speed))
        return Accion(self.r, 'gimbal.move', pitch=pitch, yaw=yaw)

    def moveto(self, pitch=0, yaw=0, pitch_speed=30, yaw_speed=30):
        _comprobar('pitch_speed', pitch_speed, MAX_GIMBAL)
        _comprobar('yaw_speed', yaw_speed, MAX_GIMBAL)
        self._girar(yaw - self.yaw, pitch - self.pitch, min(pitch_speed, yaw_speed))
        return Accion(self.r, 'gimbal.moveto', pitch=pitch, yaw=yaw)

    def recenter(self, pitch_speed=30, yaw_speed=30):
        _comprobar('pitch_speed', pitch_speed, MAX_GIMBAL)
        _comprobar('yaw_speed', yaw_speed, MAX_GIMBAL)
        self._girar(-self.yaw, -self.pitch, min(pitch_speed, yaw_speed))
        self.yaw = self.pitch = 0.0
        return Accion(self.r, 'gimbal.recenter')

    def drive_speed(self, pitch_speed=0, yaw_speed=0):
        _comprobar('pitch_speed', pitch_speed, MAX_GIMBAL)
        _comprobar('yaw_speed', yaw_speed, MAX_GIMBAL)
        self.v_yaw, self.v_pitch = yaw_speed, pitch_speed
        return Accion(self.r, 'gimbal.drive_speed', pitch_speed=pitch_speed, yaw_speed=yaw_speed)

    def sub_angle(self, freq=5, callback=None, *args):
        self._callback = callback
        self._avisar()
        return True

    def unsub_angle(self):
        self._callback = None
        return True


class Camara:
    def __init__(self, r):
        self.r = r
        patrones = ['*.jpg', '*.png', os.path.join('**', '*.jpg'), os.path.join('**', '*.png')]
        ficheros = set()
        for p in patrones:
            ficheros.update(glob.glob(os.path.join(CARPETA_IMAGENES or '.', p), recursive=True))
        self.ficheros = sorted(ficheros)
        if not self.ficheros:
            raise FileNotFoundError(f'No hay imágenes en {CARPETA_IMAGENES}')
        self.i = 0
        self.abierta = False

    def start_video_stream(self, display=False, resolution=None):
        self.abierta = True
        Accion(self.r, 'camara.start')

    def read_cv2_image(self, timeout=3, strategy='pipeline'):
        assert self.abierta, 'Se lee la cámara sin haber abierto el vídeo'
        self.r.avanzar(PASO_IMAGEN)   # cada lectura es un fotograma más (unas 10 por segundo con GPU)
        fichero = self.ficheros[self.i % len(self.ficheros)]
        self.i += 1
        Accion(self.r, 'camara.leer', fichero=os.path.basename(fichero))
        return cv2.imread(fichero)

    def stop_video_stream(self):
        self.abierta = False
        Accion(self.r, 'camara.stop')


class Blaster:
    def __init__(self, r):
        self.r = r

    def fire(self, fire_type='water', times=1):
        return Accion(self.r, 'blaster.fire', fire_type=fire_type, times=times)


class Led:
    def __init__(self, r):
        self.r = r

    def set_led(self, comp='all', r=0, g=0, b=0, effect='on', freq=1):
        return Accion(self.r, 'led', rgb=(r, g, b), effect=effect)


class Bateria:
    def __init__(self, r):
        self.r = r

    def sub_battery_info(self, freq, callback, *args):
        callback(BATERIA, *args)

    def unsub_battery_info(self):
        pass


class RobotSimulado:
    def __init__(self):
        self.acciones = []
        self.t = 0.0                  # tiempo simulado (s)
        self.movimiento = dict(t0=0.0, t1=0.0, inicio=(0.0, 0.0, 0.0), fin=(0.0, 0.0, 0.0))
        self.reloj = lambda: self.t   # la demo lo usa en lugar de time.monotonic
        self.chassis = Chasis(self)
        self.gimbal = Gimbal(self)
        self.camera = Camara(self)
        self.blaster = Blaster(self)
        self.led = Led(self)
        self.battery = Bateria(self)

    @property
    def pose(self):
        """(X adelante, Y a la izquierda en m, rumbo a la izquierda en grados), interpolada si se mueve."""
        m = self.movimiento
        if self.t >= m['t1'] or m['t1'] <= m['t0']:
            return m['fin']
        f = (self.t - m['t0']) / (m['t1'] - m['t0'])
        return tuple(a + f * (b - a) for a, b in zip(m['inicio'], m['fin']))

    def avanzar(self, dt):
        """Hace pasar `dt` segundos simulados; el gimbal sigue girando si tiene velocidad."""
        self.gimbal.avanzar(dt)
        self.t += dt

    def initialize(self, conn_type='sta', sn=None):
        return True

    def set_robot_mode(self, mode='free'):
        return Accion(self, 'modo', mode=mode)

    def play_sound(self, sound_id, times=1):
        return Accion(self, 'sonido', id=sound_id, times=times)

    def play_audio(self, filename):
        return Accion(self, 'audio', fichero=os.path.basename(filename))

    def disparos(self):
        return sum(a['times'] for a in self.acciones if a['tipo'] == 'blaster.fire')

    def close(self):
        Accion(self, 'cerrar')


ULTIMO = None   # último robot creado, para revisarlo en las pruebas


def _robot_factory():
    global ULTIMO
    ULTIMO = RobotSimulado()
    return ULTIMO


def instalar(carpeta_imagenes, retardo=0.0):
    """Registra el paquete `robomaster` falso. Hay que llamarlo antes de importar demo_utils."""
    global CARPETA_IMAGENES, RETARDO
    CARPETA_IMAGENES, RETARDO = carpeta_imagenes, retardo

    paquete = types.ModuleType('robomaster')
    paquete.__path__ = []
    m_robot = types.ModuleType('robomaster.robot')
    m_robot.Robot = _robot_factory
    m_robot.FREE, m_robot.GIMBAL_LEAD, m_robot.CHASSIS_LEAD = 'free', 'gimbal_lead', 'chassis_lead'
    m_blaster = types.ModuleType('robomaster.blaster')
    m_blaster.INFRARED_FIRE, m_blaster.WATER_FIRE = 'ir', 'water'
    m_camera = types.ModuleType('robomaster.camera')
    m_camera.STREAM_360P, m_camera.STREAM_540P, m_camera.STREAM_720P = '360p', '540p', '720p'
    m_led = types.ModuleType('robomaster.led')
    m_led.COMP_ALL, m_led.EFFECT_ON, m_led.EFFECT_OFF = 'all', 'on', 'off'
    m_led.EFFECT_FLASH, m_led.EFFECT_BREATH, m_led.EFFECT_SCROLLING = 'flash', 'breath', 'scrolling'
    for nombre, modulo in [('robot', m_robot), ('blaster', m_blaster), ('camera', m_camera), ('led', m_led)]:
        setattr(paquete, nombre, modulo)
        sys.modules['robomaster.' + nombre] = modulo
    sys.modules['robomaster'] = paquete
