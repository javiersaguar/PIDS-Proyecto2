"""Fotos de la cámara durante todo el recorrido (FOTOS_RECORRIDO en circuito.py).

    python -m unittest discover -s "ENTREGA 2/WEEK3/tests"
"""

import os
import sys
import tempfile
import unittest

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
WEEK3 = os.path.dirname(AQUI)
sys.path.insert(0, WEEK3)

import simulacion  # noqa: E402

simulacion.instalar(tempfile.mkdtemp(prefix='sim_'))

from demo_utils import Fotografo  # noqa: E402


class CamaraFalsa:
    def __init__(self):
        self.frame, self.t = None, 0.0

    def llega(self, t):
        self.frame, self.t = np.full((72, 128, 3), int(t) % 255, np.uint8), t

    def ultimo(self):
        return self.frame, self.t


class Fotos(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix='fotos_')
        self.camara = CamaraFalsa()
        self.fase = 'P1-ruta'
        # intervalo enorme: el hilo no saca ninguna y las pruebas llaman a foto() a mano
        self.f = Fotografo(self.camara, self.carpeta, intervalo=3600, fase=lambda: self.fase)

    def tearDown(self):
        self.f._parar.set()

    def fotos(self):
        return sorted(os.listdir(self.f.carpeta))

    def test_sin_fotogramas_no_guarda_nada(self):
        self.assertIsNone(self.f.foto())
        self.assertEqual(self.fotos(), [])

    def test_guarda_con_la_fase_en_el_nombre(self):
        self.camara.llega(1.0)
        self.f.foto()
        self.fase = 'baile'
        self.camara.llega(2.0)
        self.f.foto()
        nombres = self.fotos()
        self.assertEqual(len(nombres), 2)
        self.assertTrue(nombres[0].startswith('0001_P1-ruta_'))
        self.assertTrue(nombres[1].startswith('0002_baile_'))

    def test_no_repite_el_mismo_fotograma(self):
        self.camara.llega(1.0)
        self.assertIsNotNone(self.f.foto())
        self.assertIsNone(self.f.foto())
        self.assertEqual(len(self.fotos()), 1)

    def test_fase_rara_no_rompe_el_nombre(self):
        self.fase = 'R1 / marcha:1'
        self.camara.llega(1.0)
        self.assertTrue(self.fotos() == [] and self.f.foto().endswith('.jpg'))
        self.assertIn('R1_marcha_1', self.fotos()[0])

    def test_cerrar_saca_la_ultima_y_cuenta(self):
        self.camara.llega(5.0)
        self.assertEqual(self.f.cerrar(), 1)


if __name__ == '__main__':
    unittest.main()
