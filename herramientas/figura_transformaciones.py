"""Una imagen de nuestros vídeos con cada transformación del aumento aplicada por separado."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import albumentations as alb
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(sys.argv[1])
SALIDA = Path(sys.argv[2])
ANOT = REPO / 'ENTREGA 1' / 'WEEK1' / 'ANOTACION'
RELLENO = (114, 114, 114)


def leer(x):
    r = ET.parse(x).getroot()
    cajas = []
    for o in r.iter('object'):
        b = o.find('bndbox')
        d = o.find('difficult')
        cajas.append([int(float(b.find(k).text)) for k in ('xmin', 'ymin', 'xmax', 'ymax')] +
                     [int(d is not None and d.text.strip() == '1')])
    return cajas


# imagen de interior con más robots, ninguno difficult ni cortado por el borde
mejor = None
for x in sorted(ANOT.glob('[A-E]_*/ROBOMASTER_VIDEO_0[67]/labels/*.xml')):
    c = leer(x)
    if c and all(k[4] == 0 and k[0] > 20 and k[2] < 1260 and k[1] > 10 and k[3] < 710 for k in c):
        if mejor is None or len(c) > len(mejor[1]) or (len(c) == len(mejor[1]) and
                                                         min(k[2] - k[0] for k in c) > min(k[2] - k[0] for k in mejor[1])):
            mejor = (x, c)
xml, cajas = mejor
img = cv2.cvtColor(cv2.imread(str(xml.parent.parent / 'images' / (xml.stem + '.jpg'))), cv2.COLOR_BGR2RGB)
print('Imagen:', xml, len(cajas), 'robots')


def ocluir(imagen, cajas, rng):
    """Misma regla que el notebook: barras oscuras que no tapan más del 35 % del ancho de un robot."""
    imagen = imagen.copy()
    alto, ancho = imagen.shape[:2]
    for _ in range(2):
        for _ in range(50):
            grosor, inclinacion = rng.randint(14, 46), rng.randint(-25, 26)
            x, y0 = rng.randint(30, ancho - grosor - 30), rng.randint(0, int(0.45 * alto))
            bx0, bx1 = min(x, x + inclinacion), max(x + grosor, x + grosor + inclinacion)
            tapa = [max(0, min(bx1, c[2]) - max(bx0, c[0])) / float(c[2] - c[0]) for c in cajas if c[3] > y0]
            if all(t <= 0.35 for t in tapa) and any(t > 0.1 for t in tapa):
                break
        tono = int(rng.randint(15, 70))
        pts = np.array([[x, y0], [x + grosor, y0], [x + grosor + inclinacion, alto], [x + inclinacion, alto]], np.int32)
        cv2.fillConvexPoly(imagen, pts, (tono, tono, min(255, tono + 6)), lineType=cv2.LINE_AA)
    return imagen


cajas_bp = alb.BboxParams(format='pascal_voc', label_fields=['d'], min_visibility=0.3, min_width=10, min_height=10)
TRANSF = [
    ('Original', None),
    ('Volteo horizontal', alb.HorizontalFlip(p=1)),
    ('Escala ×0,7, desplazamiento\ny giro de 6°', alb.Affine(scale=0.7, translate_percent={'x': 0.06, 'y': 0.03}, rotate=6,
                                                          keep_ratio=True, rotate_method='ellipse',
                                                          mode=cv2.BORDER_CONSTANT, cval=RELLENO, p=1)),
    ('Brillo −20 % y contraste +20 %', alb.RandomBrightnessContrast(brightness_limit=(-0.2, -0.2),
                                                                    contrast_limit=(0.2, 0.2), p=1)),
    ('Desplazamiento RGB\n(R +12, B −12)', alb.RGBShift(r_shift_limit=(12, 12), g_shift_limit=(0, 0),
                                                       b_shift_limit=(-12, -12), p=1)),
    ('Desenfoque de movimiento\n(núcleo de 9 px)', alb.MotionBlur(blur_limit=(9, 9), p=1)),
    ('Compresión JPEG\n(calidad 35)', alb.ImageCompression(quality_range=(35, 35), p=1)),
    ('Oclusión sintética', 'oclusion'),
]
np.random.seed(3)
fig, ejes = plt.subplots(2, 4, figsize=(9.6, 3.55))
for ax, (titulo, t) in zip(ejes.flat, TRANSF):
    if t is None:
        im, cs = img, cajas
    elif t == 'oclusion':
        im, cs = ocluir(img, cajas, np.random.RandomState(7)), cajas
    else:
        r = alb.Compose([t], bbox_params=cajas_bp)(image=img, bboxes=[c[:4] for c in cajas], d=[c[4] for c in cajas])
        im, cs = r['image'], [list(map(int, b)) + [d] for b, d in zip(r['bboxes'], r['d'])]
    lienzo = im.copy()
    for c in cs:
        cv2.rectangle(lienzo, (c[0], c[1]), (c[2], c[3]), (42, 120, 214), 6)
    ax.imshow(lienzo)
    ax.set_title(titulo, fontsize=8.5, color='#1F2937', pad=3)
    ax.axis('off')
plt.tight_layout(pad=0.3, w_pad=0.4, h_pad=0.6)
fig.savefig(SALIDA / 'ejemplo_transformaciones.png', dpi=220)
print('ok')
