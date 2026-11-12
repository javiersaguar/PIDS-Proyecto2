import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deteccion import Detector, regla_auto


class ReglaAuto(unittest.TestCase):
    def test_umbral_y_centro(self):
        self.assertEqual(regla_auto([[40, 40, 60, 60]], [.95], 100, 100), 0)
        self.assertIsNone(regla_auto([[40, 40, 60, 60]], [.949], 100, 100))

    def test_borde_recortado(self):
        self.assertIsNone(regla_auto([[49, 40, 80, 60]], [.99], 100, 100))
        self.assertIsNone(regla_auto([[0, 0, 20, 20]], [.99], 100, 100))

    def test_sin_cajas_y_datos_invalidos(self):
        for box in ([float('nan'), 0, 100, 100], [70, 0, 20, 100], [0, 0, float('inf'), 100]):
            self.assertIsNone(regla_auto([box], [1], 100, 100))
        self.assertIsNone(regla_auto([], [], 100, 100))
        self.assertIsNone(regla_auto([[0, 0, 100, 100]], [float('nan')], 100, 100))

    def test_inferencia_pendiente_no_acumula_imagenes(self):
        class Imagen:
            shape = (100, 100, 3)
        entrada = [(Imagen(), 1)]
        llamadas = []
        resultados = []
        dentro, continuar, terminado = threading.Event(), threading.Event(), threading.Event()

        def inferir(image):
            llamadas.append(image)
            if len(llamadas) == 1:
                dentro.set()
                continuar.wait(2)
            return dict(boxes=[], scores=[], ms=1)

        def publicar(result):
            resultados.append(result)
            if len(resultados) == 2:
                terminado.set()

        detector = Detector(lambda: entrada[0], publicar)
        detector._gpu = inferir
        detector.start()
        try:
            self.assertTrue(dentro.wait(2))
            entrada[0] = (Imagen(), 2)
            entrada[0] = (Imagen(), 3)
            continuar.set()
            self.assertTrue(terminado.wait(2))
        finally:
            continuar.set()
            detector.cerrar()
        self.assertEqual([r['instante'] for r in resultados], [1, 3])
        self.assertEqual(len(llamadas), 2)


if __name__ == '__main__':
    unittest.main()
