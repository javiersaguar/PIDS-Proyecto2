"""Detector local independiente del SDK. Arrancar con Python 3.11 y CUDA 12.8.

Funciona con la RTX 5070 del portátil y con la RTX 3060 de los ordenadores del laboratorio.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

WEEK3 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEEK3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', default=str(WEEK3 /
                        'models/faster_rcnn_v2_aug_robusto_v1_lr001/model_demo.pt'))
    parser.add_argument('--arquitectura', choices=['faster_rcnn_v2', 'faster_rcnn_v3'],
                        default='faster_rcnn_v2')
    parser.add_argument('--puerto', type=int, default=8766)
    parser.add_argument('--medir', type=int, default=0, metavar='IMAGENES',
                        help='Medir inferencias sintéticas y salir, sin evaluar datasets')
    args = parser.parse_args()
    import torch
    if not torch.cuda.is_available():
        parser.exit(1, 'CUDA no está disponible. Comprueba torch con CUDA 12.8 y el controlador.\n')
    gpu = torch.cuda.get_device_name(0)
    print('GPU:', gpu, flush=True)
    # Solo se instala el módulo falso de importación. Este proceso no conecta al robot.
    import simulacion
    simulacion.instalar(str(WEEK3))
    import cv2
    import numpy as np
    from aiohttp import web
    from demo_utils import cargar_modelo, calentar, detectar
    try:
        model, device, _ = cargar_modelo(args.arquitectura, args.modelo, use_gpu=True)
        calentar(model)
    except Exception as error:
        parser.exit(1, 'No se pudo cargar el modelo entrenado: %s\n' % error)
    if args.medir:
        if args.medir < 1:
            parser.error('--medir debe ser positivo')
        tiempos = [detectar(model, np.zeros((720, 1280, 3), dtype=np.uint8))[1]
                   for _ in range(args.medir)]
        print(json.dumps(dict(dispositivo=str(device), gpu=gpu, arquitectura=args.arquitectura,
                              imagenes=len(tiempos), ms_media=sum(tiempos)/len(tiempos))))
        return

    lock = asyncio.Lock()

    async def inferir(request):
        data = await request.read()
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.shape[0] > 2160 or image.shape[1] > 3840:
            raise web.HTTPBadRequest(text='Se necesita un JPEG válido de hasta 3840 × 2160')
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        async with lock:
            pred, ms = await asyncio.get_running_loop().run_in_executor(None, detectar, model, rgb)
        return web.json_response(dict(boxes=pred['boxes'].tolist(), scores=pred['scores'].tolist(),
                                      ms=ms, width=image.shape[1], height=image.shape[0]))

    app = web.Application(client_max_size=4*1024*1024)
    app.router.add_post('/detectar', inferir)
    web.run_app(app, host='127.0.0.1', port=args.puerto)


if __name__ == '__main__':
    main()
