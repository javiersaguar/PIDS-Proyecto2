"""Pruebas de recorrido.py: los movimientos calculados llevan el robot a los puntos del plano."""

import math
import os
import sys
import unittest

WEEK3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WEEK3)

import recorrido as R  # noqa: E402


def ejecutar(movimientos, rumbo_inicial):
    """Posición en el plano (x derecha, y abajo) y rumbo tras ejecutar los movimientos del chasis.

    Mismo modelo que el SDK: x adelante, y a la derecha, z > 0 gira a la izquierda;
    cada movimiento se traslada con el rumbo de partida y después gira.
    """
    x, y, rumbo = 0.0, 0.0, rumbo_inicial
    for adelante, derecha, z in movimientos:
        r = math.radians(rumbo)
        # derecha del robot en el plano (y hacia abajo): rumbo + 90
        x += adelante * math.cos(r) + derecha * math.cos(r + math.pi / 2)
        y += adelante * math.sin(r) + derecha * math.sin(r + math.pi / 2)
        rumbo -= z
    return x, y, R.normalizar(rumbo)


PLANO = [
    dict(nombre='P1', punto=(1.0, 0.0), rivales=[(2.5, 0.5)]),
    dict(nombre='P2', punto=(1.0, 1.5), mirar=0, rivales=[(2.5, 2.0)]),
    dict(nombre='P3', punto=(2.0, 2.5), por=[(1.0, 2.5)]),
]


class PruebasRecorrido(unittest.TestCase):
    def comprobar_llegada(self, rumbo_inicial, girar):
        paradas = R.paradas_desde_plano(rumbo_inicial, PLANO, girar=girar)
        hechos = []
        for p, plano in zip(paradas, PLANO):
            hechos += p['movimientos']
            x, y, rumbo = ejecutar(hechos, rumbo_inicial)
            self.assertAlmostEqual(x, plano['punto'][0], places=2)
            self.assertAlmostEqual(y, plano['punto'][1], places=2)
            self.assertAlmostEqual(rumbo, p['rumbo'], delta=0.2)
        return paradas

    def test_girando_llega_a_cada_parada(self):
        for rumbo in (0, 90, -90, 180, 37):
            self.comprobar_llegada(rumbo, girar=True)

    def test_en_diagonal_llega_sin_girar(self):
        paradas = self.comprobar_llegada(90, girar=False)
        # Solo gira donde se pide un rumbo al llegar (mirar); el resto, en diagonal
        for p, plano in zip(paradas, PLANO):
            giros = [z for _, _, z in p['movimientos'] if z]
            self.assertEqual(len(giros), 1 if plano.get('mirar') is not None else 0, p['nombre'])

    def test_giro_a_la_derecha_es_z_negativo(self):
        movimientos, rumbo = R.tramo((0, 0), (0, 1), 0)    # mirando a la derecha, ir hacia abajo
        self.assertEqual(movimientos, [(0, 0, -90.0), (1.0, 0, 0)])
        self.assertAlmostEqual(rumbo, 90)

    def test_barrido_mira_al_rival(self):
        # Rival abajo a la derecha visto mirando a la derecha: yaw > 0 (derecha), como el gimbal
        yaws = R.barrido_hacia((0, 0), 0, [(1, 1)], abanico=30)
        self.assertEqual(yaws, [45.0, 15.0, 75.0])
        # Rival detrás: el yaw se queda en ±180, dentro del rango del gimbal
        self.assertAlmostEqual(abs(R.barrido_hacia((0, 0), 0, [(-1, 0)])[0]), 180)

    def test_objetivos_y_barrido_por_defecto(self):
        paradas = R.paradas_desde_plano(0, PLANO)
        self.assertEqual([p['objetivos'] for p in paradas], [1, 1, None])
        self.assertEqual(paradas[2]['barrido'], [0, 60, 120, 180, -120, -60])

    def test_circuito_carga_el_plano(self):
        import circuito
        self.assertEqual(len(circuito.PARADAS), len(circuito.PLANO))
        for p in circuito.PARADAS:
            self.assertTrue({'nombre', 'movimientos', 'barrido', 'pitch', 'objetivos'} <= set(p))


if __name__ == '__main__':
    unittest.main()
