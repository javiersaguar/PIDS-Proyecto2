"""Quince minutos de órdenes con reloj simulado, sin esperar ni usar hardware."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))


class Estabilidad(unittest.TestCase):
    def test_quince_minutos_virtuales_con_cortes_y_emotes(self):
        import simulacion
        from conductor import Conductor
        from audio_robot import AudioRobot
        with tempfile.TemporaryDirectory() as carpeta:
            cv2.imwrite(str(Path(carpeta)/'sintetica.jpg'), np.zeros((100,100,3),np.uint8))
            simulacion.instalar(carpeta)
            from demo_utils import connect, Senales
            from demo import Torreta
            r = connect('wifi')
            ahora = [0.]
            d = Conductor(lambda:r,reloj=lambda:ahora[0],simulado=True)
            d.robot = r
            d.estado['listo'] = True
            d.torreta = Torreta(r,reloj=lambda:ahora[0])
            d.senales = Senales(r)
            d.registro = Mock()
            d.audio_robot = AudioRobot(r,simulado=True)
            d.audio_robot.preparado = True
            tiempos = []
            fire = r.blaster.fire
            def disparar(**kw):
                tiempos.append(ahora[0])
                return fire(**kw)
            r.blaster.fire = disparar
            nombres = ['moonwalk','waka','superestrella','risa']
            for i in range(18000):
                ahora[0] = i*.05
                corte = 1100 <= i%1200 < 1120
                if not corte:
                    if i == 0 or i%1200 == 1120:
                        d.emergencia.clear()  # simula el rearme explícito tras cada corte
                    d.recibir(dict(tipo='control',mover=[1,1],mirar=[.2,-.1],disparo=i%20==0))
                    if i%1200==1:
                        d.recibir(dict(tipo='emote',nombre=nombres[(i//1200)%4]))
                d.paso()
                if corte and i%1200 >= 1106:
                    self.assertEqual(d.estado['velocidad'],[0,0])
                    self.assertIsNone(d.baile)
                r.avanzar(.05)
            d.parar()
            d.paso()
            self.assertIsNone(d.audio_robot.actual)
            self.assertTrue(all(b-a >= .3-1e-8 for a,b in zip(tiempos,tiempos[1:])))
            self.assertGreater(len(tiempos),10)
            self.assertTrue(all(a['fire_type']=='ir' for a in r.acciones if a['tipo']=='blaster.fire'))
            self.assertLessEqual(len(d.eventos),100)
            self.assertTrue(any(a['tipo']=='audio.robot' and a['reproducir'] for a in r.acciones))


if __name__ == '__main__':
    unittest.main()
