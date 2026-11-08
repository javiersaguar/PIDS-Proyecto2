"""Integración del Conductor con simulacion.py, imágenes sintéticas y reloj real."""
import sys
import tempfile
import time
import unittest
import wave
from unittest.mock import patch
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))
import cv2
import numpy as np
import simulacion


class Integracion(unittest.TestCase):
    def test_control_disparo_caducidad_y_cierre(self):
        from conductor import Conductor
        with tempfile.TemporaryDirectory() as carpeta:
            cv2.imwrite(str(Path(carpeta)/'imagen.jpg'), np.zeros((540,960,3),np.uint8))
            from audio_robot import NOMBRES
            for nombre in NOMBRES:
                with wave.open(str(Path(carpeta)/('mando_'+nombre+'_robot.wav')), 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(48000)
                    w.writeframes(bytes(960))
            parche = patch('audio_robot.CARPETA', Path(carpeta))
            parche.start()
            self.addCleanup(parche.stop)
            simulacion.instalar(carpeta)
            from demo_utils import connect
            d = Conductor(lambda: connect('wifi'), simulado=True)
            d.start()
            try:
                fin = time.monotonic()+8
                while d.foto() is None and not d.estado['error'] and time.monotonic()<fin:
                    time.sleep(.05)
                self.assertIsNone(d.estado['error'])
                self.assertIsNotNone(d.foto())
                with patch('conductor.CONFIG', Path(carpeta)/'config.json'):
                    d.recibir(dict(tipo='activar',config={}))
                d.recibir(dict(tipo='control',mover=[1,1],mirar=[1,0],disparo=True))
                time.sleep(.15)
                self.assertGreater(d.estado['disparos'],0)
                time.sleep(.35)
                self.assertEqual(d.estado['velocidad'],[0,0])
                self.assertFalse(d.config['automatico'])
                tiros=[a for a in d.robot.acciones if a['tipo']=='blaster.fire']
                self.assertTrue(all(a['fire_type']=='ir' for a in tiros))
            finally:
                d.fin.set()
                d.join(25)
            self.assertFalse(d.is_alive())
            self.assertEqual(d.robot.acciones[-1]['tipo'],'cerrar')


if __name__ == '__main__':
    unittest.main()
