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


class ChasisQueGira(ChasisFalso):
    """Chasis con IMU que se gira solo `giro` º/s al avanzar (como el del laboratorio).

    `convenio` = 1: la IMU cuenta el yaw a la derecha y drive_speed gira a la izquierda con
    z > 0 (lo supuesto); -1: al revés, para comprobar que la corrección se invierte sola.
    """

    def __init__(self, giro=0.0, yaw=0.0, convenio=1, **kw):
        super().__init__(**kw)
        self.giro, self.yaw, self.convenio = giro, yaw, convenio
        self.z, self.callback_imu = 0.0, None

    def sub_attitude(self, freq=20, callback=None):
        self.callback_imu = callback
        callback((self.yaw, 0.0, 0.0))
        return True

    def unsub_attitude(self):
        self.callback_imu = None

    def drive_speed(self, x=0, y=0, z=0, timeout=None):
        super().drive_speed(x, y, z, timeout)
        self.z = z

    def dormir(self, dt):
        super().dormir(dt)
        moviendo = self.v != (0, 0)
        self.yaw += (self.giro if moviendo else 0.0) * dt - self.convenio * self.z * dt
        if self.callback_imu is not None:
            self.callback_imu((self.yaw, 0.0, 0.0))


class PruebasRumbo(unittest.TestCase):
    def setUp(self):
        U.RUMBO.update(activo=True, referencia=None, signo=None, desvio=None, maximo=0.0, yaw_fin=None, t_fin=None)

    def test_sin_corregir_se_desviaria(self):
        c = ChasisQueGira(giro=3.0)
        U.RUMBO['activo'] = False                       # como antes del 11/11
        avanzar(c, 2.85, 0)
        self.assertGreater(abs(c.yaw), 10)

    def test_mide_el_sentido_y_mantiene_el_rumbo(self):
        for convenio in (1, -1):                        # sirva el convenio de signos que sirva
            with self.subTest(convenio=convenio):
                self.setUp()
                c = ChasisQueGira(giro=3.0, convenio=convenio)
                avanzar(c, 2.85, 0)
                self.assertEqual(U.RUMBO['signo'], convenio)
                self.assertLess(abs(c.yaw), 2.5)
                self.assertAlmostEqual(c.x, 2.85, delta=0.02)
                self.assertTrue(U.RUMBO['activo'])

    def test_el_giro_de_prueba_se_hace_una_sola_vez(self):
        c = ChasisQueGira(giro=-2.0)
        avanzar(c, 1.0, 0)
        avanzar(c, 1.0, 0)
        pruebas = [o for o in c.ordenes if o[2] == U.GIRO_PRUEBA]
        self.assertEqual(len(pruebas), 1)

    def test_el_rumbo_se_conserva_entre_rectas_seguidas_y_se_endereza(self):
        c = ChasisQueGira()
        avanzar(c, 1.0, 0)                              # fija la referencia en 0
        c.yaw = 8.0                                     # se gira justo después (sin pausa larga)
        avanzar(c, 1.0, 0)
        self.assertLess(abs(c.yaw), U.TOLERANCIA_RUMBO)

    def test_la_deriva_de_la_imu_en_una_parada_no_gira_el_robot(self):
        c = ChasisQueGira()
        avanzar(c, 1.0, 0)
        c.t += 60                                       # parada de un minuto
        c.yaw += 8.0                                    # la IMU deriva 8 grados sin que el chasis gire
        ordenes = len(c.ordenes)
        avanzar(c, 1.0, 0)
        self.assertTrue(all(abs(o[2]) < 2 for o in c.ordenes[ordenes:]))   # ni endereza ni gira 8 grados
        self.assertAlmostEqual(c.yaw, 8.0, delta=0.5)

    def test_si_la_imu_no_responde_no_corrige(self):
        c = ChasisQueGira(giro=3.0)
        c.convenio = 0                                  # el giro de prueba no cambia el yaw
        avanzar(c, 2.85, 0)
        self.assertEqual(U.RUMBO['signo'], 0)
        self.assertTrue(all(o[2] == 0 for o in c.ordenes if o[2] != U.GIRO_PRUEBA))

    def test_si_el_desvio_se_dispara_deja_de_corregir(self):
        c = ChasisQueGira(giro=60.0)                    # gira mucho más de lo que se puede corregir
        avanzar(c, 2.85, 0)
        self.assertFalse(U.RUMBO['activo'])
        self.assertAlmostEqual(c.x, 2.85, delta=0.05)

    def test_tras_un_giro_buscado_el_rumbo_nuevo_es_el_recto(self):
        U.RUMBO.update(referencia=0.0, signo=1)
        U.reiniciar_rumbo()
        c = ChasisQueGira(yaw=90.0)
        avanzar(c, 1.0, 0)
        self.assertAlmostEqual(c.yaw, 90.0, delta=0.5)


if __name__ == '__main__':
    unittest.main()
