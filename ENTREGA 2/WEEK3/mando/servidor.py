"""Servidor local de vídeo y control. Compatible con Python 3.8."""
import argparse
import asyncio
import json
import sys
import time
import atexit
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))
sys.path.insert(0, str(BASE))
from aiohttp import web
import cv2


def crear_app(conductor):
    app = web.Application(client_max_size=16384)
    propietario = None

    async def indice(request):
        return web.FileResponse(BASE / 'web' / 'index.html')

    async def prueba_mando(request):
        return web.FileResponse(BASE / 'web' / 'prueba_mando.html')

    async def salud(request):
        estado = conductor.instantanea()
        return web.json_response({k: estado.get(k) for k in
                                  ('listo', 'error', 'aviso', 'detector', 'ms_detector')})

    async def video(request):
        respuesta = web.StreamResponse(headers={
            'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
            'Cache-Control': 'no-store'})
        await respuesta.prepare(request)
        ultimo = None
        try:
            while True:
                foto = conductor.foto()
                if foto is not None and foto[0] != ultimo:
                    ultimo, imagen = foto
                    bgr = cv2.cvtColor(cv2.resize(imagen, (960, 540)), cv2.COLOR_RGB2BGR)
                    ok, jpeg = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok:
                        await asyncio.wait_for(respuesta.write(
                            b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
                            jpeg.tobytes() + b'\r\n'), timeout=1)
                await asyncio.sleep(.05)
        except (ConnectionError, asyncio.TimeoutError, asyncio.CancelledError):
            pass
        return respuesta

    async def ws(request):
        nonlocal propietario
        # Impide que páginas de otros orígenes controlen el servidor.
        origen = request.headers.get('Origin')
        if origen and origen != request.scheme + '://' + request.host:
            raise web.HTTPForbidden()
        if propietario is not None:
            raise web.HTTPConflict(text='Ya hay una sesión de control')
        socket = web.WebSocketResponse(max_msg_size=16384, heartbeat=5)
        await socket.prepare(request)
        propietario = socket
        conductor.parar()

        async def estado():
            ultimo_estado = 0
            while not socket.closed:
                if time.monotonic() - ultimo_estado >= .5:
                    await socket.send_json(dict(tipo='estado', **conductor.instantanea()))
                    ultimo_estado = time.monotonic()
                while conductor.eventos:
                    await socket.send_json(conductor.eventos.popleft())
                await asyncio.sleep(.025)

        envio = asyncio.create_task(estado())
        try:
            async for mensaje in socket:
                if mensaje.type == web.WSMsgType.TEXT:
                    try:
                        datos = json.loads(mensaje.data)
                        if not isinstance(datos, dict):
                            raise ValueError('Mensaje inválido')
                        conductor.recibir(datos)
                    except (ValueError, TypeError, KeyError, OverflowError) as e:
                        conductor.parar()
                        await socket.send_json(dict(tipo='error', mensaje=str(e)))
        finally:
            conductor.parar()
            propietario = None
            envio.cancel()
            await asyncio.gather(envio, return_exceptions=True)
        return socket

    async def audio(request):
        nombre = request.match_info['nombre']
        if nombre not in ('moonwalk', 'waka', 'risa', 'superestrella', 'scar', 'motor'):
            raise web.HTTPNotFound()
        ruta = BASE.parent / 'audio' / 'propios' / ('mando_' + nombre + '.ogg')
        if not ruta.is_file():
            raise web.HTTPNotFound(text='Prepare los audios con audio/preparar_emotes.py')
        return web.FileResponse(ruta)

    async def limpiar(app):
        conductor.parar()
        conductor.fin.set()
        await asyncio.get_event_loop().run_in_executor(None, conductor.join, 25)

    app.router.add_get('/', indice)
    app.router.add_get('/video', video)
    app.router.add_get('/ws', ws)
    app.router.add_get('/salud', salud)
    app.router.add_get('/audio/{nombre}.ogg', audio)
    app.router.add_static('/web/', BASE / 'web')
    app.router.add_get('/prueba_mando.html', prueba_mando)
    app.on_cleanup.append(limpiar)
    return app


def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--simulacion', metavar='CARPETA')
    p.add_argument('--sin-mover', action='store_true')
    p.add_argument('--detector', choices=['auto', 'cpu', 'gpu'], default='auto')
    p.add_argument('--detector-real', action='store_true',
                   help='usar inferencia real también con imágenes de la simulación')
    p.add_argument('--conexion', choices=['auto', 'wifi', 'networking'], default='auto')
    p.add_argument('--puerto', type=int, default=8765)
    args = p.parse_args()
    from proceso_detector import iniciar, cerrar, disponible
    proceso_gpu = iniciar() if args.detector == 'auto' and (not args.simulacion or args.detector_real) else None
    if proceso_gpu is not None:
        atexit.register(cerrar, proceso_gpu)
    if args.simulacion:
        import simulacion
        simulacion.instalar(args.simulacion)
    from demo_utils import connect
    from conductor import Conductor
    conductor = Conductor(lambda: connect('networking' if args.conexion == 'auto' else args.conexion,
                                         auto=args.conexion == 'auto'),
                          sin_mover=args.sin_mover, simulado=bool(args.simulacion))
    from deteccion import Detector
    def proveedor():
        foto = conductor.foto()
        return None if foto is None else (foto[1], foto[0])
    preferencia = args.detector
    if preferencia == 'auto':
        preferencia = 'gpu' if disponible() else 'cpu'
    conductor.config['detector'] = preferencia
    detector = Detector(proveedor, conductor.publicar,
                        simulado=bool(args.simulacion) and not args.detector_real)
    detector.configurar(conductor.config)
    async def detener_detector(app):
        await asyncio.get_running_loop().run_in_executor(None, detector.cerrar)
        await asyncio.get_running_loop().run_in_executor(None, cerrar, proceso_gpu)
    app = crear_app(conductor)
    app.on_cleanup.append(detener_detector)
    original_recibir = conductor.recibir
    def recibir(datos):
        original_recibir(datos)
        detector.configurar(conductor.config)
    conductor.recibir = recibir
    conductor.start()
    detector.start()
    web.run_app(app, host='127.0.0.1', port=args.puerto)


if __name__ == '__main__':
    main()
