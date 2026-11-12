"""Umbral reducido por zona (umbral_zona en circuito.py), con las cajas reales de las pruebas del 11/11.

    python -m unittest discover -s "ENTREGA 2/WEEK3/tests"
"""

import os
import sys
import tempfile
import types
import unittest

import numpy as np

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
from recorrido import paradas_desde_plano  # noqa: E402

IMAGEN = np.zeros((720, 1280, 3), np.uint8)


def prediccion(*detecciones):
    return dict(boxes=np.array([c for c, _ in detecciones], dtype=float).reshape(-1, 4),
                scores=np.array([s for _, s in detecciones], dtype=float))


def seleccionar(zona, yaw, *detecciones, distancia_max=None):
    falso = types.SimpleNamespace(zona=zona, distancia_max=distancia_max)
    return [round(s, 3) for _, s in demo.Demo.seleccionar_parada(falso, IMAGEN, prediccion(*detecciones), yaw)]


ZONA = dict(yaw=(-150, -30), umbral=0.7)


class UmbralZona(unittest.TestCase):
    def test_p1_lleva_la_zona_del_robot_camuflado(self):
        p1 = next(p for p in C.PARADAS if p['nombre'] == 'P1')
        self.assertEqual(p1['umbral_zona']['umbral'], C.UMBRAL_CAMUFLADO)
        self.assertLess(C.UMBRAL_CAMUFLADO, C.UMBRAL)
        self.assertTrue(all('umbral_zona' not in p for p in C.PARADAS if p['nombre'] != 'P1'))

    def test_sin_zona_solo_cuenta_el_umbral_general(self):
        self.assertEqual(seleccionar(None, -90, ([636, 244, 807, 407], 0.724)), [])
        self.assertEqual(seleccionar(None, 90, ([502, 340, 651, 466], 0.997)), [0.997])

    def test_robot_camuflado_a_la_izquierda_se_acepta(self):
        # 005_P1_sin_confirmar_yaw-90 y 008_P1_barrido_yaw-120 del 11/11
        self.assertEqual(seleccionar(ZONA, -90.5, ([636.2, 244.2, 806.9, 407.1], 0.724)), [0.724])
        self.assertEqual(seleccionar(ZONA, -120, ([973.5, 279.8, 1164.5, 444.5], 0.741)), [0.741])

    def test_caja_de_robomaster_a_la_derecha_no_se_acepta(self):
        # 001_P1_barrido_yaw+90: foto de un RoboMaster en una caja de cartón, 0,84
        self.assertEqual(seleccionar(ZONA, 90, ([621.1, 380.1, 657.6, 453.0], 0.844)), [])

    def test_silla_cercana_no_se_acepta_aunque_este_en_la_zona(self):
        # 008_P1_barrido_yaw-120 del 11/11 (14:54): silla de 0,72 que ocupa todo el alto
        self.assertEqual(seleccionar(ZONA, -120, ([42.3, 0.0, 935.6, 720.0], 0.716),
                                     ([973.5, 279.8, 1164.5, 444.5], 0.741)), [0.741])

    def test_por_encima_del_umbral_general_cuenta_en_cualquier_lado(self):
        self.assertEqual(seleccionar(ZONA, 90, ([502, 340, 651, 466], 0.997)), [0.997])

    def test_silla_de_la_recta_final_no_es_un_robot_aunque_supere_el_umbral(self):
        # 087_R2-marcha_fijado_yaw+180 (16:42): dos sillas de 0,99 y 0,95 y el rival de 0,93
        silla_dcha, silla_izq, rival = ([804.1, 35.2, 1280.0, 706.9], 0.993), ([4.1, 0.0, 494.5, 682.1], 0.955), \
            ([848.4, 459.6, 1034.3, 614.2], 0.931)
        self.assertEqual(seleccionar(None, 180, silla_dcha, silla_izq, rival), [])
        pred = prediccion(silla_dcha, silla_izq, rival)
        self.assertEqual([round(s, 3) for _, s in demo.robots(IMAGEN, pred, 0.8)], [0.931])

    def test_robots_reales_no_se_descartan_por_su_tamano(self):
        # El más cercano del 11/11: el de la caja de P1 a 0,96 m (197 px de alto)
        pred = prediccion(([422.4, 372.2, 640.0, 569.2], 0.999))
        self.assertEqual(len(demo.robots(IMAGEN, pred, C.UMBRAL)), 1)


class DistanciaMaxima(unittest.TestCase):
    """En P1 no cuenta el robot del fondo que se ve a la izquierda (prueba de las 16:33)."""

    def test_p1_lleva_distancia_maxima(self):
        p1 = next(p for p in C.PARADAS if p['nombre'] == 'P1')
        self.assertEqual(p1['distancia_max'], 2.0)
        self.assertTrue(all('distancia_max' not in p for p in C.PARADAS if p['nombre'] != 'P1'))

    def test_el_robot_del_fondo_no_cuenta_y_el_camuflado_si(self):
        # 004_P1_corrigiendo_yaw-60: robot del fondo 1,00 (63 px de alto) y camuflado 0,95
        fondo, camuflado = ([563.1, 302.3, 639.8, 365.3], 0.997), ([205.0, 291.7, 395.0, 460.5], 0.946)
        self.assertEqual(seleccionar(ZONA, -60, fondo, camuflado, distancia_max=2.0), [0.946])
        # 003_P1_barrido_yaw-90: el del fondo a 2,6 m (66 px) junto al camuflado (156 px)
        self.assertEqual(seleccionar(ZONA, -90, ([917.7, 331.9, 988.4, 397.9], 0.995),
                                     ([610.4, 319.2, 768.3, 475.0], 0.933), distancia_max=2.0), [0.933])

    def test_los_dos_robots_de_p1_estan_dentro(self):
        caja = ([422.4, 372.2, 640.0, 569.2], 0.999)   # 001_P1_barrido_yaw+90 (16:42)
        self.assertEqual(seleccionar(ZONA, 90, caja, distancia_max=2.0), [0.999])
        camuflado = ([598.2, 289.4, 725.6, 414.1], 0.956)   # 005_P1_confirmado_yaw-80 (16:42)
        self.assertEqual(seleccionar(ZONA, -80, camuflado, distancia_max=2.0), [0.956])

    def test_sin_distancia_maxima_el_del_fondo_cuenta(self):
        self.assertEqual(seleccionar(None, -60, ([563.1, 302.3, 639.8, 365.3], 0.997)), [0.997])

    def test_recorrido_conserva_la_distancia_maxima(self):
        p = paradas_desde_plano(0, [dict(nombre='A', punto=(1, 0), barrido=[0], distancia_max=2.0)])[0]
        self.assertEqual(p['distancia_max'], 2.0)

    def test_recorrido_conserva_la_zona(self):
        p = paradas_desde_plano(0, [dict(nombre='A', punto=(1, 0), barrido=[0], umbral_zona=ZONA)])[0]
        self.assertEqual(p['umbral_zona'], ZONA)


class Medidas(unittest.TestCase):
    def test_despues_del_tunel_las_x_son_un_15_por_ciento_mas_largas(self):
        r1 = next(p for p in C.PLANO if p['nombre'] == 'R1')['movimientos']
        r2 = next(p for p in C.PLANO if p['nombre'] == 'R2')['movimientos']
        xs = [m['x'] for m in r1 + r2 if 'x' in m]
        for nuevo, antes in zip(xs, [1.9, -1.25, 2.5, 2.0]):
            self.assertAlmostEqual(nuevo / antes, 1.15, delta=0.01)
        ys = [m['y'] for m in r1 + r2 if 'y' in m]
        self.assertEqual(ys, [-1.0, 1.0, -0.7])



class TorretaAntes(unittest.TestCase):
    """La torreta empieza a girar hacia el ataque en marcha durante los movimientos anteriores."""

    def preparar(self, movimientos):
        from unittest import mock
        falso = types.SimpleNamespace(torreta=mock.Mock())
        hilo = demo.Demo.preparar_torreta(falso, movimientos)
        if hilo is not None:
            hilo.join(2)
        return hilo, falso.torreta

    def test_en_r2_gira_180_desde_el_principio(self):
        r2 = next(p for p in C.PLANO if p['nombre'] == 'R2')['movimientos']
        hilo, torreta = self.preparar(r2)
        self.assertIsNotNone(hilo)
        torreta.ir.assert_called_once_with(180, C.PITCH_RIVAL_ALTO)

    def test_sin_movimientos_antes_del_ataque_no_hace_nada(self):
        hilo, torreta = self.preparar([dict(x=1.0, atacar=90)])
        self.assertIsNone(hilo)
        torreta.ir.assert_not_called()

    def test_con_un_giro_del_chasis_por_medio_no_gira_antes(self):
        hilo, _ = self.preparar([dict(z=90), dict(x=1.0, atacar=90)])
        self.assertIsNone(hilo)


if __name__ == '__main__':
    unittest.main()
