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


def semialto_px(distancia, alto=720, ancho=1280):
    """Mitad del alto (píxeles) de la caja de un robot de ALTURA_ROBOT m a esa distancia."""
    focal = ancho / (2 * np.tan(np.pi / 3))
    alto_grados = 2 * np.rad2deg(np.arctan(C.ALTURA_ROBOT / (2 * distancia)))
    return focal * np.tan(np.deg2rad(alto_grados / 2 * 120 / 90))


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
        # Hacia dónde miraba el gimbal cuando se tomó la imagen (también si se analiza más de una vez por segundo)
        yaw = robot.gimbal.yaw_en(t_visto)
        if self.t0 is None:
            self.t0 = robot.t
        cajas = []
        for angulo in self.robots:
            if callable(angulo):
                angulo = angulo(max(0.0, t_visto - self.t0))
                if angulo is None:
                    continue
            if isinstance(angulo, tuple):   # robot situado en el circuito (X, Y en m)
                px, py, rumbo = robot.pose
                distancia = np.hypot(angulo[0] - px, angulo[1] - py)
                rumbo_robot = np.rad2deg(np.arctan2(angulo[1] - py, angulo[0] - px))
                rel = (rumbo - yaw - rumbo_robot + 180) % 360 - 180
                medio = semialto_px(distancia)
            else:
                rel, medio = angulo - yaw, 60
            if abs(rel) < 40:         # dentro del campo de visión
                cx = pixel_de(rel)
                cajas.append([cx - medio, 360 - medio, cx + medio, 360 + medio])
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
                                                    'ANTICIPAR', 'RETARDO_CAMARA', 'BARRIDO_CONTINUO',
                                                    'ROBOTS_TOTALES', 'TIEMPO_MEMORIA', 'VIGILANCIA',
                                                    'ATACAR_EN_RUTA', 'ESPERA_OBSTACULO', 'MEMORIA',
                                                    'DETENER_SI_BLOQUEADO']}
        self.paso_imagen = simulacion.PASO_IMAGEN
        C.BAILE_FINAL, C.AUDIO_MOTOR, C.ESPERA_CAMARA = False, None, 0
        # En circuito.py las mejoras vienen desactivadas (la demo de main). Estas pruebas son de
        # las mejoras, así que las activan; las que prueban la demo de main las desactivan.
        C.SEGUIMIENTO, C.BARRIDO_CONTINUO, C.LEER_ANGULO_GIMBAL, C.MEMORIA = True, True, True, True
        C.SONIDO_CADA_DISPARO = False
        # La vigilancia del recorrido añade imágenes y divide los avances: sus pruebas la activan
        C.VIGILANCIA = False
        espera = mock.patch('time.sleep')   # sin esperas reales (cámara, disparos, batería)
        espera.start()
        self.addCleanup(espera.stop)

    def tearDown(self):
        for k, v in self.original.items():
            setattr(C, k, v)
        simulacion.PASO_IMAGEN = self.paso_imagen
        shutil.rmtree(self.salida, ignore_errors=True)

    def lanzar(self, robots, circuito, **kw):
        C.PARADAS = circuito
        ep_robot = demo.connect('wifi')
        d = demo.Demo(ep_robot, DetectorFalso(robots), Args(self.salida, **kw))
        d.ejecutar()
        resumen = json.load(open(os.path.join(d.registro.carpeta, 'resumen.json'), encoding='utf-8'))
        return ep_robot, d, resumen

    def test_ataca_al_robot_y_para_el_barrido(self):
        C.BARRIDO_CONTINUO = False
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

    def test_por_defecto_es_la_demo_de_main(self):
        # Las mejoras vienen desactivadas en circuito.py: se activan una a una en el laboratorio
        nuevas = ['SEGUIMIENTO', 'BARRIDO_CONTINUO', 'LEER_ANGULO_GIMBAL', 'MEMORIA', 'VIGILANCIA',
                  'DETENER_SI_BLOQUEADO']
        self.assertEqual({k: self.original[k] for k in nuevas}, dict.fromkeys(nuevas, False))
        self.assertTrue(self.original['SONIDO_CADA_DISPARO'])
        for k in nuevas + ['SONIDO_CADA_DISPARO']:
            setattr(C, k, self.original[k])
        C.AUDIO_DISPARO = os.path.join(CARPETA, 'scar.wav')
        open(C.AUDIO_DISPARO, 'wb').close()
        p = [dict(nombre='P1', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([70], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertEqual([f['fase'] for f in d.registro.filas], ['barrido', 'barrido', 'confirmado'])
        tipos = [a['tipo'] for a in ep.acciones]
        self.assertNotIn('gimbal.drive_speed', tipos)       # sin seguimiento ni barrido continuo
        self.assertEqual([a for a in ep.acciones if a['tipo'] == 'chasis.move'][0]['x'], 0.5)   # sin tramos
        audios = [a['fichero'] for a in ep.acciones if a['tipo'] == 'audio']
        self.assertEqual(audios.count('scar.wav'), 12)       # la SCAR en cada disparo
        self.assertFalse(d.torreta.suscrito)                 # sin leer el ángulo del gimbal

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

    def test_seguimiento_con_cpu_completa_la_rafaga(self):
        # Con CPU cada imagen tarda ~1,1 s y la torreta sigue girando mientras se analiza: con la
        # ganancia de GPU se pasaba de largo y oscilaba (3/12 disparos a 3 º/s). Ahora la ganancia
        # se adapta al tiempo medido por imagen.
        simulacion.PASO_IMAGEN = 1.1
        C.PARADAS = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        C.RETARDO_CAMARA = 0.3
        for v in (0, 3, 6, 10):
            ep = demo.connect('wifi')
            robot = lambda t, v=v: 5 + v * t   # noqa: E731
            detector = DetectorFalso([robot], retardo=0.3)
            d = demo.Demo(ep, detector, Args(self.salida))
            errores = []
            disparar = ep.blaster.fire

            def disparar_y_medir(**kw):
                errores.append(abs(robot(ep.t - detector.t0) - ep.gimbal.yaw))
                return disparar(**kw)
            ep.blaster.fire = disparar_y_medir
            d.ejecutar()
            ataque = d.ataques[0]
            self.assertTrue(ataque['completo'], f'{v} º/s')
            self.assertEqual(len(errores), 12)
            self.assertLess(max(errores), 7, f'{v} º/s')
            self.assertAlmostEqual(ataque['s_por_imagen'], 1.1, delta=0.15)
            self.assertLess(ataque['segundos'], 20)

    def test_no_dispara_hasta_ver_dos_veces_al_robot(self):
        # Con una sola imagen no se conoce la velocidad del robot y el disparo saldría detrás
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([0], p)
        filas = [f for f in d.registro.filas if f['fase'] == 'seguimiento']
        self.assertEqual(filas[0]['disparos'], 0)
        self.assertEqual(filas[1]['disparos'], 1)

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

    # --- barrido continuo y memoria (fase 2) ---------------------------------------------
    def test_ruta_del_barrido_continuo(self):
        self.assertEqual(demo.ruta_barrido(C.BARRIDO_360, 70), [0, 145, -145])
        self.assertEqual(demo.ruta_barrido(C.BARRIDO_FRONTAL, 70), [0, -45, 45])
        self.assertEqual(demo.ruta_barrido([30, -60, 90], 70), [30, 90, -60])

    def test_barrido_continuo_sin_detecciones_lo_recorre_entero(self):
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p)
        yaws = [f['yaw'] for f in d.registro.filas]
        self.assertLessEqual(min(yaws), -140)
        self.assertGreaterEqual(max(yaws), 140)
        saltos = np.abs(np.diff(yaws))
        self.assertTrue(all(s >= C.PASO_BARRIDO - 0.5 for s in saltos))   # una imagen cada PASO_BARRIDO
        self.assertEqual(ep.gimbal.yaw, 0)
        giros = [a for a in ep.acciones if a['tipo'] == 'gimbal.drive_speed']
        self.assertEqual((giros[-1]['yaw_speed'], giros[-1]['pitch_speed']), (0, 0))

    def test_barrido_continuo_tarda_menos_que_por_pasos(self):
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        tiempos = {}
        for continuo in (True, False):
            C.BARRIDO_CONTINUO = continuo
            ep, d, r = self.lanzar([], p)
            tiempos[continuo] = r['paradas'][0]['segundos']
        self.assertLess(tiempos[True], tiempos[False])

    def test_barrido_continuo_ataca_en_cuanto_lo_ve_y_para(self):
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_360, pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([100], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertAlmostEqual(r['ataques'][0]['yaw'], 100, delta=1)
        barrido = [f for f in d.registro.filas if f['fase'] == 'barrido']
        self.assertLess(max(f['yaw'] for f in barrido), 100)       # no sigue girando hasta 145
        self.assertGreaterEqual(min(f['yaw'] for f in barrido), 0)  # ni barre el otro lado

    def test_memoria_no_repite_un_robot_desde_otra_parada(self):
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_FRONTAL, pitch=0, objetivos=None),
             dict(nombre='P2', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(2.0, 0.3)], p)
        self.assertEqual(ep.disparos(), 12)
        self.assertEqual([x['atacados'] for x in r['paradas']], [1, 0])
        self.assertAlmostEqual(r['memoria'][0]['x'], 2.0, delta=0.2)
        self.assertAlmostEqual(r['memoria'][0]['y'], 0.3, delta=0.2)
        self.assertEqual(r['pose_final'][:2], [0.5, 0.0])

    def test_sin_memoria_se_repite_el_ataque(self):
        C.TIEMPO_MEMORIA = 0
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_FRONTAL, pitch=0, objetivos=None),
             dict(nombre='P2', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(2.0, 0.3)], p)
        self.assertEqual(ep.disparos(), 24)

    def test_sin_memoria_cada_parada_empieza_de_cero(self):
        # MEMORIA = False (por defecto): como en main, el robot se ataca desde las dos paradas
        C.MEMORIA = False
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_FRONTAL, pitch=0, objetivos=None),
             dict(nombre='P2', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(2.0, 0.3)], p)
        self.assertEqual(ep.disparos(), 24)
        self.assertEqual([x['atacados'] for x in r['paradas']], [1, 1])
        self.assertEqual(len(r['memoria']), 2)   # se anotan igualmente, para las evidencias

    def test_memoria_distingue_robots_juntos_en_angulo(self):
        # A 2 m y separados 0,6 m (unos 17 grados): son dos robots
        p = [dict(nombre='P1', movimientos=[], barrido=C.BARRIDO_FRONTAL, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(2.0, 0.3), (2.0, -0.3)], p)
        self.assertEqual(ep.disparos(), 24)

    def test_robot_atacado_que_se_aleja_se_vuelve_a_atacar(self):
        # Atacado en P1; cuando el robot llega a P2, se ha ido 1,5 m a un lado
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=1),
             dict(nombre='P2', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([lambda t: (2.0, 0.0) if t < 6 else (2.0, 1.5)], p)
        self.assertEqual(ep.disparos(), 24)

    def test_robots_totales_salta_los_barridos_restantes(self):
        C.ROBOTS_TOTALES = 1
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=None),
             dict(nombre='P2', movimientos=[(0.5, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([0], p)
        self.assertEqual([x['nombre'] for x in r['paradas']], ['P1'])
        self.assertEqual([a['x'] for a in ep.acciones if a['tipo'] == 'chasis.move'], [0.5])   # el recorrido sigue

    def test_distancia_y_posicion_en_el_circuito(self):
        imagen = np.zeros((720, 1280, 3), np.uint8)
        for distancia in (1.0, 2.5):
            m = semialto_px(distancia)
            caja = [640 - m, 360 - m, 640 + m, 360 + m]
            self.assertAlmostEqual(demo.distancia_estimada(imagen, caja, C.ALTURA_ROBOT), distancia, delta=0.01)
        pose = demo.mover_pose((0, 0, 0), 1.0, 0, 90)           # avanza 1 m y gira 90 grados a la izquierda
        np.testing.assert_allclose(pose, (1.0, 0.0, 90.0), atol=1e-9)
        pose = demo.mover_pose(pose, 1.0, 0.5, 0)                # ahora adelante es +Y y derecha es +X
        np.testing.assert_allclose(pose, (1.5, 1.0, 90.0), atol=1e-9)
        np.testing.assert_allclose(demo.punto_en_circuito((0, 0, 0), 90, 2.0), (0.0, -2.0), atol=1e-9)

    def test_memoria_olvida_los_descartes(self):
        m = demo.Memoria(tiempo_descarte=3.0)
        m.anotar((2.0, 0.0), 0.0, 2.0, 'descartado')
        self.assertIsNotNone(m.conocido((2.0, 0.1), 2.0, 2.0, (0, 0)))
        self.assertIsNone(m.conocido((2.0, 0.1), 4.0, 2.0, (0, 0)))
        m.anotar((2.0, 0.0), 0.0, 2.0, 'atacado')
        self.assertIsNotNone(m.conocido((2.4, 0.0), 100.0, 2.0, (0, 0)))   # a lo largo de la visual: el mismo
        self.assertIsNone(m.conocido((2.0, 0.4), 100.0, 2.0, (0, 0)))      # de lado: otro robot

    # --- vigilancia durante el recorrido (fase 3) ------------------------------------------
    def movimientos(self, ep):
        return [(round(a['x'], 3), round(a['y'], 3), a['z']) for a in ep.acciones if a['tipo'] == 'chasis.move']

    def test_vigilancia_divide_el_avance_y_mira_hacia_donde_va(self):
        C.VIGILANCIA = True
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0), (0, 0, 90), (0, 0.6, 0)], barrido=[0], pitch=0,
                  objetivos=1)]
        ep, d, r = self.lanzar([], p)
        self.assertEqual(self.movimientos(ep), [(0.5, 0, 0), (0.5, 0, 0), (0, 0, 90), (0, 0.3, 0), (0, 0.3, 0)])
        ruta = [f for f in d.registro.filas if f['fase'] == 'ruta']
        self.assertTrue(ruta)
        yaws = sorted({round(f['yaw']) for f in ruta})
        self.assertEqual(yaws, [0, 90])                     # al frente y, en el avance lateral, a la derecha
        # Tras girar 90 grados a la izquierda mira hacia +Y, y su derecha es +X
        np.testing.assert_allclose(r['pose_final'], [1.6, 0.0, 90.0], atol=1e-6)

    def test_analiza_imagenes_con_el_chasis_en_marcha(self):
        C.VIGILANCIA = True
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([], p)
        ruta = [f for f in d.registro.filas if f['fase'] == 'ruta']
        # Una revisión parado al empezar y unas 5 por tramo en marcha (0,5 m a 0,3 m/s, una cada 0,3 s)
        self.assertGreaterEqual(len(ruta), 8)
        self.assertEqual(r['eventos_ruta'], [])

    def test_ataca_a_un_rival_visto_en_el_recorrido(self):
        C.VIGILANCIA = True
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=C.BARRIDO_360, pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(1.2, 0.8)], p)
        self.assertEqual(ep.disparos(), 12)                 # en el recorrido, y en la parada ya no se repite
        self.assertEqual(r['ataques'][0]['parada'], 'P1-ruta')
        self.assertEqual([e['tipo'] for e in r['eventos_ruta']], ['ataque'])
        self.assertEqual(r['paradas'][0]['atacados'], 0)

    def test_revisa_parado_un_rival_que_aparece_con_el_chasis_en_marcha(self):
        C.VIGILANCIA = True
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([lambda t: None if t < 0.8 else (1.8, 0.9)], p)
        self.assertEqual(r['ataques'][0]['parada'], 'P1-ruta')
        self.assertEqual(ep.disparos(), 12)
        # El ataque es entre los dos tramos: después del primero y antes del segundo
        tipos = [a['tipo'] for a in ep.acciones]
        primero = tipos.index('chasis.move')
        segundo = tipos.index('chasis.move', primero + 1)
        self.assertIn('blaster.fire', tipos[primero:segundo])

    def test_espera_a_que_un_robot_deje_libre_el_camino(self):
        C.VIGILANCIA, C.ATACAR_EN_RUTA = True, False
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([lambda t: (0.9, 0.0) if t < 2 else (0.9, 2.0)], p)
        espera = [e for e in r['eventos_ruta'] if e['tipo'] == 'espera']
        self.assertEqual(len(espera), 1)
        self.assertGreaterEqual(espera[0]['segundos'], 1.5)
        self.assertIn((255, 255, 0), [a.get('rgb') for a in ep.acciones if a['tipo'] == 'led'])
        self.assertEqual(self.movimientos(ep), [(0.5, 0, 0), (0.5, 0, 0)])
        tipos = [a['tipo'] for a in ep.acciones]
        self.assertGreater(tipos.index('chasis.move'), max(i for i, a in enumerate(ep.acciones)
                                                           if a.get('rgb') == (255, 255, 0)))

    def test_camino_bloqueado_detiene_la_demo_de_forma_segura(self):
        C.VIGILANCIA, C.ATACAR_EN_RUTA, C.ESPERA_OBSTACULO, C.DETENER_SI_BLOQUEADO = True, False, 2, True
        C.PARADAS = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=None)]
        ep = demo.connect('wifi')
        d = demo.Demo(ep, DetectorFalso([(0.7, 0.0)]), Args(self.salida))
        with self.assertRaisesRegex(RuntimeError, 'bloquea el camino'):
            d.ejecutar()
        self.assertEqual(self.movimientos(ep), [])
        self.assertEqual(ep.acciones[-1]['rgb'], (0, 0, 0))
        self.assertEqual(ep.gimbal.yaw, 0)

    def test_camino_bloqueado_sigue_el_recorrido_por_defecto(self):
        # Un rival inutilizado no se aparta y la distancia puede estar mal calibrada: la demo sigue
        self.assertFalse(self.original['DETENER_SI_BLOQUEADO'])
        C.DETENER_SI_BLOQUEADO = False
        C.VIGILANCIA, C.ATACAR_EN_RUTA, C.ESPERA_OBSTACULO = True, False, 2
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(0.7, 0.0)], p)
        self.assertEqual(len(self.movimientos(ep)), 2)
        bloqueos = [e for e in r['eventos_ruta'] if e['tipo'] == 'bloqueado']
        self.assertTrue(bloqueos)
        self.assertTrue(all(e['sigue'] for e in bloqueos))
        self.assertEqual(r['pose_final'][:2], [1.0, 0.0])

    def test_un_robot_a_un_lado_o_lejos_no_bloquea(self):
        C.VIGILANCIA, C.ATACAR_EN_RUTA = True, False
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([(0.8, 0.6), (3.5, 0.0)], p)
        self.assertEqual(r['eventos_ruta'], [])
        self.assertNotIn((255, 255, 0), [a.get('rgb') for a in ep.acciones if a['tipo'] == 'led'])
        self.assertEqual(len(self.movimientos(ep)), 2)

    def test_sin_mover_no_vigila(self):
        C.VIGILANCIA = True
        p = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=[0], pitch=0, objetivos=1)]
        ep, d, r = self.lanzar([(1.2, 0.8)], p, sin_mover=True)
        self.assertNotIn('ruta', [f['fase'] for f in d.registro.filas])

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
        for continuo in (True, False):
            C.BARRIDO_CONTINUO = continuo
            ep, d, r = self.lanzar([-100, 10, 30, 175], p)
            self.assertEqual(ep.disparos(), 48, f'continuo={continuo}')
            self.assertEqual(sorted(round(a['yaw']) for a in r['ataques']), [-100, 10, 30, 175])

    def test_solo_la_mejor_si_no_se_dispara_a_todos(self):
        C.DISPARAR_A_TODOS = False
        p = [dict(nombre='P1', movimientos=[], barrido=[0], pitch=0, objetivos=None)]
        ep, d, r = self.lanzar([10, 30], p)
        self.assertEqual(ep.disparos(), 12)

    def test_sin_detecciones_no_dispara_y_guarda_todo(self):
        C.BARRIDO_CONTINUO = False
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
        C.BAILE_FINAL, C.AUDIO_MOTOR, C.VIGILANCIA = True, 'audio/engine_sound.wav', True
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
