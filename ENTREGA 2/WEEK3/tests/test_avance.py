"""Pruebas de demo_utils.avanzar: avance con drive_speed medido con la odometría."""

import os
import sys
import unittest

WEEK3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WEEK3)

import simulacion  # noqa: E402

simulacion.instalar(None)   # el SDK simulado basta: avanzar solo usa el chasis
import demo_utils as U  # noqa: E402


class ChasisFalso:
    """Chasis que integra la velocidad mandada con un reloj simulado, con deriva lateral opcional."""

    def __init__(self, deriva=0.0, con_odometria=True):
        self.t, self.x, self.y = 0.0, 0.0, 0.0
        self.v = (0.0, 0.0)
        self.deriva = deriva
        self.con_odometria = con_odometria
        self.callback = None
        self.ordenes = []

    # SDK
    def sub_position(self, cs=0, freq=20, callback=None):
        if not self.con_odometria:
            raise AttributeError('sin odometría')
        self.callback = callback
        return True

    def unsub_position(self):
        self.callback = None

    def drive_speed(self, x=0, y=0, z=0, timeout=None):
        self.ordenes.append((x, y, z, timeout))
        self.v = (x, y)

    # reloj simulado
    def reloj(self):
        return self.t

    def dormir(self, dt):
        self.t += dt
        self.x += self.v[0] * dt
        self.y += (self.v[1] + (self.deriva if self.v != (0, 0) else 0.0)) * dt
        if self.callback is not None:
            self.callback((self.x, self.y, 0.0))


class RobotFalso:
    def __init__(self, chasis):
        self.chassis = chasis


def avanzar(chasis, x, y, v=0.4):
    return U.avanzar(RobotFalso(chasis), x, y, v, dormir=chasis.dormir, reloj=chasis.reloj)


class PruebasAvance(unittest.TestCase):
    def test_llega_a_2_85_m_y_se_para(self):
        c = ChasisFalso()
        medido = avanzar(c, 2.85, 0)
        self.assertAlmostEqual(c.x, 2.85, delta=0.02)
        self.assertAlmostEqual(medido[0], 2.85, delta=0.02)
        self.assertEqual(c.ordenes[-1][:3], (0, 0, 0))            # acaba parado
        self.assertLess(c.t, 2.85 / 0.4 + 3)                       # a la velocidad pedida, no a 0,06 m/s

    def test_2_85_m_en_unos_6_s_a_la_velocidad_maxima(self):
        c = ChasisFalso()
        avanzar(c, 2.85, 0, v=0.5)
        self.assertAlmostEqual(c.x, 2.85, delta=0.02)
        self.assertLess(c.t, 6.5)

    def test_nunca_pasa_de_la_velocidad_maxima(self):
        c = ChasisFalso(deriva=0.05)
        avanzar(c, 2.0, 1.0, v=3.0)                                # se pide de más: se recorta a 0,5
        for x, y, _, _ in c.ordenes:
            self.assertLessEqual((x * x + y * y) ** 0.5, U.VEL_XY_MAX + 1e-9)

    def test_cada_orden_lleva_tiempo_maximo(self):
        # Si el programa se cuelga, el robot se para solo
        c = ChasisFalso()
        avanzar(c, 1.0, 0)
        self.assertTrue(all(t == 0.5 for x, y, _, t in c.ordenes if (x, y) != (0, 0)))

    def test_corrige_la_deriva_lateral(self):
        c = ChasisFalso(deriva=0.03)
        avanzar(c, 2.85, 0)
        self.assertLess(abs(c.y), 0.05)

    def test_en_diagonal(self):
        c = ChasisFalso()
        avanzar(c, 1.0, -1.0)
        self.assertAlmostEqual(c.x, 1.0, delta=0.02)
        self.assertAlmostEqual(c.y, -1.0, delta=0.02)

    def test_sin_odometria_no_se_mueve(self):
        c = ChasisFalso(con_odometria=False)
        self.assertIsNone(avanzar(c, 1.0, 0))
        self.assertEqual(c.ordenes, [])

    def test_si_no_avanza_da_error_y_se_para(self):
        c = ChasisFalso()
        c.drive_speed = lambda x=0, y=0, z=0, timeout=None: c.ordenes.append((x, y, z, timeout))  # atascado
        with self.assertRaises(RuntimeError):
            avanzar(c, 1.0, 0)
        self.assertEqual(c.ordenes[-1][:3], (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
