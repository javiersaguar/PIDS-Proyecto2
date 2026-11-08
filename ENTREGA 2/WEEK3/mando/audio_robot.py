"""Audios precargados y órdenes de reproducción/parada con espera acotada."""
import wave
from pathlib import Path

NOMBRES = ('moonwalk', 'waka', 'superestrella', 'risa')
SILENCIO = .3
CARPETA = Path(__file__).resolve().parent.parent / 'audio' / 'propios'


def comprobar_audio(ruta):
    with wave.open(str(ruta), 'rb') as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(),
                audio.getcomptype()) != (1, 2, 48000, 'NONE'):
            raise ValueError('Formato incorrecto de ' + str(ruta))
        return audio.getnframes() / 48000


class AudioRobot:
    """Lo usa el Conductor. El FTP solo se hace con los controles desarmados."""
    def __init__(self, robot, simulado=False, protocolo=None):
        self.robot = robot
        self.simulado = simulado
        if protocolo is None and not simulado:
            from robomaster import protocol
            protocolo = protocol
        self.protocolo = protocolo
        self.ids = {nombre: 0xE0 + 6 + i for i, nombre in enumerate(NOMBRES)}
        self.actual = None
        self.secuencia = 0
        self.preparado = False

    def preparar(self, carpeta=None, progreso=lambda mensaje: None):
        self.preparado = False
        carpeta = CARPETA if carpeta is None else Path(carpeta)
        rutas = [(n, carpeta / ('mando_' + n + '_robot.wav')) for n in NOMBRES]
        for _, ruta in rutas:
            comprobar_audio(ruta)
        if not self.simulado:
            # Reutiliza la conexión FTP del SDK. Su método upload captura las
            # excepciones, por eso se usa storbinary y se comprueba la respuesta.
            ftp = self.robot._ftp._ftp
            timeout = ftp.timeout
            timeout_socket = ftp.sock.gettimeout()
            try:
                ftp.timeout = 3
                ftp.sock.settimeout(3)
                for i, (nombre, ruta) in enumerate(rutas):
                    progreso('Cargando audio ' + nombre)
                    with ruta.open('rb') as archivo:
                        respuesta = ftp.storbinary('STOR /python/sdk_audio_%d.wav' % (6+i), archivo)
                    if not respuesta.startswith('226'):
                        raise RuntimeError('El robot no confirmó la carga de ' + nombre)
            finally:
                ftp.timeout = timeout
                ftp.sock.settimeout(timeout_socket)
        self.preparado = True

    def _enviar(self, nombre, reproducir):
        if self.simulado:
            self.robot.acciones.append(dict(tipo='audio.robot', nombre=nombre,
                                            reproducir=reproducir))
            return
        proto = self.protocolo.ProtoPlaySound()
        self.secuencia = self.secuencia % 255 + 1
        proto._action_id = self.secuencia
        proto._sound_id = self.ids[nombre]
        proto._play_ctrl = 1 if reproducir else 0
        proto._play_times = 1
        msg = self.protocolo.Msg(self.robot.client.hostbyte,
                                self.protocolo.host2byte(9, 0), proto)
        respuesta = self.robot.client.send_sync_msg(msg, timeout=.1)
        if respuesta is None:
            raise RuntimeError('Sin confirmación del audio del robot')
        estado = respuesta.get_proto()
        if estado._retcode != 0 or getattr(estado, '_accept', 0) == 1:
            raise RuntimeError('El robot rechazó la orden de audio')

    def reproducir(self, nombre):
        if not self.preparado or nombre not in self.ids:
            raise RuntimeError('El audio del emote no está preparado')
        self.parar()
        # Guardar el nombre antes de enviar permite intentar parar si se pierde el ACK.
        self.actual = nombre
        self._enviar(nombre, True)

    def parar(self):
        if self.actual is not None:
            nombre = self.actual
            self._enviar(nombre, False)
            self.actual = None
