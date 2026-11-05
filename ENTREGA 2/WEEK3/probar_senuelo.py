"""Comprueba si el detector vería como robot una imagen (un señuelo, un robot disfrazado...).

Pasa cada imagen por el modelo de circuito.py tal cual y dentro de un fotograma de la
cámara (1280x720, fondo gris) ocupando el 80, 50, 30 y 20 % del alto, para simular que
está más o menos lejos. Para cada caso da la confianza máxima, si la demo le dispararía
(confianza >= UMBRAL) y el porcentaje de verde intenso dentro de la caja, que serviría
para reconocer a un robot aliado marcado en verde (docs/senuelo_aliado.md).

    python probar_senuelo.py ../../docs/informes/figuras/senuelo/*.jpg

No necesita el robot. Con --tapar se repite la primera imagen tapando en blanco cada
zona (ruedas, cañón, cabeza y chasis) para ver en qué se fija el modelo.
"""

import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

TAMANOS = (0.8, 0.5, 0.3, 0.2)
# Zonas (x0, y0, x1, y1) en fracción de la imagen, medidas sobre el robot detective
ZONAS = {
    'ruedas y zapatos': (0, 0.70, 1, 1),
    'cañón': (0.58, 0.27, 0.88, 0.40),
    'cabeza y gimbal': (0.2, 0, 0.75, 0.45),
    'chasis central': (0.4, 0.55, 0.8, 0.8),
}


def en_fotograma(img, fraccion, fondo=120):
    lienzo = np.full((720, 1280, 3), fondo, np.uint8)
    h = int(720 * fraccion)
    w = min(1280, int(img.shape[1] * h / img.shape[0]))
    peque = np.array(Image.fromarray(img).resize((w, h)))
    y0, x0 = (720 - h) // 2, (1280 - w) // 2
    lienzo[y0:y0 + h, x0:x0 + w] = peque
    return lienzo


def verde(img, caja):
    """Fracción de píxeles de verde intenso dentro de la caja (H 70-170º, saturación y brillo altos)."""
    x0, y0, x1, y1 = (int(v) for v in caja)
    hsv = cv2.cvtColor(np.ascontiguousarray(img[y0:y1, x0:x1]), cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return float(((h >= 35) & (h <= 85) & (s >= 120) & (v >= 80)).mean()) if h.size else 0.0


def mejor(model, img):
    """(confianza, % de verde) de la detección más segura, o (0, 0) si no hay ninguna."""
    from demo_utils import detectar
    import circuito as C
    pred, _ = detectar(model, img, C.RESIZE)
    p = pred[0] if isinstance(pred, (list, tuple)) else pred
    if len(p['scores']) == 0:
        return 0.0, 0.0
    i = int(np.argmax([float(s) for s in p['scores']]))
    return float(p['scores'][i]), verde(img, p['boxes'][i])


def tapar(img, zona):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = zona
    out = img.copy()
    out[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description='Confianza del detector ante una imagen (señuelo)')
    p.add_argument('imagenes', nargs='+')
    p.add_argument('--tapar', action='store_true', help='tapar zonas de la primera imagen')
    a = p.parse_args(argv)

    import circuito as C
    from demo_utils import cargar_modelo
    model, _, _ = cargar_modelo(C.MODELO, os.path.join(AQUI, C.RUTA_MODELO), use_gpu=False)
    cab = ['imagen', 'original'] + [f'{int(f * 100)} % alto' for f in TAMANOS] + ['verde', f'¿dispara? (umbral {C.UMBRAL})']
    print('| ' + ' | '.join(cab) + ' |')
    print('|' + '---|' * len(cab))
    for ruta in a.imagenes:
        img = np.array(Image.open(ruta).convert('RGB'))
        resultados = [mejor(model, img)] + [mejor(model, en_fotograma(img, f)) for f in TAMANOS]
        confianzas = [c for c, _ in resultados]
        g = max(v for _, v in resultados)
        dispara = sum(c >= C.UMBRAL for c in confianzas)
        print(f'| {os.path.basename(ruta)} | ' + ' | '.join(f'{c * 100:.1f} %' for c in confianzas)
              + f' | {g * 100:.1f} % | {dispara} de {len(confianzas)} |')
    if a.tapar:
        img = np.array(Image.open(a.imagenes[0]).convert('RGB'))
        print(f'\nTapando zonas de {os.path.basename(a.imagenes[0])}:')
        todo = img
        for nombre, zona in ZONAS.items():
            print(f'  {nombre:18s} {mejor(model, tapar(img, zona))[0] * 100:5.1f} %')
            todo = tapar(todo, zona)
        print(f'  {"todas a la vez":18s} {mejor(model, todo)[0] * 100:5.1f} %')


if __name__ == '__main__':
    main()
