"""Pruebas de límites y vigilancia sin robot físico."""
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from conductor import Conductor, control, configuracion


class Seguridad(unittest.TestCase):
    def test_diagonal_y_limites(self):
        mover, mirar, disparo = control(dict(mover=[8,8], mirar=[9,-9], disparo=True))
        self.assertLessEqual(sum(v*v for v in mover), 1.000001)
        self.assertEqual(mirar, [1,-1])
        self.assertEqual(configuracion(dict(velocidad=50, angular=90)), dict(velocidad=.5, angular=30))
        with self.assertRaises(ValueError):
            control(dict(mover=[float('nan'),0],mirar=[0,0],disparo=True))

    def test_caducidad_para_y_desarma(self):
        d = Conductor(lambda: None, reloj=lambda: 2)
        d.robot, d.torreta = Mock(), Mock()
        d.torreta.leer.return_value = (0,0)
        d.velocidades = Mock()
        d.ultimo = 1
        d.config['automatico'] = True
        d.emergencia.clear()
        d.paso()
        d.velocidades.assert_called_once_with([0,0],[0,0])
        self.assertFalse(d.config['automatico'])

    def test_config_rechaza_fps_y_audio_bloqueante(self):
        for dato in [dict(modo='fps'),dict(audio='robot')]:
            with self.assertRaises(ValueError):
                configuracion(dato)


if __name__ == '__main__':
    unittest.main()
