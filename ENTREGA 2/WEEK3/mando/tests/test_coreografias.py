"""Límites cinemáticos y cierre de los cuatro bailes, sin robot."""
import ast
import math
from pathlib import Path
import sys
import unittest

MANDO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANDO))
import coreografias as c


class PruebasCoreografias(unittest.TestCase):
    def test_cada_baile_cabe_en_un_metro_y_vuelve_al_origen(self):
        for nombre in c.CATALOGO:
            with self.subTest(nombre=nombre):
                recorrido = c.validar(nombre)
                self.assertLessEqual(recorrido['ancho'], 1)
                self.assertLessEqual(recorrido['alto'], 1)
                self.assertLess(math.hypot(recorrido['x'], recorrido['y']), .01)
                self.assertLess(abs(recorrido['rumbo']), 1)

    def test_moonwalk_se_aleja_35_centimetros_y_la_torreta_mira_atras(self):
        self.assertAlmostEqual(c.validar('moonwalk')['ancho'], .35, places=4)
        compas = 4 * 60 / 117
        paso = c.muestra('moonwalk', 7 * compas)
        self.assertEqual(paso['yaw'], 180)
        self.assertGreaterEqual(paso['vx'], 0)

    def test_la_risa_respeta_30_grados_a_tres_ciclos_por_segundo(self):
        dt = .001
        valores = [c.muestra('risa', i * dt)['pitch'] for i in range(2001)]
        velocidades = [abs(b-a)/dt for a, b in zip(valores, valores[1:])]
        self.assertLessEqual(max(velocidades), 30)
        self.assertAlmostEqual(max(valores), 1.5, places=4)

    def test_reposo_fuera_de_la_linea_de_tiempo(self):
        for nombre, datos in c.CATALOGO.items():
            for tiempo in (-1, datos['duracion'], datos['duracion'] + 1):
                self.assertEqual(c.muestra(nombre, tiempo),
                                 dict(vx=0.0, vy=0.0, z=0.0, yaw=0.0, pitch=0.0, color=(0, 0, 0)))
        with self.assertRaises(ValueError):
            c.muestra('risa', float('nan'))

    def test_waka_alterna_rojo_y_amarillo_como_la_bandera(self):
        tiempo = 60 / 127
        vistos = set()
        for i in range(int(c.CATALOGO['waka']['duracion'] / tiempo)):
            paso = c.muestra('waka', (i + .5) * tiempo)
            self.assertEqual({paso['color'], paso['color_chasis']}, {c.ROJO, c.AMARILLO})
            vistos.add(paso['color'])
        self.assertEqual(vistos, {c.ROJO, c.AMARILLO})
        self.assertNotIn('color_chasis', c.muestra('risa', 1))

    def test_compatibilidad_python38(self):
        ast.parse((MANDO / 'coreografias.py').read_text(encoding='utf-8-sig'), feature_version=(3, 8))


if __name__ == '__main__':
    unittest.main()
