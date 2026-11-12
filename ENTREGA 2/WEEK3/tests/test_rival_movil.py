"""Control del rival con cinemática del chasis, deriva y sensores simulados."""

from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import math
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'rival'))
import rival_movil as R


class ChasisFalso:
    def __init__(self, rumbo=0.0, deriva_y=0.0, deriva_yaw=0.0, cambia_sentido=False,
                 atascado=False, interrumpir=False, cuantizar=False):
        self.t = self.x = self.y = 0.0
        self.yaw = rumbo
        self.vx = self.vy = self.vz = 0.0
        self.deriva_y, self.deriva_yaw = deriva_y, deriva_yaw
        self.cambia_sentido = cambia_sentido
        self.atascado, self.interrumpir, self.cuantizar = atascado, interrumpir, cuantizar
        self.callback = self.callback_actitud = None
        self.posicion_congelada = self.actitud_congelada = False
        self.ordenes, self.trayectoria = [], []
        self.paradas = 0
        self.al_parar = None

    def publicar(self):
        if self.callback is not None and not self.posicion_congelada:
            x, y = self.x, self.y
            if self.cuantizar:
                x, y = round(x, 2), round(y, 2)
            self.callback((x, y, 0.0))
        if self.callback_actitud is not None and not self.actitud_congelada:
            yaw = (self.yaw + 180) % 360 - 180
            self.callback_actitud((round(yaw, 2) if self.cuantizar else yaw, 0.0, 0.0))

    def sub_position(self, cs=0, freq=20, callback=None):
        self.callback = callback
        self.publicar()
        return True

    def unsub_position(self):
        self.callback = None

    def sub_attitude(self, freq=20, callback=None):
        self.callback_actitud = callback
        self.publicar()
        return True

    def unsub_attitude(self):
        self.callback_actitud = None

    def drive_speed(self, x=0, y=0, z=0, timeout=None):
        anterior = (self.vx, self.vy, self.vz)
        if self.cuantizar:
            x, y, z = round(x, 2), round(y, 2), round(z)
        self.vx, self.vy, self.vz = x, y, z
        self.ordenes.append((x, y, z, timeout))
        self.trayectoria.append((self.x, self.y, self.yaw))
        if anterior != (0, 0, 0) and (x, y, z) == (0, 0, 0):
            self.paradas += 1
            if self.al_parar:
                self.al_parar(self)
        return True

    def dormir(self, dt):
        if self.interrumpir and (self.vx or self.vy or self.vz):
            self.interrumpir = False
            raise KeyboardInterrupt
        self.t += dt
        sentido = math.copysign(1, self.vx) if self.cambia_sentido else 1.0
        lateral = self.deriva_y * sentido if self.vx else 0.0
        giro = self.deriva_yaw * sentido if self.vx else 0.0
        if not self.atascado:
            # Velocidad en ejes del chasis y posición en ejes fijos, como en el SDK.
            r = math.radians(self.yaw)
            self.x += (self.vx * math.cos(r) - (self.vy + lateral) * math.sin(r)) * dt
            self.y += (self.vx * math.sin(r) + (self.vy + lateral) * math.cos(r)) * dt
            self.yaw += (self.vz + giro) * dt
        self.publicar()


class PruebasRivalMovil(unittest.TestCase):
    def ejecutar(self, c, opciones=()):
        robot = SimpleNamespace(chassis=c, battery=Mock(), close=Mock(),
                                set_robot_mode=Mock(return_value=True),
                                get_robot_mode=Mock(return_value='free'))
        self.salida = StringIO()
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(self.salida))
            stack.enter_context(patch.object(R, 'leer_config', return_value={}))
            conectar = stack.enter_context(patch.object(R, 'conectar', return_value=robot))
            salida = stack.enter_context(patch.object(R, 'esperar_salida', return_value='Enter'))
            stack.enter_context(patch.object(R.time, 'sleep', side_effect=c.dormir))
            stack.enter_context(patch.object(R.time, 'monotonic', side_effect=lambda: c.t))
            codigo = R.main(['--conexion', 'wifi', '--modo', 'enter'] + list(opciones))
        return codigo, robot, conectar, salida

    def assert_parado(self, c):
        self.assertEqual(c.ordenes[-1][:3], (0, 0, 0))
        self.assertIsNone(c.callback)
        self.assertIsNone(c.callback_actitud)

    def test_a_delante_y_luego_b_delante_sin_girar(self):
        c = ChasisFalso()
        codigo, robot, conectar, salida = self.ejecutar(c)
        self.assertEqual(codigo, 0, self.salida.getvalue())
        conectar.assert_called_once_with({}, 'wifi')
        salida.assert_called_once()
        robot.set_robot_mode.assert_called_once_with(mode='free')
        robot.close.assert_called_once()
        self.assertAlmostEqual(max(x for x, _, _ in c.trayectoria), 0.65, delta=0.011)
        self.assertLess(abs(c.x), 0.011)
        self.assertTrue(any(vx > 0 for vx, _, _, _ in c.ordenes))
        self.assertTrue(any(vx < 0 for vx, _, _, _ in c.ordenes))
        self.assertTrue(all(vy == 0 and vz == 0 for _, vy, vz, _ in c.ordenes))
        vuelta = next(i for i, (vx, _, _, _) in enumerate(c.ordenes) if vx < 0)
        self.assertEqual(c.ordenes[vuelta - 1][:3], (0, 0, 0))
        self.assert_parado(c)

    def test_compensa_izquierda_en_ida_y_vuelta(self):
        for cambia in (False, True):
            for rumbo in (0.0, 83.3, 179.7, -90.0):
                with self.subTest(cambia=cambia, rumbo=rumbo):
                    c = ChasisFalso(rumbo=rumbo, deriva_y=-0.005, deriva_yaw=-0.6,
                                    cambia_sentido=cambia, cuantizar=True)
                    codigo, _, _, _ = self.ejecutar(c)
                    self.assertEqual(codigo, 0, self.salida.getvalue())
                    r = math.radians(rumbo)
                    laterales = [-x * math.sin(r) + y * math.cos(r) for x, y, _ in c.trayectoria]
                    self.assertLess(max(abs(y) for y in laterales), 0.02)
                    self.assertLess(math.hypot(c.x, c.y), 0.02)
                    self.assertLess(abs(R.diferencia_angular(c.yaw, rumbo)), 1.1)
                    self.assertTrue(any(vy > 0 for _, vy, _, _ in c.ordenes))
                    self.assertTrue(any(vz > 0 for _, _, vz, _ in c.ordenes))

    def test_compensa_derecha(self):
        c = ChasisFalso(deriva_y=0.005, deriva_yaw=0.6, cuantizar=True)
        codigo, _, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertLess(max(abs(y) for _, y, _ in c.trayectoria), 0.02)
        self.assertLess(math.hypot(c.x, c.y), 0.02)
        self.assertTrue(any(vy < 0 for _, vy, _, _ in c.ordenes))
        self.assertTrue(any(vz < 0 for _, _, vz, _ in c.ordenes))

    def test_vuelta_recupera_referencia_original(self):
        c = ChasisFalso()
        def desviar(chasis):
            if chasis.paradas == 1:
                chasis.y += 0.03
                chasis.yaw += 4.0
        c.al_parar = desviar
        codigo, _, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertLess(math.hypot(c.x, c.y), 0.011)
        self.assertLess(abs(c.yaw), 1.0)

    def test_ejes_fijos_y_origen_desplazado(self):
        for rumbo in (45.0, 83.3, 90.0, 180.0, -90.0):
            with self.subTest(rumbo=rumbo):
                c = ChasisFalso(rumbo=rumbo, cuantizar=True)
                c.x, c.y = 2.0, -3.0
                codigo, _, _, _ = self.ejecutar(c)
                self.assertEqual(codigo, 0, self.salida.getvalue())
                r = math.radians(rumbo)
                avances = [(x - 2) * math.cos(r) + (y + 3) * math.sin(r) for x, y, _ in c.trayectoria]
                self.assertAlmostEqual(max(avances), 0.65, delta=0.02)
                self.assertLess(math.hypot(c.x - 2, c.y + 3), 0.02)

    def test_limites_vectoriales_y_del_giro(self):
        c = ChasisFalso(deriva_y=-0.005, deriva_yaw=-0.6, cuantizar=True)
        codigo, _, _, _ = self.ejecutar(c, ['--velocidad', '0.5'])
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertTrue(all(math.hypot(x, y) <= 0.1 + 1e-9 for x, y, _, _ in c.ordenes))
        self.assertTrue(all(abs(z) <= 5 for _, _, z, _ in c.ordenes))
        self.assertTrue(all(t == 0.5 for x, y, z, t in c.ordenes if (x, y, z) != (0, 0, 0)))

    def test_sin_sensores_no_avanza_a_ciegas(self):
        for metodo in ('sub_position', 'sub_attitude'):
            with self.subTest(metodo=metodo):
                c = ChasisFalso()
                with patch.object(c, metodo, return_value=False):
                    codigo, robot, _, _ = self.ejecutar(c)
                self.assertEqual(codigo, 1)
                self.assertTrue(all(o[:3] == (0, 0, 0) for o in c.ordenes))
                self.assert_parado(c)
                robot.close.assert_called_once()

    def test_si_no_llega_el_rumbo_no_se_mueve(self):
        c = ChasisFalso()
        c.actitud_congelada = True
        codigo, _, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 1)
        self.assertTrue(all(o[:3] == (0, 0, 0) for o in c.ordenes))

    def test_sensores_congelados_cancelan_la_vuelta(self):
        for campo in ('posicion_congelada', 'actitud_congelada'):
            with self.subTest(campo=campo):
                c = ChasisFalso()
                original = c.dormir
                def congelar(dt):
                    if c.vx:
                        setattr(c, campo, True)
                    original(dt)
                with patch.object(c, 'dormir', side_effect=congelar):
                    codigo, robot, _, _ = self.ejecutar(c)
                self.assertEqual(codigo, 1)
                self.assertIn('sin actualizarse', self.salida.getvalue())
                self.assertFalse(any(vx < 0 for vx, _, _, _ in c.ordenes))
                self.assert_parado(c)
                robot.close.assert_called_once()

    def test_atasco_cancela_la_vuelta(self):
        c = ChasisFalso(atascado=True)
        codigo, robot, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 1)
        self.assertIn('no ha llegado a tiempo', self.salida.getvalue())
        self.assertFalse(any(vx < 0 for vx, _, _, _ in c.ordenes))
        self.assert_parado(c)
        robot.close.assert_called_once()

    def test_ctrl_c_para_sin_iniciar_la_vuelta(self):
        c = ChasisFalso(interrumpir=True)
        _, robot, _, _ = self.ejecutar(c)
        self.assertFalse(any(vx < 0 for vx, _, _, _ in c.ordenes))
        self.assert_parado(c)
        robot.close.assert_called_once()

    def test_sin_robot_solo_espera_la_salida(self):
        c = ChasisFalso()
        codigo, _, conectar, salida = self.ejecutar(c, ['--sin-robot'])
        self.assertEqual(codigo, 0)
        conectar.assert_not_called()
        salida.assert_called_once()
        self.assertEqual(c.ordenes, [])

    def test_diagnostico_no_cambia_el_control(self):
        normal = ChasisFalso(deriva_y=-0.005, deriva_yaw=-0.6)
        self.ejecutar(normal)
        diagnostico = ChasisFalso(deriva_y=-0.005, deriva_yaw=-0.6)
        codigo, robot, _, _ = self.ejecutar(diagnostico, ['--diagnostico'])
        self.assertEqual(codigo, 0)
        robot.get_robot_mode.assert_called_once()
        self.assertEqual(normal.ordenes, diagnostico.ordenes)
        self.assertIn('lateral=', self.salida.getvalue())
        self.assertEqual(self.salida.getvalue().count('Final del tramo:'), 2)

    def test_wrap_de_yaw_al_cruzar_180(self):
        c = ChasisFalso(rumbo=179.7, deriva_yaw=0.6, cuantizar=True)
        codigo, _, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertLess(abs(R.diferencia_angular(c.yaw, 179.7)), 1.1)
        self.assertTrue(all(abs(z) <= 5 for _, _, z, _ in c.ordenes))

    def test_distancia_negativa_invierte_el_orden_sin_girar(self):
        c = ChasisFalso()
        codigo, _, _, _ = self.ejecutar(c, ['--distancia', '-0.65'])
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertLess(next(vx for vx, _, _, _ in c.ordenes if vx), 0)
        self.assertTrue(any(vx > 0 for vx, _, _, _ in c.ordenes))
        self.assertLess(abs(c.x), 0.011)
        self.assertTrue(all(yaw == 0 for _, _, yaw in c.trayectoria))

    def test_false_del_sdk_no_es_rechazo_de_un_mensaje_sin_ack(self):
        c = ChasisFalso()
        original = c.drive_speed
        def enviar_sin_ack(x=0, y=0, z=0, timeout=None):
            original(x, y, z, timeout)
            return False
        with patch.object(c, 'drive_speed', side_effect=enviar_sin_ack):
            codigo, robot, _, _ = self.ejecutar(c)
        self.assertEqual(codigo, 0, self.salida.getvalue())
        self.assertLess(math.hypot(c.x, c.y), 0.011)
        self.assert_parado(c)
        robot.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
