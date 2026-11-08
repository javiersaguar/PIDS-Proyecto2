"""Hilo propietario del SDK y vigilancia de las órdenes del navegador."""
import collections
import json
import math
import os
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / 'config_mando.json'


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
    norma = max(1, math.hypot(*mover))
    return [v / norma for v in mover], mirar, datos['disparo']


def configuracion(datos):
    limites = {'velocidad': (0, .5), 'angular': (0, 30), 'umbral': (.95, 1),
               'intervalo': (.3, 10), 'volumen': (0, 1), 'volumen_motor': (0, 1),
               'zona_muerta': (.05, .5), 'sensibilidad': (.1, 2), 'retardo_ms': (0, 500)}
    salida = {}
    for k, v in datos.items():
        if k in limites:
            salida[k] = numero(v, *limites[k])
        elif k in ('automatico', 'asistente', 'cajas', 'motor', 'invertir'):
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
    return salida


class Conductor(threading.Thread):
    def __init__(self, conectar, sin_mover=False, simulado=False, reloj=time.monotonic):
        super().__init__(daemon=True)
        self.conectar, self.sin_mover, self.simulado, self.reloj = conectar, sin_mover, simulado, reloj
        self.cerrojo = threading.RLock()
        self.fin = threading.Event()
        self.emergencia = threading.Event()
        self.emergencia.set()
        self.cola = collections.deque(maxlen=1)
        self.config = configuracion(json.loads(CONFIG.read_text(encoding='utf-8-sig')))
        self.config['automatico'] = False
        self.orden = ([0, 0], [0, 0], False)
        self.ultimo = -float('inf')
        self.ultimo_disparo = -float('inf')
        self.estado = dict(error=None, aviso='', bateria=None, modo='free', velocidad=[0, 0],
                           yaw=0, pitch=0, fps=0, ms_detector=None, automatico=False,
                           disparos=0, emote=None, progreso=0, detector='inactivo')
        self.imagen = None
        self.resultado = None
        self.eventos = collections.deque(maxlen=100)
        self.baile = None

    def recibir(self, datos):
        tipo = datos.get('tipo')
        with self.cerrojo:
            if tipo == 'parar':
                self.parar()
            elif tipo == 'control':
                self.orden = control(datos)
                self.ultimo = self.reloj()
                self.emergencia.clear()
            elif tipo == 'emote':
                from coreografias import CATALOGO
                if datos.get('nombre') not in CATALOGO:
                    raise ValueError('Emote desconocido')
                self.cola.append(datos['nombre'])
            elif tipo == 'config':
                nuevos = configuracion(datos['config'])
                # Un cambio de ajustes exige recibir controles nuevos.
                self.parar()
                self.config.update(nuevos)
                temporal = CONFIG.with_suffix('.tmp')
                temporal.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding='utf-8')
                os.replace(str(temporal), str(CONFIG))
            else:
                raise ValueError('Mensaje desconocido')

    def parar(self):
        with self.cerrojo:
            self.emergencia.set()
            self.config['automatico'] = False
            self.orden = ([0, 0], [0, 0], False)
            self.cola.clear()

    def foto(self):
        with self.cerrojo:
            return self.imagen

    def publicar(self, resultado):
        with self.cerrojo:
            self.resultado = resultado

    def instantanea(self):
        with self.cerrojo:
            salida = dict(self.estado, config=dict(self.config))
            if self.resultado:
                salida['deteccion'] = {k: v for k, v in self.resultado.items()
                                       if k in ('boxes', 'scores', 'width', 'height')}
            return salida

    def velocidades(self, mover, mirar):
        from demo_utils import limitar
        x, y = [v * self.config['velocidad'] for v in mover]
        if self.sin_mover:
            x = y = 0
        self.robot.chassis.drive_speed(x=x, y=y, z=0, timeout=.5)
        self.torreta.velocidad(limitar(mirar[0] * self.config['angular'], 30),
                              limitar(mirar[1] * self.config['angular'], 30))
        self.estado['velocidad'] = [x, y]

    def paso(self):
        ahora = self.reloj()
        with self.cerrojo:
            caducado = self.emergencia.is_set() or ahora - self.ultimo >= .3
            mover, mirar, disparo = self.orden
            if caducado:
                self.config['automatico'] = False
                self.cola.clear()
                if self.baile:
                    self.baile = None
                    self.eventos.append(dict(tipo='fin_emote'))
                self.velocidades([0, 0], [0, 0])
                # Centrado por velocidad: cancelable y sin esperar acciones largas.
                yaw, pitch = self.torreta.leer()
                self.torreta.velocidad(max(-30, min(30, -yaw*2)), max(-30, min(30, -pitch*2)))
                self.estado.update(emote=None, progreso=0, automatico=False)
                return
            if self.cola and not self.baile:
                from coreografias import CATALOGO
                nombre = self.cola.pop()
                self.cola.clear()
                self.baile = (nombre, ahora)
                self.robot.set_robot_mode(mode='free')
                self.eventos.append(dict(tipo='emote', nombre=nombre))
            if self.baile:
                self.paso_baile(ahora)
                return
            self.velocidades(mover, mirar)
            resultado = self.resultado
            auto = False
            if resultado and ahora - resultado.get('instante', -float('inf')) < .3:
                from deteccion import regla_auto
                auto = self.config['automatico'] and regla_auto(
                    resultado['boxes'], resultado['scores'], resultado['width'],
                    resultado['height'], self.config['umbral'])
            if (disparo or auto) and ahora - self.ultimo_disparo >= self.config['intervalo']:
                from robomaster import blaster
                if not self.robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1):
                    raise RuntimeError('El blaster no confirmó el disparo')
                self.ultimo_disparo = ahora
                self.estado['disparos'] += 1
                self.eventos.append(dict(tipo='disparo', numero=self.estado['disparos']))
                self.senales.estado('disparando', parpadeo=True)
                if auto and resultado.get('imagen') is not None:
                    import numpy as np
                    pred = {k: np.asarray(resultado[k]) for k in ('boxes', 'scores')}
                    self.registro.imagen(resultado['imagen'], pred, resultado.get('ms', 0),
                                         'mando', 'auto', self.torreta.yaw, self.torreta.pitch, disparos=1)
            elif any(mover):
                self.senales.estado('moviendo')
            self.estado['automatico'] = self.config['automatico']

    def paso_baile(self, ahora):
        from coreografias import CATALOGO, muestra
        from robomaster import led
        nombre, inicio = self.baile
        t = ahora - inicio + self.config['retardo_ms']/1000
        if t >= CATALOGO[nombre]['duracion']:
            self.baile = None
            self.velocidades([0, 0], [0, 0])
            self.parar()
            self.eventos.append(dict(tipo='fin_emote'))
            return
        paso = muestra(nombre, t)
        self.robot.chassis.drive_speed(x=0 if self.sin_mover else paso['vx'],
                                      y=0 if self.sin_mover else paso['vy'],
                                      z=0 if self.sin_mover else paso['z'], timeout=.5)
        yaw, pitch = self.torreta.leer()
        self.torreta.velocidad(max(-30, min(30, (paso['yaw']-yaw)*4)),
                              max(-30, min(30, (paso['pitch']-pitch)*4)))
        self.robot.led.set_led(comp=led.COMP_ALL, r=paso['color'][0], g=paso['color'][1],
                               b=paso['color'][2], effect=led.EFFECT_ON)
        self.estado.update(emote=nombre, progreso=min(1, t/CATALOGO[nombre]['duracion']))

    def run(self):
        from demo_utils import Camara, Senales, Registro, nivel_bateria, liberar_cerrojo_sdk
        from demo import Torreta
        self.robot = self.camara = self.registro = None
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
            self.senales = Senales(self.robot)
            self.camara = Camara(self.robot, espera=0)
            self.registro = Registro(str(BASE.parent / 'evidencias' / 'mando'))
            anterior = 0
            while not self.fin.wait(.025):
                self.paso()
                ahora = self.reloj()
                if ahora - anterior >= .05:
                    if self.simulado:
                        frame = self.camara.capturar(0)
                    else:
                        import cv2
                        with self.camara._cond:
                            frame = self.camara._ultimo
                            frame = None if frame is None else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    if frame is not None:
                        with self.cerrojo:
                            self.imagen = (ahora, frame)
                        self.estado['fps'] = round(1/max(.001, ahora-anterior), 1)
                    anterior = ahora
                self.estado['yaw'], self.estado['pitch'] = self.torreta.leer()
        except Exception as e:
            if self.robot:
                liberar_cerrojo_sdk(self.robot, e)
            self.estado['error'] = str(e)
            self.parar()
        finally:
            if self.robot:
                for cerrar in [lambda: self.robot.chassis.drive_speed(x=0,y=0,z=0,timeout=.5),
                               lambda: self.torreta.centrar(), lambda: self.senales.estado('apagado'),
                               lambda: self.camara and self.camara.cerrar(),
                               lambda: self.registro and self.registro.cerrar(dict(disparos=self.estado['disparos'])),
                               self.robot.close]:
                    try:
                        cerrar()
                    except Exception:
                        pass
