"""Mueve el robot rival 2 despacio y en línea recta, en paralelo a nuestro robot en la rotonda.

Lo lanza Alejandro en su portátil, conectado al robot RIVAL (no al nuestro). El robot
espera quieto hasta recibir el aviso de la demo (UDP por la red del laboratorio) o hasta
que se pulse Enter; entonces avanza 0,65 m y retrocede otros 0,65 m a 0,05 m/s.
`--distancia` cambia la distancia de cada tramo y `--velocidad`, su velocidad.
Se conserva la misma recta y orientación del chasis en la ida y en la vuelta,
corrigiendo el desplazamiento lateral y el rumbo con la odometría y la IMU.

    python rival/rival_movil.py                       # espera el aviso o Enter y hace la ida y vuelta de 0,65 m
    python rival/rival_movil.py --modo enter          # solo con Enter
    python rival/rival_movil.py --conexion wifi --modo enter --diagnostico  # mide deriva lateral y giro
    python rival/rival_movil.py --sin-robot           # prueba de red: espera el aviso sin conectar el robot
    python rival/rival_movil.py --enviar 192.168.1.23 # (en NUESTRO portátil) envía un aviso de prueba

La conexión sale de rival/config_rival.json (copia de config_rival.ejemplo.json, que no
se sube a GitHub). Instrucciones completas en rival/README.md.

Seguridad: nunca pasa de 0,1 m/s, el robot se para solo si el script deja de mandar
órdenes (0,5 s) y Ctrl+C lo para en cualquier momento.
"""

import argparse
import json
import math
import os
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import aviso  # noqa: E402

VELOCIDAD_MAX = 0.1          # m/s: el rival siempre va muy despacio
EDAD_MAX_POSICION = 1.0     # s sin odometría nueva antes de detener el movimiento
GANANCIA_POSICION = 1.5    # velocidad de corrección por metro de error
GANANCIA_RUMBO = 1.5       # grados/s de corrección por grado de error
CORRECCION_LATERAL_MAX = 0.03  # m/s
CORRECCION_GIRO_MAX = 5.0      # grados/s
TOLERANCIA_POSICION = 0.01    # m al punto de destino
TOLERANCIA_RUMBO = 1.0        # grados respecto al rumbo inicial
CONFIG = os.path.join(AQUI, 'config_rival.json')


def argumentos(argv=None):
    p = argparse.ArgumentParser(description='Robot rival en movimiento para la demo del grupo 2')
    p.add_argument('--distancia', type=float, default=0.65,
                   help='m de ida; vuelve la misma distancia (negativo: primero hacia atrás). Por defecto 0,65')
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
    p.add_argument('--diagnostico', action='store_true',
                   help='mostrar avance, error lateral y error de rumbo respecto a la recta inicial')
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


def diferencia_angular(actual, referencia):
    """Error de rumbo en grados, también al pasar de +180 a -180."""
    return (actual - referencia + 180) % 360 - 180


def limitar_velocidad(vx, vy, maxima):
    """Limita el módulo tras redondear a los 0,01 m/s que transmite el SDK."""
    norma = math.hypot(vx, vy)
    if norma > maxima:
        vx, vy = vx * maxima / norma, vy * maxima / norma
    vx, vy = round(vx, 2), round(vy, 2)
    while math.hypot(vx, vy) > maxima + 1e-9:
        if abs(vx) >= abs(vy):
            vx = round(vx - math.copysign(0.01, vx), 2)
        else:
            vy = round(vy - math.copysign(0.01, vy), 2)
    return vx, vy


class ControlRecta:
    """Referencia única de posición y rumbo para toda la ida y vuelta.

    Los puntos se expresan en los ejes fijos de odometría (cs=1). Las velocidades
    se transforman a los ejes actuales del chasis: x hacia A e y hacia su derecha.
    La vuelta mantiene el mismo yaw; B va por delante sin girar el robot 180°.
    """

    def __init__(self, chassis):
        self.chassis = chassis
        self.posicion = self.actitud = None
        self.sub_posicion = self.sub_actitud = False

    def _posicion(self, info):
        self.posicion = (float(info[0]), float(info[1]), time.monotonic())

    def _actitud(self, info):
        self.actitud = (float(info[0]), time.monotonic())

    def __enter__(self):
        try:
            self.sub_posicion = self.chassis.sub_position(cs=1, freq=20, callback=self._posicion) is not False
            self.sub_actitud = self.chassis.sub_attitude(freq=20, callback=self._actitud) is not False
            if not self.sub_posicion or not self.sub_actitud:
                raise RuntimeError('no se pudieron suscribir la posición y el rumbo del chasis')
            limite = time.monotonic() + 2.0
            while (self.posicion is None or self.actitud is None) and time.monotonic() < limite:
                time.sleep(0.05)
            x, y, yaw = self.leer()
            self.origen = (x, y)
            self.rumbo = yaw
            r = math.radians(yaw)
            self.eje = (math.cos(r), math.sin(r))
            print(f'Control de recta activo: rumbo {yaw:+.2f} grados; misma referencia en ida y vuelta')
            return self
        except BaseException:
            self.cerrar()
            raise

    def __exit__(self, *exc):
        self.cerrar()

    def cerrar(self):
        for activa, nombre in ((self.sub_posicion, 'unsub_position'), (self.sub_actitud, 'unsub_attitude')):
            if activa:
                try:
                    getattr(self.chassis, nombre)()
                except Exception:
                    pass
        self.sub_posicion = self.sub_actitud = False

    def leer(self):
        posicion, actitud = self.posicion, self.actitud
        if posicion is None or actitud is None:
            raise RuntimeError('faltan lecturas de posición o rumbo; no se inicia el movimiento')
        x, y, t_pos = posicion
        yaw, t_yaw = actitud
        if not all(math.isfinite(v) for v in (x, y, yaw)):
            raise RuntimeError('lectura de posición o rumbo no válida')
        ahora = time.monotonic()
        if ahora - t_pos > EDAD_MAX_POSICION or ahora - t_yaw > EDAD_MAX_POSICION:
            raise RuntimeError('la posición o el rumbo llevan más de 1 s sin actualizarse; se detiene el robot')
        return x, y, yaw

    def coordenadas(self, x, y, yaw):
        dx, dy = x - self.origen[0], y - self.origen[1]
        ux, uy = self.eje
        avance = dx * ux + dy * uy
        lateral = -dx * uy + dy * ux
        return avance, lateral, diferencia_angular(yaw, self.rumbo)

    def informar(self, destino):
        x, y, yaw = self.leer()
        avance, lateral, giro = self.coordenadas(x, y, yaw)
        ahora = time.monotonic()
        print(f'[diagnostico] avance={avance:+.3f} m | objetivo={destino:+.3f} m | '
              f'lateral={100 * lateral:+.1f} cm | giro={giro:+.2f} grados | '
              f'edad posicion={max(0.0, ahora - self.posicion[2]):.2f} s | '
              f'edad giro={max(0.0, ahora - self.actitud[1]):.2f} s', flush=True)

    def mover_a(self, destino, velocidad, diagnostico=False):
        x0, y0, yaw = self.leer()
        avance, _, _ = self.coordenadas(x0, y0, yaw)
        inicio = time.monotonic()
        limite = inicio + 2 * abs(destino - avance) / velocidad + 5
        proximo_informe = inicio
        try:
            while True:
                x, y, yaw = self.leer()
                avance, lateral, giro = self.coordenadas(x, y, yaw)
                error = destino - avance
                ahora = time.monotonic()
                if diagnostico and ahora >= proximo_informe:
                    self.informar(destino)
                    proximo_informe = ahora + 1.0
                if math.hypot(error, lateral) <= TOLERANCIA_POSICION and abs(giro) <= TOLERANCIA_RUMBO:
                    break
                if abs(lateral) > 0.12 or abs(giro) > 15:
                    raise RuntimeError('el chasis se separa demasiado de la recta o del rumbo; se detiene')
                if ahora > limite:
                    raise RuntimeError(f'no ha llegado a tiempo: error longitudinal {error:+.3f} m, '
                                       f'lateral {lateral:+.3f} m y giro {giro:+.2f} grados')

                longitudinal = math.copysign(min(velocidad, max(0.01, GANANCIA_POSICION * abs(error))), error)
                if abs(error) < 0.003:
                    longitudinal = 0.0
                transversal = max(-CORRECCION_LATERAL_MAX,
                                  min(CORRECCION_LATERAL_MAX, -GANANCIA_POSICION * lateral))
                # Velocidad deseada sobre la recta fija -> ejes globales -> ejes actuales del chasis.
                ux, uy = self.eje
                global_x = longitudinal * ux - transversal * uy
                global_y = longitudinal * uy + transversal * ux
                r = math.radians(yaw)
                vx = global_x * math.cos(r) + global_y * math.sin(r)
                vy = -global_x * math.sin(r) + global_y * math.cos(r)
                vx, vy = limitar_velocidad(vx, vy, velocidad)
                # El error de rumbo no cambia de signo por ir marcha atrás.
                vz = round(max(-CORRECCION_GIRO_MAX, min(CORRECCION_GIRO_MAX, -GANANCIA_RUMBO * giro)))
                # Es un mensaje PUSH sin ACK: el SDK puede devolver False aunque lo haya enviado.
                # El avance se comprueba con los sensores y con los tiempos máximos.
                self.chassis.drive_speed(x=vx, y=vy, z=vz, timeout=0.5)
                time.sleep(0.05)
        finally:
            self.chassis.drive_speed(x=0, y=0, z=0)
            time.sleep(0.3)
            if diagnostico:
                print('[diagnostico] Final del tramo:')
                try:
                    self.informar(destino)
                except RuntimeError as e:
                    print(f'[diagnostico] {e}')
        x, y, _ = self.leer()
        return math.hypot(x - x0, y - y0), time.monotonic() - inicio


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
    if not math.isfinite(args.velocidad) or not math.isfinite(args.distancia):
        raise SystemExit('La velocidad y la distancia deben ser números finitos')
    if velocidad != abs(args.velocidad):
        print(f'[aviso] velocidad limitada a {VELOCIDAD_MAX} m/s')
    if velocidad <= 0:
        raise SystemExit('La velocidad tiene que ser mayor que 0')
    if velocidad < 0.01:
        raise SystemExit('El SDK necesita al menos 0,01 m/s para representar la velocidad')
    print(f'Movimiento: ida de {args.distancia:+.2f} m y vuelta de {-args.distancia:+.2f} m '
          f'a {velocidad:.2f} m/s (unos {2 * abs(args.distancia) / velocidad:.0f} s en movimiento)')

    if args.sin_robot:
        motivo = esperar_salida(args, puerto)
        print(f'Salida por {motivo}. Prueba sin robot: no se mueve nada.')
        return 0

    conexion = args.conexion or config.get('conexion', 'networking')
    ep_robot = conectar(config, conexion)
    try:
        if ep_robot.set_robot_mode(mode='free') is False:
            raise RuntimeError('no se pudo establecer el modo libre del robot')
        if args.diagnostico:
            try:
                print(f'[diagnostico] Modo del robot: {ep_robot.get_robot_mode()}')
            except Exception as e:
                print(f'[diagnostico] No se pudo consultar el modo del robot: {e!r}')
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
        print(f'Salida por {motivo}: empieza la ida y vuelta...')
        with ControlRecta(ep_robot.chassis) as control:
            for nombre, destino in (('Ida', args.distancia), ('Vuelta', 0.0)):
                print(f'{nombre}: destino {destino:+.2f} m sobre la recta inicial, a {velocidad:.2f} m/s')
                hecho, tiempo = control.mover_a(destino, velocidad, diagnostico=args.diagnostico)
                print(f'{nombre}: recorridos {hecho:.2f} m en {tiempo:.1f} s')
    except KeyboardInterrupt:
        print('Detenido con Ctrl+C')
    except RuntimeError as e:
        print(f'[aviso] Recorrido cancelado: {e}')
        return 1
    finally:
        try:
            ep_robot.chassis.drive_speed(x=0, y=0, z=0)
        except Exception:
            pass
        ep_robot.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
