"""Imágenes del aumento de datos para la presentación: cada transformación, aplicada sola, con sus cajas.

Usa las mismas transformaciones e intensidades que el catálogo de ENTREGA 1/WEEK1/data_aug.ipynb (Figura 20 de
la memoria) y las ampliaciones de herramientas/aumento_robusto.py, que forman el perfil robusto_v1 con el que se
entrenaron todos los modelos de la cadena, incluido el final. También genera las que no se usaron, con las cajas
tal como las devuelve albumentations.

Necesita albumentations 1.4.18 (el entorno .venv-aug):

    .venv-aug/Scripts/python.exe herramientas/figuras_aumento.py

Escribe docs/informes/figuras/aumento/*.jpg y presentacion/src/datos/aumento.js.
"""
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault('NO_ALBUMENTATIONS_UPDATE', '1')
import albumentations as alb  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from herramientas.aumento_robusto import lluvia_suave, oclusion_texturada, sombra_local, transformar  # noqa: E402

assert alb.__version__ == '1.4.18', f'Hace falta albumentations 1.4.18 (hay {alb.__version__})'
ANOTACION = RAIZ / 'ENTREGA 1' / 'WEEK1' / 'ANOTACION'
SALIDA = RAIZ / 'docs' / 'informes' / 'figuras' / 'aumento'
MODULO = RAIZ / 'presentacion' / 'src' / 'datos' / 'aumento.js'
RELLENO = (114, 114, 114)
ANCHO, ALTO = 1280, 720
GUARDAR = (832, 468)


def leer(video, frame):
    carpeta = next(ANOTACION.glob(f'*/ROBOMASTER_VIDEO_{video}'))
    nombre = f'frame_{frame:04d}'
    img = cv2.cvtColor(cv2.imread(str(carpeta / 'images' / f'{nombre}.jpg')), cv2.COLOR_BGR2RGB)
    xml = (carpeta / 'labels' / f'{nombre}.xml').read_text(encoding='utf-8')
    cajas = []
    for o in re.findall(r'<object>(.*?)</object>', xml, re.S):
        v = {k: float(re.search(f'<{k}>([^<]*)</{k}>', o).group(1)) for k in ('xmin', 'ymin', 'xmax', 'ymax', 'difficult')}
        cajas.append({'xmin': v['xmin'], 'ymin': v['ymin'], 'xmax': v['xmax'], 'ymax': v['ymax'], 'difficult': int(v['difficult'])})
    return img, cajas


def aplicar(t, img, cajas, semilla=7):
    """Una transformación sola con el filtro de cajas del notebook (parametros_cajas)."""
    np.random.seed(semilla)
    import random
    random.seed(semilla)
    comp = alb.Compose([t], bbox_params=alb.BboxParams(format='pascal_voc', label_fields=['idx'], min_visibility=0.3,
                                                       min_area=100, min_width=10, min_height=10))
    r = comp(image=img, bboxes=[[c['xmin'], c['ymin'], c['xmax'], c['ymax']] for c in cajas], idx=list(range(len(cajas))))
    salida = [{'xmin': b[0], 'ymin': b[1], 'xmax': b[2], 'ymax': b[3], 'difficult': cajas[int(i)]['difficult']}
              for b, i in zip(r['bboxes'], r['idx'])]
    return r['image'], salida


def ocluir_barras(imagen, cajas, rng):
    """Oclusión del perfil base (data_aug.ipynb, función ocluir): barras oscuras que tapan como mucho el 35 % del ancho."""
    imagen = imagen.copy()
    alto, ancho = imagen.shape[:2]
    for _ in range(rng.randint(1, 3)):
        for _ in range(10):
            grosor, inclinacion = rng.randint(14, 46), rng.randint(-25, 26)
            x, y0 = rng.randint(30, ancho - grosor - 30), rng.randint(0, int(0.45 * alto))
            bx0, bx1 = min(x, x + inclinacion), max(x + grosor, x + grosor + inclinacion)
            tapa = [max(0, min(bx1, c['xmax']) - max(bx0, c['xmin'])) / float(c['xmax'] - c['xmin'])
                    for c in cajas if c['ymax'] > y0]
            if all(t <= 0.35 for t in tapa):
                break
        else:
            continue
        tono = int(rng.randint(15, 70))
        puntos = np.array([[x, y0], [x + grosor, y0], [x + grosor + inclinacion, alto], [x + inclinacion, alto]], np.int32)
        cv2.fillConvexPoly(imagen, puntos, (tono, tono, min(255, tono + int(rng.randint(0, 12)))), lineType=cv2.LINE_AA)
    return imagen


afin = dict(keep_ratio=True, mode=cv2.BORDER_CONSTANT, cval=RELLENO, rotate_method='ellipse', p=1)
base, cajas_base = leer('05', 480)        # interior: el mismo fotograma que ya usaba la diapositiva
ext, cajas_ext = leer('04', 1416)         # exterior: sombras y llovizna solo se aplican a V04 y V09
dif, cajas_dif = leer('02', 1344)         # imagen con difficult: el refuerzo solo va a estas


def postes(img, cajas):
    """Oclusión texturada del perfil final: la primera semilla que tapa parte de algún robot."""
    for semilla in range(18, 60):
        salida, mascara = oclusion_texturada(img, cajas, semilla, 0.25)
        if mascara.any() and any(mascara[int(c['ymin']):int(c['ymax']), int(c['xmin']):int(c['xmax'])].mean() > 0.08
                                 for c in cajas):
            return salida
    raise RuntimeError('ninguna semilla tapa un robot')


# (clave, título, se usa, fila de la tabla o motivo, función)
CATALOGO = [
    ('original', 'Original', None, None, lambda: (base, cajas_base)),
    ('volteo', 'Volteo horizontal', True, 0, lambda: aplicar(alb.HorizontalFlip(p=1), base, cajas_base)),
    ('alejar', 'Alejar ×0,6', True, 1, lambda: aplicar(alb.Affine(scale=(0.6, 0.6), **afin), base, cajas_base)),
    ('acercar', 'Acercar ×1,25', True, 1, lambda: aplicar(alb.Affine(scale=(1.25, 1.25), **afin), base, cajas_base)),
    ('girar', 'Desplazar y girar 6°', True, 2, lambda: aplicar(alb.Affine(
        translate_percent={'x': (0.08, 0.08), 'y': (0.05, 0.05)}, rotate=(6, 6), **afin), base, cajas_base)),
    ('brillo', 'Brillo y contraste', True, 3, lambda: aplicar(alb.RandomBrightnessContrast(
        brightness_limit=(0.2, 0.2), contrast_limit=(0.2, 0.2), p=1), base, cajas_base)),
    ('gamma', 'Gamma, más oscuro', True, 3, lambda: aplicar(alb.RandomGamma(gamma_limit=(125, 125), p=1), base, cajas_base)),
    ('tono', 'Tono y saturación', True, 4, lambda: aplicar(alb.HueSaturationValue(
        hue_shift_limit=(8, 8), sat_shift_limit=(20, 20), val_shift_limit=(10, 10), p=1), base, cajas_base)),
    ('canales', 'Desplazamiento RGB', True, 4, lambda: aplicar(alb.RGBShift(
        r_shift_limit=(12, 12), g_shift_limit=(0, 0), b_shift_limit=(-12, -12), p=1), base, cajas_base)),
    ('movimiento', 'Desenfoque de movimiento', True, 5, lambda: aplicar(alb.MotionBlur(blur_limit=(9, 9), p=1), base, cajas_base)),
    ('jpeg', 'Compresión JPEG, calidad 35', True, 6, lambda: aplicar(alb.ImageCompression(quality_range=(35, 35), p=1), base, cajas_base)),
    ('ruido', 'Ruido de sensor', True, 6, lambda: aplicar(alb.GaussNoise(var_limit=(40, 40), p=1), base, cajas_base)),
    ('resolucion', 'Menor resolución ×0,5', True, 6, lambda: aplicar(alb.Downscale(scale_range=(0.5, 0.5), p=1), base, cajas_base)),
    ('sombra', 'Sombra · V04, exterior', True, 7, lambda: (sombra_local(ext, 5), cajas_ext)),
    ('lluvia', 'Llovizna · V04, exterior', True, 7, lambda: (lluvia_suave(ext, 11), cajas_ext)),
    ('postes', 'Postes con textura', True, 8, lambda: (postes(base, cajas_base), cajas_base)),
    ('dif_oscuro', 'Difficult · más oscuro', True, 9, lambda: ((dif.astype(float) * 0.75).astype(np.uint8), cajas_dif)),
    ('dif_movido', 'Difficult · más movido', True, 9, lambda: (transformar(dif, alb.MotionBlur(blur_limit=(7, 11), p=1), 9), cajas_dif)),
    ('barras', 'Barras lisas', False, 'una barra lisa no parece una pata de silla: el modelo final usa postes con textura',
     lambda: (ocluir_barras(base, cajas_base, np.random.RandomState(3)), cajas_base)),
    ('volteo_v', 'Volteo vertical', False, 'el robot nunca está boca abajo', lambda: aplicar(alb.VerticalFlip(p=1), base, cajas_base)),
    ('giro90', 'Giro de 90°', False, 'el robot nunca aparece de lado', lambda: aplicar(alb.Rotate(
        limit=(90, 90), border_mode=cv2.BORDER_CONSTANT, value=RELLENO, p=1), base, cajas_base)),
    ('perspectiva', 'Perspectiva', False, 'las cajas que devuelve no coinciden con el robot', lambda: aplicar(alb.Perspective(
        scale=(0.05, 0.05), pad_mode=cv2.BORDER_CONSTANT, pad_val=RELLENO, p=1), base, cajas_base)),
    ('recorte', 'Recorte 640×480', False, 'ensancha los robots un 33 % y pierde el 14 % de las cajas', lambda: aplicar(alb.Compose([
        alb.RandomCrop(height=480, width=640, p=1), alb.Resize(height=ALTO, width=ANCHO)]), base, cajas_base)),
    ('desenfoque', 'Desenfoque uniforme', False, 'no se parece al desenfoque real, que es de movimiento',
     lambda: aplicar(alb.Blur(blur_limit=(7, 7), p=1), base, cajas_base)),
    ('intercambio', 'Intercambio de canales', False, 'da colores que la cámara nunca dará',
     lambda: aplicar(alb.ChannelShuffle(p=1), base, cajas_base)),
]

SALIDA.mkdir(parents=True, exist_ok=True)
importaciones, filas = [], []
for n, (clave, titulo, usada, fila, f) in enumerate(CATALOGO):
    img, cajas = f()
    alto, ancho = img.shape[:2]
    assert (ancho, alto) == (ANCHO, ALTO), (clave, img.shape)
    fichero = SALIDA / f'{n:02d}_{clave}.jpg'
    cv2.imwrite(str(fichero), cv2.cvtColor(cv2.resize(img, GUARDAR, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 86])
    norm = [{'x': round(c['xmin'] / ANCHO, 4), 'y': round(c['ymin'] / ALTO, 4), 'w': round((c['xmax'] - c['xmin']) / ANCHO, 4),
             'h': round((c['ymax'] - c['ymin']) / ALTO, 4), 'difficult': bool(c['difficult'])} for c in cajas]
    var = 'a_' + clave
    importaciones.append(f"import {var} from '@repo/{fichero.relative_to(RAIZ).as_posix()}';")
    extra = {'fila': fila} if usada else ({'motivo': fila} if usada is False else {})
    filas.append(f"  {{ clave: '{clave}', titulo: {json.dumps(titulo, ensure_ascii=False)}, usada: {json.dumps(usada)}, "
                 f"src: {var}, {json.dumps(extra, ensure_ascii=False)[1:-1]}{', ' if extra else ''}cajas: {json.dumps(norm)} }},")
    print(f'{fichero.name:28} {len(cajas)} cajas')

MODULO.write_text('// Generado por herramientas/figuras_aumento.py: no editar a mano.\n'
                  '// Cada transformación aplicada sola, con sus cajas. usada: true (perfil del modelo final), false (no se usó).\n'
                  + '\n'.join(importaciones) + '\n\nexport const AUMENTO_IMAGENES = [\n' + '\n'.join(filas) + '\n];\n',
                  encoding='utf-8', newline='\n')
print('Escritos', len(CATALOGO), 'imágenes en', SALIDA.relative_to(RAIZ), 'y', MODULO.relative_to(RAIZ))
