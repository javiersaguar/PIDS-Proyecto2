"""Comprueba negativos, límites temporales y vídeos de distinta duración."""

from pathlib import Path
import sys
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from visualizaciones_eda import preparar_datos, recuentos_interactivos


class FigurasEdaTests(unittest.TestCase):
    def setUp(self):
        self.imgs = pd.DataFrame([
            dict(secuencia='V01', frame=24, robots=1, difficult=1),
            dict(secuencia='V01', frame=48, robots=0, difficult=0),
            dict(secuencia='V01', frame=50, robots=2, difficult=0),
            dict(secuencia='V02', frame=24, robots=1, difficult=0),
        ])
        cajas = pd.DataFrame([
            dict(secuencia='V01', frame=24, cx=.5, cy=.5, difficult=1),
            dict(secuencia='V01', frame=50, cx=.4, cy=.5, difficult=0),
            dict(secuencia='V01', frame=50, cx=.6, cy=.5, difficult=0),
            dict(secuencia='V02', frame=24, cx=1., cy=1., difficult=0),
        ])
        self.datos = preparar_datos(self.imgs, cajas, fps=10)

    def test_negativos_en_denominador_y_limite_de_cinco_segundos(self):
        primera, segunda = self.datos['ventanas'][:2]
        self.assertEqual(primera['imagenes'], 2)
        self.assertEqual(primera['cuentas'], [1, 1])
        self.assertEqual(primera['mapas'][0].sum(), 50)
        self.assertEqual(segunda['ventana'], 1)
        self.assertEqual(segunda['cuentas'], [2, 0])
        self.assertEqual(segunda['mapas'][1].sum(), 0)

    def test_borde_incluido_y_difficult_es_subconjunto(self):
        ultimo = self.datos['globales'][-1]
        self.assertEqual(ultimo['mapas'][0][-1, -1], 100)
        for r in self.datos['globales'] + self.datos['ventanas']:
            self.assertTrue((r['mapas'][1] <= r['mapas'][0]).all())

    def test_video_corto_no_se_rellena_con_ceros(self):
        fig = recuentos_interactivos(self.datos)
        self.assertEqual(list(fig.frames[-1].data[0].y), [1, 0, 2])
        self.assertEqual(list(fig.frames[-1].data[1].y), [1])
        self.assertEqual(len(fig.frames), 3)


if __name__ == '__main__':
    unittest.main()
