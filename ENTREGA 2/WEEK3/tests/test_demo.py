"""Pruebas de demo.py con el robot simulado y un detector falso.

El detector falso "ve" robots colocados en ángulos fijos alrededor de la parada:
devuelve una caja donde caería cada robot según el yaw actual del gimbal. Así se
comprueba la puntería, los 12 disparos, que un robot no se ataca dos veces, las
velocidades y la parada segura con Ctrl+C, sin robot ni pesos del modelo.

    python -m unittest discover -s "ENTREGA 2/WEEK3/tests"
"""

import ast
import glob
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

AQUI = os.path.dirname(os.path.abspath(__file__))
WEEK3 = os.path.dirname(AQUI)
sys.path.insert(0, WEEK3)

import simulacion  # noqa: E402

CARPETA = tempfile.mkdtemp(prefix='sim_')
import cv2  # noqa: E402
cv2.imwrite(os.path.join(CARPETA, 'vacia.jpg'), np.zeros((720, 1280, 3), np.uint8))
simulacion.instalar(CARPETA)

import demo  # noqa: E402
import circuito as C  # noqa: E402


def pixel_de(alpha, ancho=1280):
    """Inversa de auto_aim: columna de la imagen donde se ve un objeto a `alpha` grados."""
    focal = ancho / (2 * np.tan(np.pi / 3))
    return ancho / 2 + focal * np.tan(np.deg2rad(alpha * 120 / 90))


class DetectorFalso(torch.nn.Module):
    def __init__(self, robots, confianza=0.99, retardo=0.0):
        super().__init__()
        self.peso = torch.nn.Parameter(torch.zeros(1))
        # Ángulos (grados) de los robots respecto al frente del chasis. Un robot que se mueve
        # es una función del tiempo simulado desde la primera imagen, que devuelve su ángulo
        # o None cuando no está.
        self.robots = robots
        self.confianza = confianza
        self.retardo = retardo        # s: la imagen muestra el mundo de hace `retardo` (vídeo por wifi)
        self.historial = []           # (t, yaw del gimbal)
        self.t0 = None

    def forward(self, images):
        robot = simulacion.ULTIMO
        self.historial.append((robot.t, robot.gimbal.yaw))
        t_visto = robot.t - self.retardo
        anteriores = [y for t, y in self.historial if t <= t_visto + 1e-9]
        yaw = anteriores[-1] if anteriores else self.historial[0][1]
        if self.t0 is None:
            self.t0 = robot.t
        cajas = []
        for angulo in self.robots:
            if callable(angulo):
                angulo = angulo(max(0.0, t_visto - self.t0))
                if angulo is None:
                    continue
            rel = angulo - yaw
            if abs(rel) < 40:         # dentro del campo de visión
                cx = pixel_de(rel)
                cajas.append([cx - 60, 300, cx + 60, 420])
        n = len(cajas)
        return [dict(boxes=torch.tensor(cajas, dtype=torch.float32).reshape(n, 4),
                     scores=torch.full((n,), self.confianza), labels=torch.ones(n, dtype=torch.int64))]


class Args:
    def __init__(self, evidencias, sin_disparar=False, sin_mover=False, paradas=''):
        self.evidencias, self.sin_disparar, self.sin_mover = evidencias, sin_disparar, sin_mover
        self.paradas, self.simulacion = paradas, CARPETA


class PruebasDemo(unittest.TestCase):

    def setUp(self):
        self.salida = tempfile.mkdtemp(prefix='evid_')
        self.original = {k: getattr(C, k) for k in ['PARADAS', 'BAILE_FINAL', 'AUDIO_MOTOR', 'ESPERA_CAMARA',
                                                    'DISPARAR_A_TODOS', 'BARRIDO_COMPLETO', 'CONFIRMAR',
                                                    'VELOCIDAD_XY', 'AUDIO_DISPARO', 'AUDIO_FINAL',
                                                    'SEGUIMIENTO', 'SONIDO_CADA_DISPARO', 'LEER_ANGULO_GIMBAL',
                                                    'ANTICIPAR', 'RETARDO_CAMARA']}
        C.BAILE_FINAL, C.AUDIO_MOTOR, C.ESPERA_CAMARA = False, None, 0
        espera = mock.patch('time.sleep')   # sin esperas reales (cámara, disparos, batería)
        espera.start()
        self.addCleanup(espera.stop)

    def tearDown(self):
        for k, v in self.original.items():
            setattr(C, k, v)
        shutil.rmtree(self.salida, ignore_errors=True)

    def lanzar(self, robots, circuito, **kw):
        C.PARADAS = circuito
        ep_robot = demo.connect('wifi')
        d = demo.Demo(ep_robot, DetectorFalso(robots), Args(self.salida, **kw))
        d.ejecutar()
        resumen = json.load(open(os.path.join(d.registro.carpeta, 'resumen.json'), encoding='utf-8'))
        return ep_robot, d, resumen

    def test_ataca_al_robot_y_para_el_barrido(self):
        p = [dict(nombre='P1', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([70], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertEqual(len(r['ataques']), 1)
        self.assertAlmostEqual(r['ataques'][0]['yaw'], 70, delta=1)
        # Lo ve con yaw 60 y deja de barrer: imágenes con yaw 0 y 60, y luego las del seguimiento
        fases = [f['fase'] for f in d.registro.filas]
        self.assertEqual(fases[:2], ['barrido', 'barrido'])
        self.assertEqual(set(fases[2:]), {'seguimiento'})
        self.assertEqual(d.registro.filas[-1]['disparos'], 12)

    def test_sin_seguimiento_confirma_una_vez_y_dispara_la_rafaga(self):
        C.SEGUIMIENTO = False
        p = [dict(nombre='P1', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([70], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertEqual([f['fase'] for f in d.registro.filas], ['barrido', 'barrido', 'confirmado'])

    # --- seguimiento de robots que se mueven ------------------------------------------
    def test_sigue_a_un_robot_que_se_mueve_y_le_dispara_12_veces(self):
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 5 + 6 * t], p)
        self.assertEqual(ep.disparos(), 12)
        ataque = r['ataques'][0]
        self.assertTrue(ataque['completo'])
        self.assertAlmostEqual(ataque['velocidad_robot'], 6, delta=2)
        giros = [a for a in ep.acciones if a['tipo'] == 'gimbal.drive_speed']
        self.assertTrue(giros)
        self.assertEqual((giros[-1]['yaw_speed'], giros[-1]['pitch_speed']), (0, 0))   # queda parada

    def test_compensa_el_retardo_de_la_camara(self):
        # La imagen llega 0,3 s tarde y el robot va a 12 º/s: cada disparo debe caer sobre él
        # (la caja falsa mide unos 14º, así que basta con un error menor de 7º)
        C.PARADAS = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        C.RETARDO_CAMARA = 0.3
        ep = demo.connect('wifi')
        robot = lambda t: 5 + 12 * t   # noqa: E731
        detector = DetectorFalso([robot], retardo=0.3)
        d = demo.Demo(ep, detector, Args(self.salida))
        errores = []
        disparar = ep.blaster.fire

        def disparar_y_medir(**kw):
            errores.append(abs(robot(ep.t - detector.t0) - ep.gimbal.yaw))
            return disparar(**kw)
        ep.blaster.fire = disparar_y_medir
        d.ejecutar()
        self.assertEqual(len(errores), 12)
        self.assertLess(max(errores), 7)
        self.assertLess(np.mean(errores), 3)

    def test_dispara_solo_con_el_robot_centrado(self):
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 5 + 6 * t], p)
        disparos_previos = 0
        for f in d.registro.filas:
            if f['fase'] == 'seguimiento' and f['disparos'] > disparos_previos:
                self.assertLess(abs(f['objetivo_yaw'] - f['yaw']), 7)   # 0,4 del ancho de la caja falsa
                disparos_previos = f['disparos']
        self.assertEqual(disparos_previos, 12)

    def test_fija_al_robot_aunque_se_haya_movido_desde_el_barrido(self):
        # En el barrido está en 0; al ir a confirmarlo ya está en 18 (la versión anterior no disparaba)
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 0 if t < 0.05 else 18], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertAlmostEqual(r['ataques'][0]['yaw'], 18, delta=1)

    def test_no_fija_un_robot_demasiado_lejos_de_donde_se_vio(self):
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 0 if t < 0.05 else 35], p)
        self.assertEqual(ep.disparos(), 0)
        self.assertFalse(r['ataques'][0]['confirmado'])
        self.assertIn('sin_confirmar', [f['fase'] for f in d.registro.filas])

    def test_robot_que_desaparece_se_da_por_perdido(self):
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 0 if t < 1.0 else None], p)
        ataque = r['ataques'][0]
        self.assertFalse(ataque['completo'])
        self.assertTrue(0 < ataque['disparos'] < 12)
        self.assertEqual(r['paradas'][0]['atacados'], 0)
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))

    def test_sin_disparar_sigue_sin_usar_el_blaster(self):
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 5 + 6 * t], p, sin_disparar=True)
        self.assertEqual(ep.disparos(), 0)
        self.assertTrue(r['ataques'][0]['completo'])

    def test_lectura_del_gimbal_al_reves(self):
        def avisar_al_reves(gimbal):
            if gimbal._callback is not None:
                gimbal._callback((gimbal.pitch, -gimbal.yaw, gimbal.pitch, -gimbal.yaw))
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        with mock.patch.object(simulacion.Gimbal, '_avisar', avisar_al_reves):
            ep, d, r = self.lanzar([lambda t: 5 + 6 * t], p)
        self.assertTrue(d.torreta.usar_medida)
        self.assertEqual(d.torreta.signos, (1, -1))
        self.assertEqual(ep.disparos(), 12)

    def test_sin_lectura_del_gimbal_estima_el_angulo(self):
        C.LEER_ANGULO_GIMBAL = False
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: 5 + 6 * t], p)
        self.assertFalse(d.torreta.usar_medida)
        self.assertEqual(ep.disparos(), 12)

    def test_ctrl_c_al_seguir_para_la_torreta(self):
        C.PARADAS = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep = demo.connect('wifi')
        d = demo.Demo(ep, DetectorFalso([lambda t: 5 + 6 * t]), Args(self.salida))
        with mock.patch.object(ep.blaster, 'fire', side_effect=[True, True, KeyboardInterrupt]):
            with self.assertRaises(KeyboardInterrupt):
                d.ejecutar()
        giros = [a for a in ep.acciones if a['tipo'] == 'gimbal.drive_speed']
        self.assertEqual((giros[-1]['yaw_speed'], giros[-1]['pitch_speed']), (0, 0))
        self.assertEqual(ep.gimbal.yaw, 0)
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))

    def test_punteria_vertical_y_tamano_de_la_caja(self):
        imagen = np.zeros((720, 1280, 3), np.uint8)
        self.assertGreater(demo.auto_pitch(imagen, [600, 100, 680, 200]), 0)    # por encima del centro
        self.assertLess(demo.auto_pitch(imagen, [600, 500, 680, 600]), 0)
        self.assertAlmostEqual(demo.auto_pitch(imagen, [600, 300, 680, 420]), 0, places=6)
        ancho, alto = demo.tamano_angular(imagen, [580, 300, 700, 420])
        self.assertAlmostEqual(ancho, alto, delta=0.5)
        self.assertGreater(ancho, 0)

    def test_no_repite_un_robot_visto_en_dos_imagenes(self):
        C.BARRIDO_COMPLETO = True
        p = [dict(nombre='P1', movimientos=[], barrido=[0, 20, 40], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([20], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertEqual(len(r['ataques']), 1)

    def test_blaster_sin_respuesta_detiene_la_demo_y_registra_la_rafaga_parcial(self):
        C.PARADAS = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep = demo.connect('wifi')
        d = demo.Demo(ep, DetectorFalso([0]), Args(self.salida))
        with mock.patch.object(ep.blaster, 'fire', side_effect=[True, True, False]) as fire:
            with self.assertRaisesRegex(RuntimeError, 'no confirmó el disparo 3'):
                d.ejecutar()

        self.assertEqual(fire.call_count, 3)
        self.assertEqual(d.registro.filas[-1]['disparos'], 2)
        with open(os.path.join(d.registro.carpeta, 'resumen.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f)['disparos'], 2)
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))

    def test_dispara_a_todos_los_robots_de_la_parada(self):
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([-100, 10, 30, 175], p)
        self.assertEqual(ep.disparos(), 48)
        self.assertEqual(sorted(round(a['yaw']) for a in r['ataques']), [-100, 10, 30, 175])

    def test_solo_la_mejor_si_no_se_dispara_a_todos(self):
        C.DISPARAR_A_TODOS = False
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([10, 30], p)
        self.assertEqual(ep.disparos(), 12)

    def test_sin_detecciones_no_dispara_y_guarda_todo(self):
        p = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=1),
             dict(nombre='P2', movimientos=[(0, 0, 90)], barrido=C.BARRIDO_FRONTAL, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p)
        self.assertEqual(ep.disparos(), 0)
        self.assertEqual(r['imagenes'], 6 + 3)
        imagenes = glob.glob(os.path.join(d.registro.carpeta, '*.jpg'))
        originales = glob.glob(os.path.join(d.registro.carpeta, 'originales', '*.jpg'))
        self.assertEqual((len(imagenes), len(originales)), (9, 9))
        self.assertEqual(ep.gimbal.yaw, 0)

    def test_sin_disparar_y_sin_mover(self):
        p = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([0], p, sin_disparar=True, sin_mover=True)
        tipos = [a['tipo'] for a in ep.acciones]
        self.assertNotIn('blaster.fire', tipos)
        self.assertNotIn('chasis.move', tipos)
        self.assertEqual(len(r['ataques']), 1)

    def test_paradas_elegidas(self):
        p = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1),
             dict(nombre='P2', movimientos=[(0, 0.5, 0)], barrido=[0], pitch=0, objetivos=1),
             dict(nombre='P3', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p, paradas='P2')
        movs = [(a['x'], a['y']) for a in ep.acciones if a['tipo'] == 'chasis.move']
        self.assertEqual(movs, [(1, 0), (0, 0.5)])   # llega a P2 y no sigue
        self.assertEqual([x['nombre'] for x in r['paradas']], ['P2'])

    def test_usa_todos_los_modulos_y_el_baile(self):
        C.BAILE_FINAL, C.AUDIO_MOTOR = True, 'audio/engine_sound.wav'
        p = [dict(nombre='P1', movimientos=[(0.5, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([0], p)
        tipos = {a['tipo'].split('.')[0] for a in ep.acciones}
        for modulo in ['chasis', 'gimbal', 'camara', 'blaster', 'led', 'sonido', 'audio']:
            self.assertIn(modulo, tipos)

    def test_ctrl_c_deja_el_robot_quieto(self):
        p = [dict(nombre='P1', movimientos=[(1, 0, 0), (1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        C.PARADAS = p
        ep = demo.connect('wifi')
        mover = ep.chassis.move
        llamadas = []

        def mover_y_cortar(**kw):
            llamadas.append(kw)
            if len(llamadas) == 2:
                raise KeyboardInterrupt
            return mover(**kw)

        ep.chassis.move = mover_y_cortar
        d = demo.Demo(ep, DetectorFalso([]), Args(self.salida))
        with self.assertRaises(KeyboardInterrupt):
            d.ejecutar()
        ultimas = [a['tipo'] for a in ep.acciones[-4:]]
        self.assertEqual(ultimas, ['chasis.drive_speed', 'gimbal.recenter', 'camara.stop', 'led'])
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))
        self.assertTrue(os.path.isfile(os.path.join(d.registro.carpeta, 'resumen.json')))

    def test_velocidades_recortadas(self):
        C.VELOCIDAD_XY = 2.0     # aunque alguien la suba en circuito.py, no pasa de 0,5 m/s
        p = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p)
        v = [a['xy_speed'] for a in ep.acciones if a['tipo'] == 'chasis.move']
        self.assertEqual(v, [0.5])

    def confirmar(self, robots, angulo, ya_atacados):
        C.PARADAS = []
        ep = demo.connect('wifi')
        d = demo.Demo(ep, DetectorFalso(robots), Args(self.salida))
        d.camara = demo.Camara(ep, espera=0)
        return ep, d.apuntar_y_disparar('P1', angulo, 0.99, ya_atacados)

    def test_no_dispara_si_al_confirmar_el_robot_no_esta_centrado(self):
        ep, atacado = self.confirmar([30], 0, [])     # se esperaba en 0 y está en 30
        self.assertFalse(atacado)
        self.assertEqual(ep.disparos(), 0)

    def test_no_dispara_dos_veces_al_mismo_robot_al_confirmar(self):
        ep, atacado = self.confirmar([5], 0, [5])     # el más centrado ya se atacó
        self.assertFalse(atacado)
        self.assertEqual(ep.disparos(), 0)

    def test_confirma_y_corrige_la_punteria(self):
        ep, atacado = self.confirmar([8], 0, [])
        self.assertTrue(atacado)
        self.assertEqual(ep.disparos(), 12)
        self.assertAlmostEqual(ep.gimbal.yaw, 8, delta=0.5)

    def test_no_arranca_con_la_bateria_critica(self):
        simulacion.BATERIA = 5
        try:
            p = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
            with self.assertRaises(RuntimeError):
                self.lanzar([0], p)
            tipos = [a['tipo'] for a in simulacion.ULTIMO.acciones]
            self.assertNotIn('chasis.move', tipos)
            self.assertNotIn('blaster.fire', tipos)
        finally:
            simulacion.BATERIA = 87

    def test_un_movimiento_sin_respuesta_detiene_la_demo(self):
        class SinRespuesta:
            def wait_for_completed(self, timeout=None):
                return False   # el robot no confirma el movimiento a tiempo
        C.PARADAS = [dict(nombre='P1', movimientos=[(1, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep = demo.connect('wifi')
        ep.chassis.move = lambda **kw: SinRespuesta()
        d = demo.Demo(ep, DetectorFalso([]), Args(self.salida))
        with self.assertRaises(RuntimeError):
            d.ejecutar()
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))   # se cerró de forma segura

    def test_los_sonidos_no_se_solapan(self):
        class Sonando:
            is_completed = False
        enviados = []

        class Robot:
            def play_sound(self, sound_id, times=1):
                enviados.append(sound_id)
                return Sonando()
        senales = demo.Senales(Robot(), {'a': 1, 'b': 2})
        senales.sonido('a')
        senales.sonido('b')   # el primero sigue sonando: no se envía
        self.assertEqual(enviados, [1])

    def test_libera_el_cerrojo_que_deja_el_sdk(self):
        import threading
        cerrojo = threading.Lock()
        ep = mock.Mock()
        ep._action_dispatcher._in_progress_mutex = cerrojo
        cerrojo.acquire()
        demo.liberar_cerrojo_sdk(ep, Exception('otro error'))
        self.assertTrue(cerrojo.locked())
        demo.liberar_cerrojo_sdk(ep, Exception('Robot is already performing 1 action(s)'))
        self.assertFalse(cerrojo.locked())

    def test_bateria_sin_lectura_no_detiene_la_demo(self):
        class Bateria:
            def sub_battery_info(self, freq, callback, *args):
                return True            # la lectura no llega nunca

            def unsub_battery_info(self):
                raise AttributeError("'NoneType' object has no attribute 'done'")   # fallo del SDK
        ep = mock.Mock()
        ep.battery = Bateria()
        with mock.patch('time.time', side_effect=[0, 0, 10]):
            self.assertIsNone(demo.nivel_bateria(ep))

    def test_el_audio_de_disparo_suena_una_vez_por_rafaga(self):
        C.AUDIO_DISPARO = os.path.join(CARPETA, 'scar.wav')
        open(C.AUDIO_DISPARO, 'wb').close()
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        for seguimiento in (True, False):
            C.SEGUIMIENTO = seguimiento
            ep, d, r = self.lanzar([0], p)
            audios = [a['fichero'] for a in ep.acciones if a['tipo'] == 'audio']
            self.assertEqual(audios.count('scar.wav'), 1)
            self.assertEqual(ep.disparos(), 12)

    def test_cada_disparo_suena_con_su_audio_si_se_pide(self):
        C.AUDIO_DISPARO = os.path.join(CARPETA, 'scar.wav')
        C.SONIDO_CADA_DISPARO = True
        open(C.AUDIO_DISPARO, 'wb').close()
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        for seguimiento in (True, False):
            C.SEGUIMIENTO = seguimiento
            ep, d, r = self.lanzar([0], p)
            audios = [a['fichero'] for a in ep.acciones if a['tipo'] == 'audio']
            self.assertEqual(audios.count('scar.wav'), 12)
            self.assertEqual(ep.disparos(), 12)

    def test_baile_con_cancion_y_luces(self):
        C.BAILE_FINAL = True
        C.AUDIO_FINAL = os.path.join(CARPETA, 'cancion.wav')
        open(C.AUDIO_FINAL, 'wb').close()
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p)
        self.assertIn('cancion.wav', [a.get('fichero') for a in ep.acciones if a['tipo'] == 'audio'])
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))   # al cerrar, LED apagados

    def test_sin_audios_propios_usa_los_del_sdk(self):
        C.AUDIO_DISPARO, C.AUDIO_FINAL = 'audio/propios/no_existe.wav', None
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([0], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertIn(C.SONIDOS['disparo'], [a.get('id') for a in ep.acciones if a['tipo'] == 'sonido'])

    def test_detect_and_shoot_de_la_plantilla(self):
        ep = demo.connect('wifi')
        image, prediction = demo.detect_and_shoot(ep, DetectorFalso([10]), score_threshold=0.5)
        self.assertEqual(ep.disparos(), 1)
        self.assertAlmostEqual(ep.gimbal.yaw, 10, delta=0.5)


class PruebaPython38(unittest.TestCase):
    """El entorno del laboratorio es Python 3.8: no usar sintaxis más moderna."""

    def test_sintaxis(self):
        for fichero in glob.glob(os.path.join(WEEK3, '*.py')):
            with open(fichero, encoding='utf-8') as f:
                ast.parse(f.read(), fichero, feature_version=(3, 8))


if __name__ == '__main__':
    unittest.main()
