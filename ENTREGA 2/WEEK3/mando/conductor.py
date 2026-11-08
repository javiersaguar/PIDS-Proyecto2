"""Hilo propietario del SDK y vigilancia de las órdenes del navegador."""
import collections
import json
import math
import os
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Ajustes locales, ignorados por Git. Si no existen se parte de la plantilla versionada.
CONFIG = BASE / 'config_mando.json'
EJEMPLO = BASE / 'config_mando.ejemplo.json'

CADUCIDAD = .3      # s sin órdenes del navegador antes de parar y desarmar
EDAD_AUTO = .5      # s como mucho entre la imagen y el disparo automático
GIRO_AUTO = 2.0     # º que puede haberse movido la torreta desde esa imagen
GIRO_CHASIS = 30    # º/s del chasis con L1/R1 o Z/X (límite del proyecto)
REPOSO = ([0, 0], [0, 0], False, 0)


def leer_config():
    ruta = CONFIG if CONFIG.is_file() else EJEMPLO
    return json.loads(ruta.read_text(encoding='utf-8-sig'))


def numero(valor, minimo, maximo):
    valor = float(valor)
    if not math.isfinite(valor):
        raise ValueError('Valor no finito')
    return max(minimo, min(maximo, valor))


def control(datos):
    mover = [numero(v, -1, 1) for v in datos['mover']]
    mirar = [numero(v, -1, 1) for v in datos['mirar']]
    if len(mover) != 2 or len(mirar) != 2 or not isinstance(datos['disparo'], bool):
        raise ValueError('Control inválido')
    girar = numero(datos.get('girar', 0), -1, 1)
    norma = max(1, math.hypot(*mover))
    return [v / norma for v in mover], mirar, datos['disparo'], girar


def configuracion(datos):
    limites = {'velocidad': (0, .5), 'angular': (0, 30), 'umbral': (.95, 1),
               'intervalo': (.3, 10), 'volumen': (0, 1), 'volumen_motor': (0, 1),
               'zona_muerta': (.05, .5), 'sensibilidad': (.1, 2), 'retardo_ms': (0, 500)}
    salida = {}
    for k, v in datos.items():
        if k in limites:
            salida[k] = numero(v, *limites[k])
        elif k in ('automatico', 'asistente', 'cajas', 'motor', 'invertir', 'relativo_camara'):
            if not isinstance(v, bool):
                raise ValueError('Se esperaba un interruptor')
            salida[k] = v
        elif k in ('modo', 'audio', 'detector'):
            opciones = {'modo': ('free', 'fps'), 'audio': ('ordenador',),
                        'detector': ('gpu', 'cpu')}
            if v not in opciones[k]:
                raise ValueError('Opción pendiente de validar o no disponible')
            salida[k] = v
        elif k == 'controles':
            if not isinstance(v, dict) or len(json.dumps(v)) > 5000:
                raise ValueError('Controles inválidos')
            salida[k] = v
    if salida.get('modo') == 'fps':
        raise ValueError('GIMBAL_LEAD pendiente de medir en laboratorio')
    if salida.get('asistente'):
        raise ValueError('Asistente de puntería pendiente de calibración')
    return salida


def hacia_camara(mover, yaw):
    """Pasa (adelante, derecha) de la cámara a ejes del chasis; yaw > 0 a la derecha."""
    a = math.radians(yaw)
    f, r = mover
    return [f * math.cos(a) - r * math.sin(a), f * math.sin(a) + r * math.cos(a)]


class Conductor(threading.Thread):
    """Único hilo que habla con el SDK.

    El cerrojo solo protege el estado compartido con el servidor. Las órdenes al
    robot se mandan fuera de él, para que la parada y el vídeo no esperen.
    """

    def __init__(self, conectar, sin_mover=False, simulado=False, reloj=time.monotonic):
        super().__init__(daemon=True)
        self.conectar, self.sin_mover, self.simulado, self.reloj = conectar, sin_mover, simulado, reloj
        self.cerrojo = threading.RLock()
        self.fin = threading.Event()
        self.emergencia = threading.Event()
        self.emergencia.set()
        self.cola = collections.deque(maxlen=1)
        self.config = dict(relativo_camara=True)
        self.config.update(configuracion(leer_config()))
        self.config['automatico'] = False
        self.orden = REPOSO
        self.ultimo = -float('inf')
        self.ultimo_disparo = -float('inf')
        self.estado = dict(error=None, aviso='', bateria=None, modo='free', velocidad=[0, 0],
                           yaw=0, pitch=0, fps=0, ms_detector=None, automatico=False,
                           disparos=0, sin_confirmar=0, emote=None, progreso=0,
                           detector='inactivo', armado=False, lectura_torreta=None)
        self.imagen = None
        self.resultado = None
        self.eventos = collections.deque(maxlen=100)
        self.baile = None
        self.audio_robot = None
        self._led = None
        self.estado['listo'] = False

    def recibir(self, datos):
        tipo = datos.get('tipo')
        with self.cerrojo:
            if tipo in ('control', 'emote', 'activar') and not self.estado['listo']:
                raise ValueError('Espera a que termine la preparación del robot')
            if tipo == 'parar':
                self.parar()
            elif tipo == 'control':
                orden = control(datos)
                if self.emergencia.is_set():
                    return
                self.orden = orden
                self.ultimo = self.reloj()
            elif tipo == 'emote':
                if self.emergencia.is_set() or self.reloj()-self.ultimo >= CADUCIDAD:
                    raise ValueError('Activa los controles antes de lanzar un emote')
                from coreografias import CATALOGO
                if datos.get('nombre') not in CATALOGO:
                    raise ValueError('Emote desconocido')
                self.cola.append(datos['nombre'])
            elif tipo in ('config', 'activar'):
                nuevos = configuracion(datos['config'])
                # Un cambio de ajustes exige recibir controles nuevos.
                self.parar()
                self.config.update(nuevos)
                temporal = CONFIG.with_suffix('.tmp')
                guardada = dict(self.config, automatico=False)
                temporal.write_text(json.dumps(guardada, ensure_ascii=False, indent=2), encoding='utf-8')
                os.replace(str(temporal), str(CONFIG))
                if tipo == 'activar':
                    self.ultimo = self.reloj()
                    self.emergencia.clear()
                    self.estado['armado'] = True
            else:
                raise ValueError('Mensaje desconocido')

    def parar(self):
        with self.cerrojo:
            self.emergencia.set()
            self.config['automatico'] = False
            self.orden = REPOSO
            self.cola.clear()
            self.estado['armado'] = False

    def foto(self):
        with self.cerrojo:
            return self.imagen

    def publicar(self, resultado):
        with self.cerrojo:
            self.resultado = resultado
            self.estado.update(ms_detector=resultado.get('ms'), detector=resultado.get('detector'),
                               aviso=resultado.get('aviso', ''))

    def instantanea(self):
        with self.cerrojo:
            salida = dict(self.estado, config=dict(self.config))
            if self.resultado:
                salida['age_ms'] = round(max(0, self.reloj()-self.resultado.get('instante', 0))*1000)
                salida['deteccion'] = {k: v for k, v in self.resultado.items()
                                       if k in ('boxes', 'scores', 'width', 'height')}
            return salida

    # --- órdenes al robot (solo desde este hilo y sin el cerrojo) -----------------------
    def velocidades(self, mover, mirar, girar=0):
        from demo_utils import limitar
        x, y = [v * self.config['velocidad'] for v in mover]
        if self.config.get('relativo_camara', True) and (x or y):
            # W lleva el robot hacia donde mira la cámara, no hacia el frente del chasis.
            x, y = hacia_camara([x, y], self.torreta.leer()[0])
        z = -limitar(girar * GIRO_CHASIS, GIRO_CHASIS)   # z > 0 gira a la izquierda
        if self.sin_mover:
            x = y = z = 0
        self.robot.chassis.drive_speed(x=x, y=y, z=z, timeout=.5)
        self.torreta.velocidad(limitar(mirar[0] * self.config['angular'], 30),
                               limitar(mirar[1] * self.config['angular'], 30))
        self.estado['velocidad'] = [x, y]

    def senal(self, nombre, parpadeo=False):
        """Cambia los LED solo si cambia el estado, para no saturar la conexión."""
        clave = ('senal', nombre, parpadeo)
        if clave != self._led:
            self.senales.estado(nombre, parpadeo=parpadeo)
            self._led = clave

    def color(self, rgb):
        from robomaster import led
        clave = ('rgb', tuple(rgb))
        if clave != self._led:
            self.robot.led.set_led(comp=led.COMP_ALL, r=rgb[0], g=rgb[1], b=rgb[2],
                                   effect=led.EFFECT_ON)
            self._led = clave

    def reposo(self):
        if self.baile:
            self.baile = None
            self._led = None
            self.eventos.append(dict(tipo='fin_emote'))
        self.velocidades([0, 0], [0, 0])
        if self.audio_robot:
            self.audio_robot.parar()
        # Centrado por velocidad: cancelable y sin esperar acciones largas.
        yaw, pitch = self.torreta.leer()
        self.torreta.velocidad(max(-30, min(30, -yaw*2)), max(-30, min(30, -pitch*2)))
        self.estado.update(emote=None, progreso=0, automatico=False)

    def blanco(self, resultado, ahora):
        """True si la última detección tiene un robot bajo la mira y sigue valiendo.

        Vale si la imagen es reciente y la torreta apenas se ha movido desde que se
        tomó (el mismo criterio de ángulo en el instante de la imagen que la demo).
        """
        if not resultado or ahora - resultado.get('instante', -float('inf')) >= EDAD_AUTO:
            return False
        from deteccion import regla_auto
        if regla_auto(resultado['boxes'], resultado['scores'], resultado['width'],
                      resultado['height'], self.config['umbral']) is None:
            return False
        import circuito as C
        yaw0, pitch0 = self.torreta.angulo_en(resultado['instante'] - C.RETARDO_CAMARA)
        yaw, pitch = self.torreta.leer()
        return abs(yaw - yaw0) <= GIRO_AUTO and abs(pitch - pitch0) <= GIRO_AUTO

    def disparar(self, ahora, auto, resultado):
        from robomaster import blaster
        self.ultimo_disparo = ahora
        try:
            confirmado = self.robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1)
            motivo = 'el robot no lo confirmó'
        except Exception as e:
            confirmado, motivo = False, str(e)
        if not confirmado:
            # Un disparo perdido no corta la sesión: se avisa y se sigue.
            self.estado['sin_confirmar'] += 1
            self.eventos.append(dict(tipo='aviso', mensaje='Disparo sin confirmar: ' + motivo))
            return
        self.estado['disparos'] += 1
        self.eventos.append(dict(tipo='disparo', numero=self.estado['disparos']))
        self.senal('disparando', parpadeo=True)
        if auto and resultado.get('image') is not None:
            import numpy as np
            pred = {k: np.asarray(resultado[k]) for k in ('boxes', 'scores')}
            self.registro.imagen(resultado['image'], pred, resultado.get('ms', 0),
                                 'mando', 'auto', self.torreta.yaw, self.torreta.pitch, disparos=1)

    def empezar_baile(self, nombre):
        from coreografias import validar
        from audio_robot import SILENCIO
        validar(nombre)
        self.robot.set_robot_mode(mode='free')
        # La música se envía con el robot quieto y ya precargada.
        self.velocidades([0, 0], [0, 0])
        self.audio_robot.reproducir(nombre)
        self.baile = (nombre, self.reloj() + SILENCIO)
        self.eventos.append(dict(tipo='emote', nombre=nombre))

    def paso(self):
        ahora = self.reloj()
        with self.cerrojo:
            armado = not self.emergencia.is_set()
            if armado and ahora - self.ultimo >= CADUCIDAD:
                self.emergencia.set()
                armado = False
                self.eventos.append(dict(tipo='desarmado',
                                         motivo='No llegan órdenes del navegador'))
            emote = None
            if not armado:
                self.config['automatico'] = False
                self.cola.clear()
            elif self.cola and not self.baile:
                emote = self.cola.pop()
                self.cola.clear()
            mover, mirar, disparo, girar = self.orden
            automatico = self.config['automatico']
            intervalo = self.config['intervalo']
            resultado = self.resultado
            self.estado['armado'] = armado
        if not armado:
            self.reposo()
            return
        if emote:
            self.empezar_baile(emote)
        if self.baile:
            self.paso_baile(ahora)
            return
        self.velocidades(mover, mirar, girar)
        auto = automatico and self.blanco(resultado, ahora)
        if (disparo or auto) and ahora - self.ultimo_disparo >= intervalo:
            self.disparar(ahora, auto, resultado)
        elif any(mover) or girar:
            self.senal('moviendo')
        self.estado['automatico'] = automatico

    def paso_baile(self, ahora):
        from coreografias import CATALOGO, muestra
        nombre, inicio = self.baile
        t = ahora - inicio + self.config['retardo_ms']/1000
        if t >= CATALOGO[nombre]['duracion']:
            # Al acabar se sigue con los controles armados: el navegador manda reposo
            # mientras dura el baile, así que el robot no arranca solo.
            self.baile = None
            self._led = None
            self.velocidades([0, 0], [0, 0])
            self.audio_robot.parar()
            self.estado.update(emote=None, progreso=0)
            self.eventos.append(dict(tipo='fin_emote'))
            return
        paso = muestra(nombre, t)
        self.robot.chassis.drive_speed(x=0 if self.sin_mover else paso['vx'],
                                       y=0 if self.sin_mover else paso['vy'],
                                       z=0 if self.sin_mover else paso['z'], timeout=.5)
        yaw, pitch = self.torreta.leer()
        self.torreta.velocidad(max(-30, min(30, (paso['yaw']-yaw)*4)),
                               max(-30, min(30, (paso['pitch']-pitch)*4)))
        self.color(paso['color'])
        self.estado.update(emote=nombre, progreso=max(0, min(1, t/CATALOGO[nombre]['duracion'])))

    def run(self):
        from demo_utils import Camara, Senales, Registro, nivel_bateria, liberar_cerrojo_sdk
        from demo import Torreta
        self.robot = self.camara = self.registro = self.torreta = None
        try:
            self.robot = self.conectar()
            self.robot.set_robot_mode(mode='free')
            self.estado['bateria'] = nivel_bateria(self.robot)
            if self.estado['bateria'] is not None and self.estado['bateria'] < 10:
                raise RuntimeError('Batería crítica, cargue el robot')
            if self.estado['bateria'] is not None and self.estado['bateria'] < 20:
                self.estado['aviso'] = 'Batería por debajo del 20 %'
            self.torreta = Torreta(self.robot)
            self.torreta.centrar()
            # Lee el ángulo real del gimbal; sin esto se estima con las órdenes y deriva.
            self.estado['lectura_torreta'] = self.torreta.comprobar_lectura()
            print('Torreta: ' + self.estado['lectura_torreta'], flush=True)
            self.senales = Senales(self.robot)
            from audio_robot import AudioRobot
            self.audio_robot = AudioRobot(self.robot, simulado=self.simulado)
            self.audio_robot.preparar(progreso=lambda texto: self.estado.update(aviso=texto))
            self.camara = Camara(self.robot, espera=0)
            self.registro = Registro(str(BASE.parent / 'evidencias' / 'mando'))
            self.parar()
            self.estado.update(listo=True, aviso='Emotes preparados en el robot' if not self.simulado
                               else 'Simulación: audio del robot registrado sin reproducir')
            anterior = 0
            while not self.fin.wait(.025):
                self.paso()
                ahora = self.reloj()
                if ahora - anterior >= .05:
                    if self.simulado:
                        frame = self.camara.capturar(0)
                        instante = ahora
                    else:
                        import cv2
                        with self.camara._cond:
                            frame = self.camara._ultimo
                            instante = self.camara._t_ultimo
                            frame = None if frame is None else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    if frame is not None:
                        with self.cerrojo:
                            self.imagen = (instante, frame)
                        self.estado['fps'] = round(1/max(.001, ahora-anterior), 1)
                    anterior = ahora
                self.estado['yaw'], self.estado['pitch'] = self.torreta.leer()
        except Exception as e:
            if self.robot:
                liberar_cerrojo_sdk(self.robot, e)
            self.estado['error'] = str(e)
            self.parar()
        finally:
            self.estado['listo'] = False
            if self.robot:
                for cerrar in [lambda: self.robot.chassis.drive_speed(x=0,y=0,z=0,timeout=.5),
                               lambda: self.audio_robot and self.audio_robot.parar(),
                               lambda: self.torreta and self.torreta.centrar(),
                               lambda: self.torreta and self.torreta.cancelar_lectura(),
                               lambda: self.senales.estado('apagado'),
                               lambda: self.camara and self.camara.cerrar(),
                               lambda: self.registro and self.registro.cerrar(dict(disparos=self.estado['disparos'])),
                               self.robot.close]:
                    try:
                        cerrar()
                    except Exception:
                        pass
