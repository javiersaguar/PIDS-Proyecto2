"""Comprueba transporte de audio con el protocolo del SDK y sin robot."""
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))
from robomaster import protocol as protocolo_real
from audio_robot import AudioRobot, comprobar_audio, NOMBRES


class Audio(unittest.TestCase):
    def robot(self):
        robot = Mock()
        robot.client.hostbyte = 0xC9
        robot.client.send_sync_msg.return_value.get_proto.return_value = SimpleNamespace(_retcode=0,_accept=0)
        return robot

    def test_reproducir_y_parar_serializa_ordenes_acotadas(self):
        r = self.robot()
        audio = AudioRobot(r, protocolo=protocolo_real)
        audio.preparado = True
        audio.reproducir('risa')
        audio.parar()
        llamadas = r.client.send_sync_msg.call_args_list
        self.assertEqual(len(llamadas), 2)
        for llamada, control in zip(llamadas, (1, 0)):
            msg = llamada.args[0]
            contenido = msg.get_proto().pack_req()
            self.assertEqual(contenido[6], control)
            self.assertEqual(msg.get_proto()._sound_id, 0xE9)
            self.assertEqual(llamada.kwargs['timeout'], .1)
        self.assertIsNone(audio.actual)
        r.play_audio.assert_not_called()
        r.action_dispatcher.send_action.assert_not_called()

    def test_fallo_de_ack_mantiene_nombre_para_cancelar(self):
        r = self.robot()
        r.client.send_sync_msg.return_value = None
        audio = AudioRobot(r, protocolo=protocolo_real)
        audio.preparado = True
        with self.assertRaisesRegex(RuntimeError, 'Sin confirmación'):
            audio.reproducir('waka')
        self.assertEqual(audio.actual, 'waka')

    def test_rechazo_y_respuesta_final_del_sdk(self):
        for aceptacion, rechaza in [(1, True), (2, False)]:
            r = self.robot()
            r.client.send_sync_msg.return_value.get_proto.return_value = SimpleNamespace(
                _retcode=0, _accept=aceptacion)
            audio = AudioRobot(r, protocolo=protocolo_real)
            audio.preparado = True
            if rechaza:
                with self.assertRaisesRegex(RuntimeError, 'rechazó'):
                    audio.reproducir('risa')
            else:
                audio.reproducir('risa')

    def test_precarga_ftp_una_vez_y_propaga_fallos(self):
        with tempfile.TemporaryDirectory() as ruta:
            carpeta=Path(ruta)
            for n in NOMBRES:
                with wave.open(str(carpeta/('mando_'+n+'_robot.wav')),'wb') as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
                    w.writeframes(bytes(960))
            r=self.robot()
            transporte=r._ftp._ftp
            transporte.timeout=10
            transporte.sock.gettimeout.return_value=10
            transporte.storbinary.return_value='226 Transfer complete'
            audio=AudioRobot(r,protocolo=protocolo_real)
            audio.preparar(carpeta)
            self.assertTrue(audio.preparado)
            self.assertEqual(transporte.storbinary.call_count,4)
            transporte.sock.settimeout.assert_any_call(3)
            self.assertEqual(transporte.timeout,10)
            transporte.storbinary.side_effect=OSError('FTP caído')
            audio=AudioRobot(r,protocolo=protocolo_real)
            with self.assertRaises(OSError):
                audio.preparar(carpeta)
            self.assertFalse(audio.preparado)
            self.assertEqual(transporte.timeout,10)

    def test_formato_incorrecto_se_rechaza(self):
        with tempfile.TemporaryDirectory() as ruta:
            archivo=Path(ruta)/'mal.wav'
            with wave.open(str(archivo),'wb') as w:
                w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100)
                w.writeframes(bytes(100))
            with self.assertRaises(ValueError):
                comprobar_audio(archivo)

    def test_emote_se_cancela_al_caducar_control(self):
        import simulacion
        simulacion.instalar(str(BASE.parent))
        from conductor import Conductor
        ahora=[1.]
        r=Mock()
        r.acciones=[]
        d=Conductor(lambda:r,reloj=lambda:ahora[0])
        d.robot=r
        d.estado['listo']=True
        d.torreta=Mock()
        d.torreta.leer.return_value=(0,0)
        d.audio_robot=AudioRobot(r,simulado=True)
        d.audio_robot.preparado=True
        d.emergencia.clear()
        d.recibir(dict(tipo='control',mover=[0,0],mirar=[0,0],disparo=False))
        d.recibir(dict(tipo='emote',nombre='risa'))
        d.paso()
        self.assertEqual(r.acciones[-1],dict(tipo='audio.robot',nombre='risa',reproducir=True))
        ahora[0]+= .31
        d.paso()
        self.assertEqual(r.acciones[-1],dict(tipo='audio.robot',nombre='risa',reproducir=False))
        self.assertIsNone(d.baile)
        self.assertFalse(d.config['automatico'])


if __name__=='__main__':
    unittest.main()
