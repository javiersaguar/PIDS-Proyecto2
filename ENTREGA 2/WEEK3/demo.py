"""Demo del Bloque 3: recorrer el circuito, detectar a los RoboMasters rivales y dispararles.

La configuración (paradas, umbral, estrategia) está en circuito.py. Uso:

    python demo.py                      # demo completa
    python demo.py --sin-disparar       # recorrido y detección, sin usar el blaster
    python demo.py --sin-mover          # sin mover el chasis (solo gimbal, cámara y blaster)
    python demo.py --sin-mover --sin-disparar --paradas P2   # calibrar una parada
    python demo.py --simulacion                 # sin robot: ve las imágenes de test de la asignatura

Todas las imágenes a las que se aplica el detector se guardan en
evidencias/<fecha_hora>/ con las cajas y la confianza dibujadas, junto a
registro.csv y resumen.json.

Ctrl+C detiene el chasis, centra el gimbal, apaga los LED y cierra la conexión.
"""

import argparse
import collections
import os
import sys
import threading

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)


def argumentos(argv=None):
    p = argparse.ArgumentParser(description='Demo del Bloque 3 (grupo 2)')
    p.add_argument('--sin-disparar', action='store_true', help='no usar el blaster')
    p.add_argument('--sin-mover', action='store_true', help='no mover el chasis')
    p.add_argument('--paradas', default='', help='paradas donde detectar, separadas por comas (por defecto, todas)')
    p.add_argument('--simulacion', nargs='?', const=os.path.join(AQUI, '..', '..', 'ENTREGA 1', 'WEEK2', 'DATOS_ASIGNATURA', 'data_test'), default=None,
                   metavar='CARPETA', help='usar un robot simulado que ve las imágenes de CARPETA')
    p.add_argument('--modelo', default=None, help='ruta del checkpoint (por defecto, la de circuito.py)')
    p.add_argument('--arquitectura', default=None, help='arquitectura del checkpoint (por defecto, la de circuito.py)')
    p.add_argument('--ver', action='store_true', help='mostrar en una ventana cada imagen analizada')
    p.add_argument('--umbral', type=float, default=None, help='umbral de confianza (por defecto, el de circuito.py)')
    p.add_argument('--evidencias', default=os.path.join(AQUI, 'evidencias'), help='carpeta de salida')
    p.add_argument('--conexion', choices=['auto', 'wifi', 'networking'], default='auto',
                   help='modo de conexión; auto: networking con serial_number.txt, salvo en la wifi del robot')
    return p.parse_args(argv)


# El robot simulado sustituye al SDK, así que tiene que instalarse antes de importar demo_utils
if __name__ == '__main__' and '--simulacion' in sys.argv:
    import simulacion
    simulacion.instalar(argumentos().simulacion)

from demo_utils import *  # noqa: E402,F401,F403
import circuito as C      # noqa: E402


def detect_and_shoot(ep_robot, model, score_threshold=0.5, resize_shape=None):
    """Capture an image, detect the enemy robot, aim the gimbal at it and shoot.

    Versión básica de la plantilla (una captura, un disparo al mejor). La demo
    usa Demo.atacar_parada, que barre la parada, confirma la puntería y dispara 12 veces.
    :return: (image, prediction), igual que predict().
    """

    # --- STEP 1: capture the frame and run the detector (done for you) --------
    image, prediction = predict(ep_robot, model, resize_shape=resize_shape)

    # --- STEP 2: choose the best detection ------------------------------------
    keep = prediction['scores'] >= score_threshold
    if not keep.any():
        return image, prediction
    best_box = prediction['boxes'][keep][np.argmax(prediction['scores'][keep])]

    # --- STEP 3: aim the gimbal at the target ---------------------------------
    alpha = auto_aim(image, best_box)
    ep_robot.gimbal.move(pitch=0, yaw=alpha, pitch_speed=VEL_GIMBAL_MAX, yaw_speed=VEL_GIMBAL_MAX).wait_for_completed(timeout=10)

    # --- STEP 4: shoot --------------------------------------------------------
    if not ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1):
        raise RuntimeError('El blaster no confirmó el disparo infrarrojo')

    return image, prediction


class Torreta:
    """Gimbal con su ángulo respecto al chasis (yaw > 0 a la derecha, pitch > 0 arriba).

    Al llegar a cada parada se centra (queda alineado con el chasis). Se mueve de
    dos formas: con giros hasta un ángulo (`ir`), para barrer, y con velocidad
    (`velocidad`), para seguir a un robot que se mueve.

    El ángulo se lee del propio gimbal (sub_angle) si `comprobar_lectura` ha
    verificado que la lectura sigue a los giros; si no, se estima por software
    sumando los giros y la velocidad mandada por el tiempo transcurrido.
    """

    YAW_MAX = 240                     # el gimbal admite unos ±250º
    PITCH_MIN, PITCH_MAX = -20, 30    # el gimbal admite unos -20º/+35º

    def __init__(self, ep_robot, reloj=time.monotonic):
        self.ep_robot = ep_robot
        self.gimbal = ep_robot.gimbal
        self.reloj = reloj
        self.yaw = 0.0                # estimación por software
        self.pitch = 0.0
        self.medida = None            # último (pitch, yaw) leído con sub_angle
        self.usar_medida = False
        self.signos = (1, 1)          # (pitch, yaw): sentido de la lectura respecto a los giros
        self.suscrito = False
        self._v = (0.0, 0.0)          # (yaw, pitch) º/s mandados con drive_speed
        self._t_v = None
        self._enviado = None          # instante del último drive_speed enviado
        self.historial = collections.deque(maxlen=200)   # (t, yaw, pitch) de cada lectura

    def angulo_en(self, t):
        """(yaw, pitch) que tenía la torreta en el instante `t`, interpolando el historial.

        El fotograma que llega de la cámara es de hace RETARDO_CAMARA s: para saber
        hacia dónde está un robot hay que sumar su desvío en la imagen al ángulo de
        entonces, no al de ahora.
        """
        self.leer()
        h = self.historial
        if t >= h[-1][0]:
            return h[-1][1], h[-1][2]
        if t <= h[0][0]:
            return h[0][1], h[0][2]
        for (t0, y0, p0), (t1, y1, p1) in zip(reversed(list(h)[:-1]), reversed(list(h)[1:])):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                return y0 + f * (y1 - y0), p0 + f * (p1 - p0)
        return h[-1][1], h[-1][2]

    # --- lectura del ángulo -------------------------------------------------------
    def _al_medir(self, info):
        self.medida = (float(info[0]), float(info[1]))

    def comprobar_lectura(self, giro=20, cabeceo=10):
        """Gira la torreta y comprueba que sub_angle la sigue; si es así, se usa a partir de ahora.

        Fija también el sentido de la lectura, que puede ir al revés que los giros.
        :return: texto con el resultado, para mostrarlo en la consola.
        """
        self.usar_medida = False
        try:
            self.gimbal.sub_angle(freq=20, callback=self._al_medir)
            self.suscrito = True
        except Exception as e:
            return f'sin lectura del ángulo ({e}): se estima por software'
        self.centrar()
        fin = time.time() + 2
        while self.medida is None and time.time() < fin:
            time.sleep(0.05)
        if self.medida is None:
            return 'el gimbal no envía su ángulo: se estima por software'
        p0, y0 = self.medida
        self.ir(giro, cabeceo)
        time.sleep(0.3)
        p1, y1 = self.medida
        self.centrar()
        d_pitch, d_yaw = p1 - p0, y1 - y0
        if abs(abs(d_yaw) - giro) > 0.3 * giro or abs(abs(d_pitch) - cabeceo) > 0.5 * cabeceo:
            return (f'la lectura no sigue al giro (yaw {d_yaw:+.1f} de {giro}, pitch {d_pitch:+.1f} de {cabeceo}): '
                    'se estima por software')
        self.signos = (1 if d_pitch > 0 else -1, 1 if d_yaw > 0 else -1)
        self.usar_medida = True
        return f'lectura del ángulo comprobada (signos pitch {self.signos[0]:+d}, yaw {self.signos[1]:+d})'

    def cancelar_lectura(self):
        if self.suscrito:
            self.gimbal.unsub_angle()
            self.suscrito = False

    def leer(self):
        """(yaw, pitch) actuales respecto al chasis."""
        if self._t_v is not None:     # integra la velocidad mandada desde la última lectura
            ahora = self.reloj()
            dt = ahora - self._t_v
            self.yaw += self._v[0] * dt
            self.pitch += self._v[1] * dt
            self._t_v = ahora
        if self.usar_medida and self.medida is not None:
            self.pitch, self.yaw = self.signos[0] * self.medida[0], self.signos[1] * self.medida[1]
        self.historial.append((self.reloj(), self.yaw, self.pitch))
        return self.yaw, self.pitch

    # --- movimiento ---------------------------------------------------------------------
    def velocidad(self, yaw_speed, pitch_speed=0.0):
        """Gira a velocidad constante (º/s, nunca más de la del SDK) hasta la siguiente orden."""
        yaw, pitch = self.leer()
        yaw_speed, pitch_speed = limitar(yaw_speed, VEL_GIMBAL_MAX), limitar(pitch_speed, VEL_GIMBAL_MAX)
        if (yaw >= self.YAW_MAX and yaw_speed > 0) or (yaw <= -self.YAW_MAX and yaw_speed < 0):
            yaw_speed = 0.0
        if (pitch >= self.PITCH_MAX and pitch_speed > 0) or (pitch <= self.PITCH_MIN and pitch_speed < 0):
            pitch_speed = 0.0
        ahora = self.reloj()
        # La misma orden se reenvía como mucho cada 0,2 s, para no saturar la conexión
        if (yaw_speed, pitch_speed) == self._v and self._enviado is not None and ahora - self._enviado < 0.2:
            return
        self.gimbal.drive_speed(pitch_speed=pitch_speed, yaw_speed=yaw_speed)
        self._enviado = ahora
        self._v = (yaw_speed, pitch_speed)
        self._t_v = ahora if (yaw_speed or pitch_speed) else None

    def parar(self):
        if self._v != (0.0, 0.0):
            self.leer()
            self.gimbal.drive_speed(pitch_speed=0, yaw_speed=0)
            self._v, self._t_v, self._enviado = (0.0, 0.0), None, None

    def centrar(self):
        self.parar()
        ejecutar_accion(self.ep_robot, lambda: self.gimbal.recenter(pitch_speed=VEL_GIMBAL_MAX,
                                                                    yaw_speed=VEL_GIMBAL_MAX),
                        timeout=20, que='gimbal (centrar)')
        self.yaw = self.pitch = 0.0

    def ir(self, yaw, pitch=None):
        self.parar()
        actual_yaw, actual_pitch = self.leer()
        yaw = max(-self.YAW_MAX, min(self.YAW_MAX, yaw))
        pitch = actual_pitch if pitch is None else max(self.PITCH_MIN, min(self.PITCH_MAX, pitch))
        d_yaw, d_pitch = yaw - actual_yaw, pitch - actual_pitch
        if abs(d_yaw) > 0.5 or abs(d_pitch) > 0.5:
            tiempo = max(abs(d_yaw), abs(d_pitch)) / VEL_GIMBAL_MAX
            ejecutar_accion(self.ep_robot, lambda: self.gimbal.move(pitch=d_pitch, yaw=d_yaw, pitch_speed=VEL_GIMBAL_MAX,
                                                                    yaw_speed=VEL_GIMBAL_MAX),
                            timeout=2 * tiempo + 5, que='gimbal')
        self.yaw, self.pitch = yaw, pitch
        self.historial.clear()        # tras un giro hasta un ángulo, el pasado ya no sirve
        self.leer()


class Demo:
    def __init__(self, ep_robot, model, args):
        self.ep_robot = ep_robot
        self.model = model
        self.args = args
        self.reloj = reloj_del_robot(ep_robot)
        self.torreta = Torreta(ep_robot, self.reloj)
        self.senales = Senales(ep_robot, C.SONIDOS)
        self.registro = Registro(args.evidencias, umbral=C.UMBRAL, mostrar=getattr(args, 'ver', False))
        self.camara = None
        self.ataques = []
        self.paradas_hechas = []
        self.pose = (0.0, 0.0, 0.0)   # posición del chasis en el circuito (X, Y en m; rumbo en grados)
        self.eventos_ruta = []        # ataques y esperas durante el recorrido
        self._aviso_ruta = False      # algo visto con el chasis en marcha que hay que revisar parado
        self._analisis_tramo = 0      # imágenes analizadas durante el tramo en curso
        self._ultimo_analisis = None
        self.memoria = Memoria(radio=C.RADIO_MISMO_ROBOT, error_distancia=C.ERROR_DISTANCIA,
                               tiempo_memoria=C.TIEMPO_MEMORIA, tiempo_descarte=C.TIEMPO_DESCARTE)
        self.audios_avisados = set()
        self.inicio = time.time()

    # --- piezas ---------------------------------------------------------------
    def mover(self, x, y, z, durante=None):
        """Mueve el chasis (x adelante, y derecha, z giro a la izquierda) sin pasar de la velocidad del SDK.

        `durante` se llama una y otra vez mientras el chasis está en marcha (vigilancia).
        """
        print(f'  chasis: x={x:+.2f} m  y={y:+.2f} m  z={z:+.0f} grados')
        if self.args.sin_mover:
            return
        medido = mover_chasis(self.ep_robot, x, y, z, C.VELOCIDAD_XY, C.VELOCIDAD_Z, que='chasis', durante=durante,
                              odometria=getattr(C, 'AVANCE_CON_ODOMETRIA', True))
        if medido is not None:
            print(f'    odometría: x={medido[0]:+.2f} m  y={medido[1]:+.2f} m')
        self.pose = mover_pose(self.pose, x, y, z)

    # --- vigilancia durante el recorrido -------------------------------------------------
    def todos_atacados(self):
        return C.ROBOTS_TOTALES is not None and len(self.memoria.atacados()) >= C.ROBOTS_TOTALES

    def evaluar_ruta(self, image, prediction, yaw_c, rumbo, alcance):
        """Revisa una imagen del recorrido.

        :param rumbo: dirección del avance respecto al chasis (grados, > 0 a la derecha).
        :param alcance: metros que quedan por recorrer en el tramo.
        :return: (bloqueo, nuevos). `bloqueo` es (distancia, yaw) del robot más cercano que hay
                 en el pasillo (ANCHO_PASILLO) hasta alcance + DISTANCIA_SEGURIDAD, o None.
                 `nuevos` son los rivales que no están en la memoria: (caja, confianza, yaw, distancia).
        """
        ahora = self.reloj()
        bloqueo, nuevos = None, []
        # Para el camino basta UMBRAL_SEGUIMIENTO: ante la duda, se espera
        for caja, score in seleccionar(prediction, min(C.UMBRAL, C.UMBRAL_SEGUIMIENTO)):
            angulo = yaw_c + C.SIGNO_YAW * auto_aim(image, caja)
            distancia = distancia_estimada(image, caja, C.ALTURA_ROBOT)
            if distancia is not None:
                rel = np.deg2rad(angulo - rumbo)
                delante, lateral = distancia * np.cos(rel), abs(distancia * np.sin(rel))
                if (0 < delante <= alcance + C.DISTANCIA_SEGURIDAD and lateral <= C.ANCHO_PASILLO / 2
                        and (bloqueo is None or distancia < bloqueo[0])):
                    bloqueo = (distancia, angulo)
            if score >= C.UMBRAL and not self.es_conocido(angulo, distancia, ahora):
                nuevos.append((caja, score, angulo, distancia))
        return bloqueo, nuevos

    def registrar_ruta(self, etiqueta, image, prediction, ms, yaw_c, pitch_c, bloqueo, nuevos):
        self.registro.imagen(image, prediction, ms, etiqueta, 'ruta', yaw_c, pitch_c,
                             objetivo=nuevos[0][0] if nuevos else None,
                             objetivo_yaw=nuevos[0][2] if nuevos else None,
                             distancia=bloqueo[0] if bloqueo else (nuevos[0][3] if nuevos else None))

    def vigilar(self, etiqueta, rumbo, alcance):
        """Con el chasis en marcha: analiza una imagen cada INTERVALO_RUTA s y avisa si hay algo que revisar.

        Lee siempre el fotograma más reciente, aunque no toque analizarlo, para no
        dejar que se acumulen en la cola de la cámara.
        """
        image = self.camara.capturar(0)
        ahora = self.reloj()
        if self._ultimo_analisis is not None and ahora - self._ultimo_analisis < C.INTERVALO_RUTA:
            time.sleep(0.02)
            return
        self._ultimo_analisis = ahora
        t_captura = ahora - C.RETARDO_CAMARA
        prediction, ms = detectar(self.model, image, C.RESIZE)
        yaw_c, pitch_c = self.torreta.angulo_en(t_captura)
        bloqueo, nuevos = self.evaluar_ruta(image, prediction, yaw_c, rumbo, alcance)
        self._analisis_tramo += 1
        self.registrar_ruta(etiqueta, image, prediction, ms, yaw_c, pitch_c, bloqueo, nuevos)
        if bloqueo is not None or (nuevos and C.ATACAR_EN_RUTA and not self.todos_atacados()):
            self._aviso_ruta = True

    def despejar(self, etiqueta, rumbo, alcance):
        """Con el chasis parado: ataca a los rivales nuevos y espera a que el camino esté libre.

        Si un robot sigue en el pasillo pasados ESPERA_OBSTACULO s, lo anota y sigue el
        recorrido; con DETENER_SI_BLOQUEADO detiene la demo (RuntimeError), que para el
        chasis y deja la torreta centrada.
        """
        inicio, ataques, esperando = self.reloj(), 0, False
        while True:
            image, prediction, ms = self.mirar(espera=C.RETARDO_CAMARA)
            yaw_c, pitch_c = self.torreta.leer()
            bloqueo, nuevos = self.evaluar_ruta(image, prediction, yaw_c, rumbo, alcance)
            self.registrar_ruta(etiqueta, image, prediction, ms, yaw_c, pitch_c, bloqueo, nuevos)
            if nuevos and C.ATACAR_EN_RUTA and ataques < 2 and not self.todos_atacados():
                for _, score, angulo, distancia in nuevos:
                    print(f'  rival visto en el recorrido en {angulo:+.0f} grados, a {distancia or 0:.1f} m')
                    final = self.seguir_y_disparar(etiqueta, angulo, score, (), distancia)
                    self.eventos_ruta.append(dict(tramo=etiqueta, tipo='ataque', yaw=round(angulo, 1),
                                                  completo=final is not None,
                                                  pose=[round(v, 2) for v in self.pose]))
                    ataques += 1
                self.torreta.ir(rumbo, C.PITCH_RUTA)
                self.senales.estado('moviendo')
                continue
            if bloqueo is None:
                if esperando:
                    self.eventos_ruta.append(dict(tramo=etiqueta, tipo='espera',
                                                  segundos=round(self.reloj() - inicio, 1),
                                                  pose=[round(v, 2) for v in self.pose]))
                    print(f'  camino libre tras {self.reloj() - inicio:.1f} s')
                    self.senales.estado('moviendo')
                return
            if self.reloj() - inicio > C.ESPERA_OBSTACULO:
                self.eventos_ruta.append(dict(tramo=etiqueta, tipo='bloqueado',
                                              segundos=round(self.reloj() - inicio, 1),
                                              distancia=round(bloqueo[0], 2), sigue=not C.DETENER_SI_BLOQUEADO,
                                              pose=[round(v, 2) for v in self.pose]))
                if C.DETENER_SI_BLOQUEADO:
                    raise RuntimeError(f'{etiqueta}: un robot bloquea el camino a {bloqueo[0]:.1f} m desde hace '
                                       f'{C.ESPERA_OBSTACULO} s')
                # Puede ser un rival ya inutilizado (no se va a apartar) o una distancia mal estimada
                # (ALTURA_ROBOT sin calibrar): la demo sigue en lugar de terminar
                print(f'[aviso] {etiqueta}: el robot del camino (a {bloqueo[0]:.1f} m) no se aparta en '
                      f'{C.ESPERA_OBSTACULO} s: se sigue el recorrido')
                self.senales.estado('moviendo')
                return
            if not esperando:
                print(f'  robot en el camino a {bloqueo[0]:.1f} m ({bloqueo[1]:+.0f} grados): esperando')
                self.senales.estado('obstaculo', parpadeo=True)
                esperando = True
            time.sleep(0.2)

    def recorrer(self, etiqueta, x, y, z):
        """Movimiento del recorrido entre paradas, vigilando el camino (VIGILANCIA).

        Los avances se dividen en tramos de TRAMO_VIGILANCIA m con la torreta mirando hacia
        donde va el robot. Antes del primer tramo, y tras cualquier tramo en el que se haya
        visto algo (o no se haya podido analizar ninguna imagen), el robot revisa parado
        (despejar). Los giros no se dividen; tras un giro se centra la torreta.
        """
        largo = (x * x + y * y) ** 0.5
        if not C.VIGILANCIA or self.args.sin_mover or largo < 1e-6 or z:
            self.mover(x, y, z)
            if C.VIGILANCIA and z and not self.args.sin_mover:
                self.torreta.centrar()
            return
        n = max(1, int(np.ceil(largo / C.TRAMO_VIGILANCIA - 1e-9)))
        paso = largo / n
        rumbo = float(np.rad2deg(np.arctan2(y, x)))   # y > 0 es a la derecha, como el yaw
        self.torreta.ir(rumbo, C.PITCH_RUTA)
        for i in range(n):
            if i == 0 or self._aviso_ruta or self._analisis_tramo == 0:
                self.despejar(etiqueta, rumbo, paso)
            self._aviso_ruta, self._analisis_tramo, self._ultimo_analisis = False, 0, None
            self.senales.estado('moviendo')
            self.mover(x / n, y / n, 0, durante=lambda: self.vigilar(etiqueta, rumbo, paso))

    def en_circuito(self, yaw, distancia):
        """Punto del circuito donde está un robot visto con ese yaw del gimbal y a esa distancia."""
        return None if distancia is None else punto_en_circuito(self.pose, yaw, distancia)

    def es_conocido(self, yaw, distancia, t):
        """True si la detección coincide con un robot ya atacado o un descarte reciente (ver Memoria).

        Sin MEMORIA solo cuentan los descartes: los robots atacados se siguen anotando (para las
        evidencias), pero no se usan para dejar de disparar, como en la versión de main.
        """
        tipos = None if C.MEMORIA else ('descartado',)
        return self.memoria.conocido(self.en_circuito(yaw, distancia), t, distancia, self.pose[:2],
                                     tipos=tipos) is not None

    def mirar(self, espera=None):
        """Captura y aplica el detector: (imagen, predicción, ms).

        Por defecto espera ESPERA_CAMARA para que la imagen salga quieta; al seguir
        a un robot se pasa espera=0 y se toma el fotograma más reciente.
        """
        image = self.camara.capturar(espera)
        prediction, ms = detectar(self.model, image, C.RESIZE)
        return image, prediction, ms

    def sonar_disparo(self, ya_sonado):
        """Sonido de la ráfaga: AUDIO_DISPARO (o el del SDK) una vez, o en cada disparo con SONIDO_CADA_DISPARO.

        Nunca espera: si hay otro sonido en curso, se omite y se reintenta en el disparo siguiente.
        :return: True si ya ha sonado en esta ráfaga.
        """
        if ya_sonado and not C.SONIDO_CADA_DISPARO:
            return True
        audio = self.ruta_audio(C.AUDIO_DISPARO)
        if audio is not None:
            return self.senales.audio(audio) or ya_sonado
        if ya_sonado:
            return True
        if self.senales.ocupado():
            return False
        self.senales.sonido('disparo')
        return True

    def seguir_y_disparar(self, parada, angulo, confianza, ya_atacados=(), distancia=None):
        """Fija el robot visto en `angulo`, lo sigue con la torreta y le dispara solo cuando está centrado.

        Cada imagen se analiza en cuanto llega (sin esperas). Se elige la detección más
        cercana a donde se espera el robot, contando con lo que se ha movido, y se gira la
        torreta a una velocidad proporcional al error más la velocidad estimada del robot.
        La torreta sigue girando mientras se analiza la imagen siguiente, así que la ganancia
        se limita a CORRECCION_POR_IMAGEN / (tiempo medido por imagen): en cada imagen se
        corrige como mucho esa fracción del error, también con CPU (más de 1 s por imagen).
        Por lo mismo, el tiempo máximo con un robot crece si cada imagen tarda mucho.
        Se dispara cuando el error es menor que la tolerancia (que crece con el tamaño de
        la caja) y han pasado INTERVALO_DISPARO s desde el anterior, hasta DISPAROS_POR_ROBOT.
        Con ANTICIPAR no se dispara hasta haberlo visto en dos imágenes: con una sola aún no
        se conoce su velocidad y, si se mueve, el disparo sale detrás de él.

        Para fijarlo hace falta confianza >= UMBRAL, que no sea un robot ya atacado (en la
        parada, `ya_atacados`, o en la memoria del circuito) y que esté a menos de SALTO_MAX
        de donde se vio; después basta con UMBRAL_SEGUIMIENTO. Si no se ve en PERDIDAS_MAX
        imágenes seguidas, se da por perdido. Al completar la ráfaga, el robot se anota en la
        memoria; si no se llega a fijar, se anota como descarte durante TIEMPO_DESCARTE s.
        :return: ángulo final del robot si se ha completado la ráfaga (o, con --sin-disparar,
                 si se habría completado); None si no se ha fijado o se ha perdido antes.
        """
        self.senales.estado('apuntando')
        self.senales.sonido('detectado')
        self.torreta.ir(angulo)
        inicio = self.reloj()
        objetivo, t_objetivo = angulo, None   # último ángulo visto del robot (respecto al chasis) y cuándo
        velocidad = 0.0                       # velocidad angular estimada del robot (º/s)
        fijado, centrados, disparos, perdidas, imagenes, vistas = False, 0, 0, 0, 0, 0
        ultimo_disparo, sonado, motivo = None, False, 'completado'
        periodo, t_anterior = None, None      # s por imagen (media móvil) e instante de la imagen anterior
        tiempo_max = C.TIEMPO_MAX_OBJETIVO
        try:
            while centrados < C.DISPAROS_POR_ROBOT:
                if self.reloj() - inicio > tiempo_max:
                    motivo = 'tiempo agotado'
                    break
                t_pedida = self.reloj()
                image = self.camara.capturar(0)
                t_captura = self.reloj() - C.RETARDO_CAMARA
                prediction, ms = detectar(self.model, image, C.RESIZE)
                ahora = self.reloj()
                dt = ahora - (t_anterior if t_anterior is not None else t_pedida)
                t_anterior = ahora
                if dt > 0:
                    periodo = dt if periodo is None else 0.5 * periodo + 0.5 * dt
                ganancia = (C.GANANCIA_SEGUIMIENTO if not periodo else
                            min(C.GANANCIA_SEGUIMIENTO, C.CORRECCION_POR_IMAGEN / periodo))
                if periodo:
                    tiempo_max = max(C.TIEMPO_MAX_OBJETIVO, 2 * C.DISPAROS_POR_ROBOT * periodo)
                yaw, pitch = self.torreta.leer()
                yaw_c, pitch_c = self.torreta.angulo_en(t_captura)   # hacia dónde miraba al tomar la imagen
                imagenes += 1
                prevision = objetivo + (velocidad * (t_captura - t_objetivo) if t_objetivo is not None else 0.0)
                candidatos = []
                for caja, score in seleccionar(prediction, C.UMBRAL_SEGUIMIENTO if fijado else C.UMBRAL):
                    a = yaw_c + C.SIGNO_YAW * auto_aim(image, caja)
                    if abs(a - prevision) > C.SALTO_MAX:
                        continue
                    d = distancia_estimada(image, caja, C.ALTURA_ROBOT)
                    if fijado or (es_nuevo(a, ya_atacados, C.TOLERANCIA_YAW) and not self.es_conocido(a, d, ahora)):
                        candidatos.append((abs(a - prevision), a, caja, score, d))
                if not candidatos:
                    perdidas += 1
                    self.torreta.parar()
                    self.registro.imagen(image, prediction, ms, parada, 'seguimiento' if fijado else 'sin_confirmar',
                                         yaw, pitch, disparos=disparos)
                    if perdidas >= C.PERDIDAS_MAX:
                        motivo = 'perdido' if fijado else 'no confirmado'
                        break
                    continue
                _, a, caja, confianza, d = min(candidatos, key=lambda c: c[0])
                distancia = d if d is not None else distancia
                if t_objetivo is not None and t_captura > t_objetivo:
                    v = (a - objetivo) / (t_captura - t_objetivo)
                    velocidad = limitar(0.5 * velocidad + 0.5 * v, VEL_GIMBAL_MAX)
                objetivo, t_objetivo, fijado, perdidas = a, t_captura, True, 0
                vistas += 1

                # Error de puntería ahora (el robot ha seguido moviéndose desde la imagen) y
                # tolerancia según su tamaño aparente
                err_yaw = a + (velocidad * (ahora - t_captura) if C.ANTICIPAR else 0.0) - yaw
                err_pitch = (pitch_c + auto_pitch(image, caja, C.ALTURA_PUNTERIA) - pitch) if C.CORREGIR_PITCH else 0.0
                ancho, alto = tamano_angular(image, caja)
                centrado = (abs(err_yaw) <= max(C.TOLERANCIA_DISPARO, 0.4 * ancho)
                            and abs(err_pitch) <= max(C.TOLERANCIA_DISPARO, 0.4 * alto))
                if (centrado and vistas >= (2 if C.ANTICIPAR else 1)
                        and (ultimo_disparo is None or ahora - ultimo_disparo >= C.INTERVALO_DISPARO)):
                    if not self.args.sin_disparar:
                        if disparos == 0:
                            self.senales.estado('disparando', parpadeo=True)
                        if not self.ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1):
                            self.registro.imagen(image, prediction, ms, parada, 'seguimiento', yaw, pitch,
                                                 objetivo=caja, objetivo_yaw=a, disparos=disparos, distancia=d)
                            self.ataques.append(dict(parada=parada, yaw=round(a, 1), confianza=round(confianza, 3),
                                                     confirmado=True, disparos=disparos, completo=False,
                                                     imagenes=imagenes))
                            raise RuntimeError(f'{parada}: el blaster no confirmó el disparo {disparos + 1} '
                                               f'de {C.DISPAROS_POR_ROBOT} ({disparos} confirmados por el SDK)')
                        disparos += 1
                        sonado = self.sonar_disparo(sonado)
                    centrados += 1
                    ultimo_disparo = ahora
                self.registro.imagen(image, prediction, ms, parada, 'seguimiento', yaw, pitch, objetivo=caja,
                                     objetivo_yaw=a, disparos=disparos, distancia=d)
                if centrados < C.DISPAROS_POR_ROBOT:
                    giro = (velocidad if C.ANTICIPAR else 0.0) + ganancia * err_yaw
                    self.torreta.velocidad(giro, ganancia * err_pitch)
        finally:
            self.torreta.parar()
        completo = centrados >= C.DISPAROS_POR_ROBOT
        duracion = self.reloj() - inicio
        punto = self.en_circuito(objetivo, distancia)
        self.ataques.append(dict(parada=parada, yaw=round(objetivo, 1), confianza=round(confianza, 3),
                                 confirmado=fijado, disparos=disparos, completo=completo, imagenes=imagenes,
                                 segundos=round(duracion, 1), velocidad_robot=round(velocidad, 1),
                                 s_por_imagen=None if periodo is None else round(periodo, 2),
                                 distancia_m=None if distancia is None else round(distancia, 2),
                                 punto=None if punto is None else [round(v, 2) for v in punto]))
        if completo:
            self.memoria.anotar(punto, self.reloj(), distancia, 'atacado', parada)
        elif not fijado:
            self.memoria.anotar(punto, self.reloj(), distancia, 'descartado', parada)
        if not completo:
            print(f'  objetivo en {angulo:+.1f} grados {motivo} tras {disparos} disparos ({imagenes} imágenes)')
            return None
        print(f'  objetivo seguido hasta {objetivo:+.1f} grados (confianza {confianza:.3f}): {disparos} disparos '
              f'en {duracion:.1f} s, {imagenes} imágenes')
        self.celebrar()
        return objetivo

    def apuntar_y_disparar(self, parada, angulo, confianza, ya_atacados=()):
        """Gira hacia un objetivo, confirma que sigue ahí, corrige la puntería y dispara.

        Al confirmar se toma la detección más centrada. Si queda a más de
        TOLERANCIA_YAW del centro, el objetivo previsto no está; si coincide con un
        robot ya atacado en la parada, se dispararía dos veces al mismo. En ambos
        casos no se dispara.
        :return: True si se ha atacado (o, con --sin-disparar, si se habría atacado).
        """
        self.senales.estado('apuntando')
        self.senales.sonido('detectado')
        self.torreta.ir(angulo)
        caja = None
        if C.CONFIRMAR:
            image, prediction, ms = self.mirar()
            yaw_captura = self.torreta.yaw
            objetivos = seleccionar(prediction, C.UMBRAL)
            residuo = None
            if objetivos:
                caja, confianza_conf = mas_centrada(image, objetivos)
                residuo = C.SIGNO_YAW * auto_aim(image, caja)
                if abs(residuo) > C.TOLERANCIA_YAW or not es_nuevo(yaw_captura + residuo, ya_atacados,
                                                                   C.TOLERANCIA_YAW):
                    residuo = None
            if residuo is None:
                self.registro.imagen(image, prediction, ms, parada, 'sin_confirmar', yaw_captura, self.torreta.pitch)
                print(f'  objetivo en {angulo:+.1f} grados no confirmado: no se dispara')
                self.ataques.append(dict(parada=parada, yaw=round(angulo, 1), confianza=round(confianza, 3),
                                         confirmado=False, disparos=0))
                return False
            confianza = confianza_conf
            self.torreta.ir(yaw_captura + residuo)
        disparos = 0
        if not self.args.sin_disparar:
            self.senales.estado('disparando', parpadeo=True)
            disparos = self.rafaga()
        if C.CONFIRMAR:
            self.registro.imagen(image, prediction, ms, parada, 'confirmado', yaw_captura, self.torreta.pitch,
                                 objetivo=caja, objetivo_yaw=self.torreta.yaw, disparos=disparos)
        self.ataques.append(dict(parada=parada, yaw=round(self.torreta.yaw, 1), confianza=round(confianza, 3),
                                 confirmado=C.CONFIRMAR, disparos=disparos))
        if not self.args.sin_disparar and disparos < C.DISPAROS_POR_ROBOT:
            raise RuntimeError(f'{parada}: el blaster no confirmó el disparo {disparos + 1} '
                               f'de {C.DISPAROS_POR_ROBOT} ({disparos} confirmados por el SDK)')
        print(f'  objetivo en {self.torreta.yaw:+.1f} grados (confianza {confianza:.3f}): {disparos} disparos')
        self.celebrar()
        return True

    def celebrar(self):
        """Gesto corto tras inutilizar un robot: LED verde y cabeceo del gimbal."""
        self.senales.estado('hecho')
        self.senales.sonido('hecho')
        pitch = self.torreta.pitch
        self.torreta.ir(self.torreta.yaw, pitch + 10)
        self.torreta.ir(self.torreta.yaw, pitch)

    def analizar_barrido(self, nombre, image, prediction, ms, yaw_c, pitch_c, revisados, atacados):
        """Busca robots nuevos en una imagen del barrido, la guarda y ataca a cada uno.

        Un robot es nuevo si supera UMBRAL, no está a menos de TOLERANCIA_YAW de uno ya
        revisado en esta parada y no coincide con uno de la memoria del circuito.
        `yaw_c` y `pitch_c` son los ángulos de la torreta al tomar la imagen.
        :return: número de robots nuevos en la imagen.
        """
        ahora = self.reloj()
        nuevos = []
        for caja, score in seleccionar(prediction, C.UMBRAL):
            angulo = yaw_c + C.SIGNO_YAW * auto_aim(image, caja)
            distancia = distancia_estimada(image, caja, C.ALTURA_ROBOT)
            if (es_nuevo(angulo, revisados + [a for _, _, a, _ in nuevos], C.TOLERANCIA_YAW)
                    and not self.es_conocido(angulo, distancia, ahora)):
                nuevos.append((caja, score, angulo, distancia))
        if not C.DISPARAR_A_TODOS:
            nuevos = nuevos[:1]
        self.registro.imagen(image, prediction, ms, nombre, 'barrido', yaw_c, pitch_c,
                             objetivo=nuevos[0][0] if nuevos else None,
                             objetivo_yaw=nuevos[0][2] if nuevos else None,
                             distancia=nuevos[0][3] if nuevos else None)
        for _, score, angulo, distancia in nuevos:
            revisados.append(angulo)
            if C.SEGUIMIENTO:
                final = self.seguir_y_disparar(nombre, angulo, score, atacados, distancia)
                if final is not None:
                    atacados.append(final)
                    revisados.append(final)
            elif self.apuntar_y_disparar(nombre, angulo, score, atacados):
                atacados.append(angulo)
                self.memoria.anotar(self.en_circuito(angulo, distancia), self.reloj(), distancia, 'atacado', nombre)
        return len(nuevos)

    def barrer_por_pasos(self, p, revisados, atacados, completa):
        """Barrido parando la torreta en cada ángulo de p['barrido'] (BARRIDO_CONTINUO = False)."""
        for yaw in p['barrido']:
            if completa():
                break
            self.senales.estado('buscando')
            self.torreta.ir(yaw, p.get('pitch', 0))
            image, prediction, ms = self.mirar()
            yaw_c, pitch_c = self.torreta.leer()
            n = self.analizar_barrido(p['nombre'], image, prediction, ms, yaw_c, pitch_c, revisados, atacados)
            print(f'  yaw {yaw:+4.0f}: {n} objetivo(s) nuevo(s), {ms:.0f} ms')

    def barrer_continuo(self, p, revisados, atacados, completa):
        """Barrido girando la torreta sin parar y analizando una imagen cada PASO_BARRIDO grados.

        Recorre los extremos de ruta_barrido(). Cada imagen se sitúa con el ángulo que tenía
        la torreta al tomarla (RETARDO_CAMARA). Si aparece un robot nuevo, se para, se le
        sigue y dispara, y el barrido continúa desde donde haya quedado la torreta.
        """
        pitch = p.get('pitch', 0)
        ruta = ruta_barrido(p['barrido'], C.CAMPO_VISION)
        vel = limitar(C.VEL_BARRIDO, VEL_GIMBAL_MAX)
        self.senales.estado('buscando')
        self.torreta.ir(ruta[0], pitch)
        image, prediction, ms = self.mirar(espera=C.RETARDO_CAMARA)   # primera imagen, con la torreta quieta
        yaw_c, pitch_c = self.torreta.leer()
        self.analizar_barrido(p['nombre'], image, prediction, ms, yaw_c, pitch_c, revisados, atacados)
        ultimo = yaw_c
        print(f'  barrido continuo: {" -> ".join(f"{r:+.0f}" for r in ruta)} grados')
        for destino in ruta[1:]:
            yaw, _ = self.torreta.leer()
            sentido = 1 if destino >= yaw else -1
            limite = self.reloj() + 2 * abs(destino - yaw) / vel + 5
            while not completa():
                yaw, pitch_actual = self.torreta.leer()
                if (destino - yaw) * sentido <= 1.0:
                    break
                if self.reloj() > limite:
                    raise RuntimeError(f'{p["nombre"]}: la torreta no llega a {destino:+.0f} grados en el barrido')
                if abs(pitch_actual - pitch) > 2:              # tras seguir a un robot, recupera el pitch
                    self.torreta.ir(yaw, pitch)
                    self.senales.estado('buscando')
                self.torreta.velocidad(sentido * vel, 0)
                image = self.camara.capturar(0)
                t_captura = self.reloj() - C.RETARDO_CAMARA
                yaw_c, pitch_c = self.torreta.angulo_en(t_captura)
                if abs(yaw_c - ultimo) < C.PASO_BARRIDO:
                    time.sleep(0.02)   # sin analizar: no hace falta leer la cámara sin parar
                    continue
                ultimo = yaw_c
                prediction, ms = detectar(self.model, image, C.RESIZE)
                if self.analizar_barrido(p['nombre'], image, prediction, ms, yaw_c, pitch_c, revisados, atacados):
                    ultimo = self.torreta.leer()[0]
                    limite = self.reloj() + 2 * abs(destino - ultimo) / vel + 5
            self.torreta.parar()
            # Una imagen en el extremo, para no dejar sin mirar el final del tramo
            yaw, _ = self.torreta.leer()
            if not completa() and abs(yaw - ultimo) >= C.PASO_BARRIDO / 2:
                image, prediction, ms = self.mirar(espera=C.RETARDO_CAMARA)
                yaw_c, pitch_c = self.torreta.leer()
                ultimo = yaw_c
                self.analizar_barrido(p['nombre'], image, prediction, ms, yaw_c, pitch_c, revisados, atacados)

    def atacar_parada(self, p):
        """Barre la parada con el gimbal y ataca a cada robot nuevo que supere el umbral."""
        nombre, esperados = p['nombre'], p.get('objetivos')
        print(f'[{nombre}] buscando (esperados: {esperados if esperados is not None else "?"})')
        self.senales.estado('buscando')
        self.senales.sonido('buscando')
        self.torreta.centrar()
        revisados, atacados = [], []
        inicio = self.reloj()

        def completa():
            return esperados is not None and len(atacados) >= esperados and not C.BARRIDO_COMPLETO

        if C.BARRIDO_CONTINUO and C.SEGUIMIENTO:
            self.barrer_continuo(p, revisados, atacados, completa)
        else:
            self.barrer_por_pasos(p, revisados, atacados, completa)
        if not atacados:
            self.senales.estado('nada')
        self.torreta.centrar()
        self.paradas_hechas.append(dict(nombre=nombre, esperados=esperados, atacados=len(atacados),
                                        yaw_atacados=[round(a, 1) for a in atacados],
                                        imagenes=sum(f['parada'] == nombre for f in self.registro.filas),
                                        segundos=round(self.reloj() - inicio, 1),
                                        pose=[round(v, 2) for v in self.pose]))

    def ruta_audio(self, relativa):
        """Ruta absoluta de un audio de circuito.py, o None si no está configurado o no existe."""
        if not relativa:
            return None
        ruta = os.path.join(AQUI, relativa)
        if os.path.isfile(ruta):
            return ruta
        if relativa not in self.audios_avisados:
            self.audios_avisados.add(relativa)
            print(f'[aviso] no existe {relativa}: se usan los sonidos del SDK (ver audio/convertir_audio.py)')
        return None

    def rafaga(self):
        """Ráfaga sin seguimiento (SEGUIMIENTO = False). Devuelve cuántas órdenes de disparo confirmó el SDK.

        Con SONIDO_CADA_DISPARO (por defecto, como en main) espera al audio de cada disparo;
        sin él suena una vez y dispara cada INTERVALO_DISPARO s.
        """
        rafaga = self.ruta_audio(getattr(C, 'AUDIO_RAFAGA', None))
        if rafaga is not None:
            self.senales.esperar_sonido(8)  # deja acabar el motor o el aviso de detección
            if self.senales.audio(rafaga):
                return self.disparar_al_ritmo()
        audio = self.ruta_audio(C.AUDIO_DISPARO)
        por_disparo = audio is not None and C.SONIDO_CADA_DISPARO
        if por_disparo:
            self.senales.esperar_sonido(8)
        sonado = False
        for confirmados in range(C.DISPAROS_POR_ROBOT):
            if not self.ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1):
                return confirmados
            if por_disparo and self.senales.audio(audio):
                inicio = time.monotonic()
                self.senales.esperar_sonido(C.ESPERA_AUDIO_DISPARO)
                time.sleep(max(0.0, C.INTERVALO_DISPARO - (time.monotonic() - inicio)))
            else:
                sonado = self.sonar_disparo(sonado)
                time.sleep(C.INTERVALO_DISPARO)
        return C.DISPAROS_POR_ROBOT

    def disparar_al_ritmo(self):
        """Dispara DISPAROS_POR_ROBOT veces al ritmo de AUDIO_RAFAGA, que ya está sonando.

        Cada disparo va en su instante (silencio inicial + i * INTERVALO_DISPARO desde que
        empieza el audio), así el tiempo que tarda fire() no retrasa los siguientes.
        :return: órdenes de disparo confirmadas por el SDK.
        """
        inicio = time.monotonic() + C.SILENCIO_AUDIO_DISPARO
        for confirmados in range(C.DISPAROS_POR_ROBOT):
            time.sleep(max(0.0, inicio + confirmados * C.INTERVALO_DISPARO - time.monotonic()))
            if not self.ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1):
                return confirmados
        self.senales.esperar_sonido(2)   # deja acabar el último disparo del audio
        return C.DISPAROS_POR_ROBOT

    def luces_fiesta(self, parar):
        """Cambia el color de los LED LED_FIESTA_HZ veces por segundo hasta que se active `parar`."""
        colores = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255),
                   (255, 0, 255)]
        i = 0
        while not parar.is_set():
            r, g, b = colores[i % len(colores)]
            try:
                self.ep_robot.led.set_led(comp=led.COMP_ALL, r=r, g=g, b=b, effect=led.EFFECT_ON)
            except Exception:
                pass
            i += 1
            parar.wait(1.0 / C.LED_FIESTA_HZ)

    def baile(self):
        """Baile final con la canción de AUDIO_FINAL y los LED cambiando de color muy rápido."""
        print('Baile final')
        self.senales.esperar_sonido(5)
        cancion = self.ruta_audio(C.AUDIO_FINAL)
        if cancion is None or not self.senales.audio(cancion):
            self.senales.sonido('hecho')
        parar = threading.Event()
        luces = threading.Thread(target=self.luces_fiesta, args=(parar,), daemon=True)
        luces.start()
        try:
            for _ in range(4):
                self.torreta.ir(20, 10)
                self.torreta.ir(-20, -5)
            self.torreta.ir(0, 0)
            if not self.args.sin_mover:
                for z in (20, -40, 20):
                    self.mover(0, 0, z)
            # Las luces siguen mientras suena la canción
            fin = time.time() + C.DURACION_FIESTA_MAX
            while self.senales.ocupado() and time.time() < fin:
                parar.wait(0.1)
        finally:
            parar.set()
            luces.join(timeout=1)
        self.senales.estado('fin')

    # --- demo completa ----------------------------------------------------------
    def ejecutar(self):
        elegidas = [n.strip() for n in self.args.paradas.split(',') if n.strip()]
        nombres = [p['nombre'] for p in C.PARADAS]
        for n in elegidas:
            assert n in nombres, f'La parada {n} no existe en circuito.py ({nombres})'
        ultima = max(nombres.index(n) for n in elegidas) if elegidas else len(C.PARADAS) - 1
        recorrido = []
        try:
            try:
                self.ep_robot.set_robot_mode(mode=robot.FREE)  # gimbal y chasis independientes
            except Exception as e:
                print(f'[aviso] modo del robot: {e}')
            bateria = nivel_bateria(self.ep_robot)
            print(f'Batería: {bateria}%')
            if bateria is not None and bateria < C.BATERIA_CRITICA:
                raise RuntimeError(f'batería al {bateria}%: con menos del {C.BATERIA_CRITICA}% el robot no '
                                   'responde. Cárguela antes de seguir')
            if bateria is not None and bateria < C.BATERIA_MINIMA:
                print(f'[aviso] batería por debajo del {C.BATERIA_MINIMA}%: cárguela antes de la demo')
            self.camara = Camara(self.ep_robot, espera=C.ESPERA_CAMARA)
            if C.LEER_ANGULO_GIMBAL:
                print(f'Torreta: {self.torreta.comprobar_lectura()}')
            self.torreta.centrar()
            self.senales.estado('moviendo', parpadeo=True)
            self.senales.sonido('inicio')
            self.senales.esperar_sonido(8)  # el SDK no admite dos sonidos a la vez
            if C.AUDIO_MOTOR:
                self.senales.audio(os.path.join(AQUI, C.AUDIO_MOTOR))

            for p in C.PARADAS[:ultima + 1]:
                print(f'[{p["nombre"]}] desplazamiento')
                self.senales.estado('moviendo')
                for x, y, z in p['movimientos']:
                    self.recorrer(p['nombre'] + '-ruta', x, y, z)
                    recorrido.append((x, y, z))
                if C.ROBOTS_TOTALES is not None and len(self.memoria.atacados()) >= C.ROBOTS_TOTALES:
                    print(f'[{p["nombre"]}] ya se han atacado los {C.ROBOTS_TOTALES} robots: no se barre')
                elif not elegidas or p['nombre'] in elegidas:
                    self.atacar_parada(p)

            if C.VOLVER_AL_INICIO:
                print('Vuelta al inicio')
                self.senales.estado('moviendo')
                for x, y, z in reversed(recorrido):
                    self.mover(-x, -y, -z)
            if C.BAILE_FINAL:
                self.baile()
        finally:
            self.cerrar()

    def cerrar(self):
        """Deja el robot quieto y seguro pase lo que pase (también con Ctrl+C o un error)."""
        pasos = [
            ('chasis', lambda: self.ep_robot.chassis.drive_speed(x=0, y=0, z=0)),
            ('gimbal', self.torreta.centrar),
            ('lectura del gimbal', self.torreta.cancelar_lectura),
            ('camara', lambda: self.camara and self.camara.cerrar()),
            ('led', lambda: self.senales.estado('apagado')),
        ]
        for nombre, paso in pasos:
            try:
                paso()
            except BaseException as e:
                print(f'[aviso] al cerrar {nombre}: {e!r}')
        filas = self.registro.filas
        resumen = dict(
            fecha=time.strftime('%Y-%m-%d %H:%M:%S'), duracion_s=round(time.time() - self.inicio, 1),
            modelo=C.MODELO, ruta_modelo=C.RUTA_MODELO, umbral=C.UMBRAL, resize=C.RESIZE,
            opciones=dict(sin_disparar=self.args.sin_disparar, sin_mover=self.args.sin_mover,
                          paradas=self.args.paradas, simulacion=self.args.simulacion),
            estrategia=dict(disparar_a_todos=C.DISPARAR_A_TODOS, barrido_completo=C.BARRIDO_COMPLETO,
                            confirmar=C.CONFIRMAR, disparos_por_robot=C.DISPAROS_POR_ROBOT,
                            tolerancia_yaw=C.TOLERANCIA_YAW, seguimiento=C.SEGUIMIENTO,
                            umbral_seguimiento=C.UMBRAL_SEGUIMIENTO, salto_max=C.SALTO_MAX,
                            tolerancia_disparo=C.TOLERANCIA_DISPARO, intervalo_disparo=C.INTERVALO_DISPARO,
                            ganancia=C.GANANCIA_SEGUIMIENTO, correccion_por_imagen=C.CORRECCION_POR_IMAGEN,
                            anticipar=C.ANTICIPAR, sonido_cada_disparo=C.SONIDO_CADA_DISPARO,
                            corregir_pitch=C.CORREGIR_PITCH,
                            lectura_gimbal=self.torreta.usar_medida, barrido_continuo=C.BARRIDO_CONTINUO,
                            paso_barrido=C.PASO_BARRIDO, campo_vision=C.CAMPO_VISION,
                            memoria=C.MEMORIA, altura_robot=C.ALTURA_ROBOT, radio_mismo_robot=C.RADIO_MISMO_ROBOT,
                            error_distancia=C.ERROR_DISTANCIA, robots_totales=C.ROBOTS_TOTALES,
                            vigilancia=C.VIGILANCIA, tramo_vigilancia=C.TRAMO_VIGILANCIA,
                            atacar_en_ruta=C.ATACAR_EN_RUTA, ancho_pasillo=C.ANCHO_PASILLO,
                            distancia_seguridad=C.DISTANCIA_SEGURIDAD,
                            detener_si_bloqueado=C.DETENER_SI_BLOQUEADO),
            imagenes=len(filas),
            ms_inferencia_medio=round(sum(f['ms_inferencia'] for f in filas) / len(filas), 1) if filas else None,
            disparos=sum(a['disparos'] for a in self.ataques),
            paradas=self.paradas_hechas, ataques=self.ataques, circuito=C.PARADAS,
            memoria=self.memoria.entradas, pose_final=[round(v, 2) for v in self.pose],
            eventos_ruta=self.eventos_ruta,
        )
        self.registro.cerrar(resumen)
        print(f'Evidencias en {self.registro.carpeta}: {len(filas)} imágenes, {resumen["disparos"]} disparos')
        return resumen


def main(argv=None):
    args = argumentos(argv)
    C.MODELO = args.arquitectura or C.MODELO
    C.RUTA_MODELO = args.modelo or C.RUTA_MODELO
    if args.umbral is not None:
        C.UMBRAL = args.umbral
    model, device, _ = cargar_modelo(C.MODELO, C.RUTA_MODELO, use_gpu=C.USAR_GPU)
    print(f'Modelo {C.MODELO} en {device}; primera inferencia: {calentar(model, C.RESIZE):.0f} ms')
    # El robot simulado no necesita serial_number.txt
    try:
        if args.simulacion:
            ep_robot = connect('wifi')
        elif args.conexion == 'auto':
            ep_robot = connect('networking')
        else:
            ep_robot = connect(args.conexion, auto=False)
    except ConnectionError as e:
        print(f'[error] {e}')
        return None
    demo = None
    try:
        demo = Demo(ep_robot, model, args)
        demo.ejecutar()
    except KeyboardInterrupt:
        print('Demo detenida con Ctrl+C: robot parado y gimbal centrado')
    except RuntimeError as e:
        print(f'[error] demo detenida: {e}')
    finally:
        ep_robot.close()
    return demo


if __name__ == '__main__':
    main()
