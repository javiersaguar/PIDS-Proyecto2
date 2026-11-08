"""Rearme tras los bailes, disparos sin confirmar, puntería automática, LED y giros."""
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))
import simulacion

simulacion.instalar(str(BASE.parent))
from conductor import Conductor, hacia_camara, leer_config, configuracion


def preparado(ahora):
    from demo_utils import connect, Senales
    from demo import Torreta
    from audio_robot import AudioRobot
    r = connect('wifi')
    d = Conductor(lambda: r, reloj=lambda: ahora[0], simulado=True)
    d.robot, d.registro = r, Mock()
    d.torreta = Torreta(r, reloj=lambda: ahora[0])
    d.senales = Senales(r)
    d.audio_robot = AudioRobot(r, simulado=True)
    d.audio_robot.preparado = True
    d.estado['listo'] = True
    d.emergencia.clear()
    d.estado['armado'] = True
    return d, r


def controlar(d, ahora, **orden):
    datos = dict(tipo='control', mover=[0, 0], mirar=[0, 0], disparo=False)
    datos.update(orden)
    d.recibir(datos)
    d.paso()
    ahora[0] += .05


class Correcciones(unittest.TestCase):
    def test_tras_el_baile_siguen_armados_los_controles(self):
        ahora = [0.]
        d, r = preparado(ahora)
        controlar(d, ahora)
        d.recibir(dict(tipo='emote', nombre='risa'))
        while ahora[0] < 5:
            controlar(d, ahora)
        self.assertIsNone(d.baile)
        self.assertFalse(d.emergencia.is_set())
        self.assertTrue(any(e['tipo'] == 'fin_emote' for e in d.eventos))
        controlar(d, ahora, mover=[1, 0])
        self.assertGreater(d.estado['velocidad'][0], 0)

    def test_la_caducidad_avisa_al_navegador(self):
        ahora = [0.]
        d, r = preparado(ahora)
        controlar(d, ahora)
        ahora[0] += .5
        d.paso()
        self.assertFalse(d.instantanea()['armado'])
        self.assertEqual([e['tipo'] for e in d.eventos].count('desarmado'), 1)
        d.paso()
        self.assertEqual([e['tipo'] for e in d.eventos].count('desarmado'), 1)

    def test_un_disparo_sin_confirmar_no_corta_la_sesion(self):
        ahora = [0.]
        d, r = preparado(ahora)
        r.blaster.fire = Mock(return_value=False)
        controlar(d, ahora, disparo=True)
        self.assertEqual(d.estado['sin_confirmar'], 1)
        self.assertEqual(d.estado['disparos'], 0)
        self.assertTrue(any(e['tipo'] == 'aviso' for e in d.eventos))
        r.blaster.fire = Mock(side_effect=RuntimeError('sin ACK'))
        ahora[0] += .3
        controlar(d, ahora, disparo=True)
        self.assertEqual(d.estado['sin_confirmar'], 2)
        self.assertFalse(d.emergencia.is_set())

    def test_automatico_solo_si_la_torreta_no_se_ha_movido(self):
        ahora = [10.]
        d, r = preparado(ahora)
        d.config['automatico'] = True
        d.torreta.leer()
        caja = dict(boxes=[[400, 200, 560, 340]], scores=[.99], width=960, height=540,
                    instante=ahora[0], image=None)
        self.assertTrue(d.blanco(caja, ahora[0] + .2))
        self.assertFalse(d.blanco(caja, ahora[0] + .6))          # imagen demasiado vieja
        d.torreta.yaw += 5                                        # la torreta ya se movió
        d.torreta.leer()
        self.assertFalse(d.blanco(caja, ahora[0] + .2))

    def test_led_solo_cuando_cambian(self):
        ahora = [0.]
        d, r = preparado(ahora)
        d.senales = Mock()
        for _ in range(20):
            controlar(d, ahora, mover=[1, 0])
        d.senales.estado.assert_called_once_with('moviendo', parpadeo=False)
        controlar(d, ahora)
        d.recibir(dict(tipo='emote', nombre='risa'))
        inicio = len(r.acciones)
        while ahora[0] < 5:
            controlar(d, ahora)
        leds = [a for a in r.acciones[inicio:] if a['tipo'] == 'led']
        # Risa alterna amarillo y apagado a 10 Hz: unas 32 órdenes en 3,15 s, no 126.
        self.assertGreater(len(leds), 5)
        self.assertLess(len(leds), 40)

    def test_movimiento_hacia_la_camara_y_giro_del_chasis(self):
        self.assertTrue(all(math.isclose(a, b, abs_tol=1e-9)
                            for a, b in zip(hacia_camara([1, 0], 90), [0, 1])))
        self.assertTrue(all(math.isclose(a, b, abs_tol=1e-9)
                            for a, b in zip(hacia_camara([0, 1], 90), [-1, 0])))
        ahora = [0.]
        d, r = preparado(ahora)
        d.robot.chassis.drive_speed = Mock()
        d.torreta.yaw = 90
        controlar(d, ahora, mover=[1, 0], girar=1)
        kw = d.robot.chassis.drive_speed.call_args.kwargs
        self.assertAlmostEqual(kw['x'], 0, places=6)
        self.assertAlmostEqual(kw['y'], .5, places=6)
        self.assertEqual(kw['z'], -30)
        self.assertLessEqual(math.hypot(kw['x'], kw['y']), .5 + 1e-9)
        d.config['relativo_camara'] = False
        controlar(d, ahora, mover=[1, 0])
        self.assertAlmostEqual(d.robot.chassis.drive_speed.call_args.kwargs['x'], .5)

    def test_plantilla_de_ajustes(self):
        with patch('conductor.CONFIG', BASE / 'no_existe.json'):
            datos = leer_config()
        self.assertTrue(configuracion(datos)['relativo_camara'])


if __name__ == '__main__':
    unittest.main()
