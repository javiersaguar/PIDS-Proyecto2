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
    ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1)

    return image, prediction


class Torreta:
    """Gimbal con su ángulo llevado por software.

    Al llegar a cada parada se centra (queda alineado con el chasis) y desde
    ahí se mueve con giros relativos, así el yaw de cada imagen es conocido.
    """

    YAW_MAX = 240  # el gimbal admite unos ±250º

    def __init__(self, ep_robot):
        self.ep_robot = ep_robot
        self.gimbal = ep_robot.gimbal
        self.yaw = 0.0
        self.pitch = 0.0

    def centrar(self):
        ejecutar_accion(self.ep_robot, lambda: self.gimbal.recenter(pitch_speed=VEL_GIMBAL_MAX,
                                                                    yaw_speed=VEL_GIMBAL_MAX),
                        timeout=20, que='gimbal (centrar)')
        self.yaw = self.pitch = 0.0

    def ir(self, yaw, pitch=None):
        yaw = max(-self.YAW_MAX, min(self.YAW_MAX, yaw))
        pitch = self.pitch if pitch is None else pitch
        d_yaw, d_pitch = yaw - self.yaw, pitch - self.pitch
        if abs(d_yaw) > 0.5 or abs(d_pitch) > 0.5:
            tiempo = max(abs(d_yaw), abs(d_pitch)) / VEL_GIMBAL_MAX
            ejecutar_accion(self.ep_robot, lambda: self.gimbal.move(pitch=d_pitch, yaw=d_yaw, pitch_speed=VEL_GIMBAL_MAX,
                                                                    yaw_speed=VEL_GIMBAL_MAX),
                            timeout=2 * tiempo + 5, que='gimbal')
        self.yaw, self.pitch = yaw, pitch


class Demo:
    def __init__(self, ep_robot, model, args):
        self.ep_robot = ep_robot
        self.model = model
        self.args = args
        self.torreta = Torreta(ep_robot)
        self.senales = Senales(ep_robot, C.SONIDOS)
        self.registro = Registro(args.evidencias, umbral=C.UMBRAL, mostrar=getattr(args, 'ver', False))
        self.camara = None
        self.ataques = []
        self.paradas_hechas = []
        self.audios_avisados = set()
        self.inicio = time.time()

    # --- piezas ---------------------------------------------------------------
    def mover(self, x, y, z):
        """Mueve el chasis (x adelante, y derecha, z giro a la izquierda) sin pasar de la velocidad del SDK."""
        print(f'  chasis: x={x:+.2f} m  y={y:+.2f} m  z={z:+.0f} grados')
        if self.args.sin_mover:
            return
        v_xy, v_z = limitar(C.VELOCIDAD_XY, VEL_XY_MAX), limitar(C.VELOCIDAD_Z, VEL_Z_MAX)
        tiempo = (x * x + y * y) ** 0.5 / v_xy + abs(z) / v_z
        ejecutar_accion(self.ep_robot, lambda: self.ep_robot.chassis.move(x=x, y=y, z=z, xy_speed=v_xy, z_speed=v_z),
                        timeout=2 * tiempo + 5, que='chasis')

    def mirar(self):
        """Captura con el gimbal quieto y aplica el detector: (imagen, predicción, ms)."""
        image = self.camara.capturar()
        prediction, ms = detectar(self.model, image, C.RESIZE)
        return image, prediction, ms

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
        print(f'  objetivo en {self.torreta.yaw:+.1f} grados (confianza {confianza:.3f}): {disparos} disparos')
        self.ataques.append(dict(parada=parada, yaw=round(self.torreta.yaw, 1), confianza=round(confianza, 3),
                                 confirmado=C.CONFIRMAR, disparos=disparos))
        self.celebrar()
        return True

    def celebrar(self):
        """Gesto corto tras inutilizar un robot: LED verde y cabeceo del gimbal."""
        self.senales.estado('hecho')
        self.senales.sonido('hecho')
        pitch = self.torreta.pitch
        self.torreta.ir(self.torreta.yaw, pitch + 10)
        self.torreta.ir(self.torreta.yaw, pitch)

    def atacar_parada(self, p):
        """Barre la parada con el gimbal y ataca a cada robot nuevo que supere el umbral."""
        nombre, esperados = p['nombre'], p.get('objetivos')
        print(f'[{nombre}] buscando (esperados: {esperados if esperados is not None else "?"})')
        self.senales.estado('buscando')
        self.senales.sonido('buscando')
        self.torreta.centrar()
        revisados, atacados = [], []
        for yaw in p['barrido']:
            if esperados is not None and len(atacados) >= esperados and not C.BARRIDO_COMPLETO:
                break
            self.senales.estado('buscando')
            self.torreta.ir(yaw, p.get('pitch', 0))
            image, prediction, ms = self.mirar()
            nuevos = []
            for caja, score in seleccionar(prediction, C.UMBRAL):
                angulo = self.torreta.yaw + C.SIGNO_YAW * auto_aim(image, caja)
                if es_nuevo(angulo, revisados + [a for _, _, a in nuevos], C.TOLERANCIA_YAW):
                    nuevos.append((caja, score, angulo))
            if not C.DISPARAR_A_TODOS:
                nuevos = nuevos[:1]
            self.registro.imagen(image, prediction, ms, nombre, 'barrido', self.torreta.yaw, self.torreta.pitch,
                                 objetivo=nuevos[0][0] if nuevos else None,
                                 objetivo_yaw=nuevos[0][2] if nuevos else None)
            print(f'  yaw {yaw:+4.0f}: {len(nuevos)} objetivo(s) nuevo(s), {ms:.0f} ms')
            for _, score, angulo in nuevos:
                revisados.append(angulo)
                if self.apuntar_y_disparar(nombre, angulo, score, atacados):
                    atacados.append(angulo)
        if not atacados:
            self.senales.estado('nada')
        self.torreta.centrar()
        self.paradas_hechas.append(dict(nombre=nombre, esperados=esperados, atacados=len(atacados),
                                        yaw_atacados=[round(a, 1) for a in atacados],
                                        imagenes=sum(f['parada'] == nombre for f in self.registro.filas)))

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
        """Dispara DISPAROS_POR_ROBOT veces; con AUDIO_DISPARO, cada disparo suena con ese audio."""
        audio = self.ruta_audio(C.AUDIO_DISPARO)
        if audio is None:
            self.senales.sonido('disparo')
        for _ in range(C.DISPAROS_POR_ROBOT):
            self.ep_robot.blaster.fire(fire_type=blaster.INFRARED_FIRE, times=1)
            if audio is not None and self.senales.audio(audio):
                self.senales.esperar_sonido(C.ESPERA_AUDIO_DISPARO)
            else:
                time.sleep(0.3)
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
                    self.mover(x, y, z)
                    recorrido.append((x, y, z))
                if not elegidas or p['nombre'] in elegidas:
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
                            tolerancia_yaw=C.TOLERANCIA_YAW),
            imagenes=len(filas),
            ms_inferencia_medio=round(sum(f['ms_inferencia'] for f in filas) / len(filas), 1) if filas else None,
            disparos=sum(a['disparos'] for a in self.ataques),
            paradas=self.paradas_hechas, ataques=self.ataques, circuito=C.PARADAS,
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
        ep_robot = connect('wifi' if args.simulacion else 'networking')
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
