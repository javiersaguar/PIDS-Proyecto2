"""Ampliaciones de T14: exteriores, obstáculos y copias de imágenes difíciles.

Recibe imágenes RGB uint8 después del aumento geométrico. No mueve cajas ni
infiere etiquetas nuevas. Compatible con albumentations 1.4.18.
"""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import random

import albumentations as alb
import cv2
import numpy as np


@dataclass(frozen=True)
class ConfigAumento:
    sombras: bool = True
    oclusion: bool = True
    difficult: bool = True
    lluvia: bool = True
    exteriores: tuple = ('V04', 'V09')
    p_sombra: float = 0.25
    p_oclusion: float = 0.15
    p_difficult: float = 0.5
    p_lluvia: float = 0.15
    max_oculto: float = 0.25

    def __post_init__(self):
        for nombre in ('p_sombra', 'p_oclusion', 'p_difficult', 'p_lluvia', 'max_oculto'):
            if not 0 <= getattr(self, nombre) <= 1:
                raise ValueError(nombre + ' debe estar entre 0 y 1')
        if self.p_sombra + self.p_lluvia > 1:
            raise ValueError('Sombra y lluvia comparten un sorteo: su suma no puede superar 1')


def configurar(perfil):
    """Perfiles individuales para atribuir mejoras y uno conjunto para explorar."""
    nombres = {'sombras_v1': 'sombras', 'oclusion_v1': 'oclusion',
               'difficult_v1': 'difficult', 'lluvia_v1': 'lluvia'}
    if perfil == 'robusto_v1':
        return ConfigAumento()
    if perfil not in nombres:
        raise ValueError('Perfil desconocido: ' + perfil)
    opciones = dict.fromkeys(('sombras', 'oclusion', 'difficult', 'lluvia'), False)
    opciones[nombres[perfil]] = True
    return ConfigAumento(**opciones)


@contextmanager
def semilla_temporal(semilla):
    """Reproduce Albumentations 1.4.18 sin alterar el estado aleatorio del llamador."""
    estado_py, estado_np = random.getstate(), np.random.get_state()
    random.seed(int(semilla))
    np.random.seed(int(semilla) % (2 ** 32))
    try:
        yield
    finally:
        random.setstate(estado_py)
        np.random.set_state(estado_np)


def transformar(imagen, transformacion, semilla):
    with semilla_temporal(semilla):
        # RandomRain de 1.4.18 dibuja sobre su entrada: preservar el original.
        return transformacion(image=imagen.copy())['image']


def sombra_local(imagen, semilla):
    return transformar(imagen, alb.RandomShadow(
        shadow_roi=(0, 0.15, 1, 1), num_shadows_limit=(1, 1),
        shadow_intensity_range=(0.65, 0.85), p=1), semilla)


def lluvia_suave(imagen, semilla):
    # Drizzle fija gotas de 10 px en 1.4.18. Poco desenfoque y oscurecimiento.
    return transformar(imagen, alb.RandomRain(
        rain_type='drizzle', slant_range=(-8, 8), drop_width=1,
        blur_value=3, brightness_coefficient=0.9, p=1), semilla)


def fracciones_ocultas(mascara, cajas):
    """Fracción del área de CADA caja tapada por la unión de los obstáculos."""
    resultado = []
    for c in cajas:
        region = mascara[int(c['ymin']):int(c['ymax']), int(c['xmin']):int(c['xmax'])]
        resultado.append(float(np.count_nonzero(region)) / region.size if region.size else 1.)
    return resultado


def oclusion_texturada(imagen, cajas, semilla, max_oculto=0.25):
    """Postes/patas con anchura variable, textura, iluminación y borde suavizado.

    Son obstáculos procedurales, no recortes fotográficos. Se limita la unión de
    sus máscaras, incluido el borde suavizado, al 25 % del área de cada caja.
    """
    rng = np.random.RandomState(semilla)
    alto, ancho = imagen.shape[:2]
    union = np.zeros((alto, ancho), np.uint8)
    salida = imagen.astype(np.float32).copy()
    for _ in range(rng.randint(1, 3)):
        for _ in range(30):
            x = rng.randint(0, ancho)
            y = rng.randint(0, max(1, int(alto * 0.5)))
            grosor = rng.randint(max(2, ancho // 100), max(3, ancho // 35))
            inclinacion = rng.randint(-max(1, ancho // 30), max(2, ancho // 30))
            inferior = max(2, int(grosor * rng.uniform(0.6, 1.4)))
            puntos = np.array([[x, y], [x + grosor, y],
                               [x + inclinacion + inferior, alto - 1],
                               [x + inclinacion, alto - 1]], np.int32)
            mascara = np.zeros_like(union)
            cv2.fillConvexPoly(mascara, puntos, 255)
            alfa = cv2.GaussianBlur(mascara, (3, 3), 0).astype(np.float32) / 255
            propuesta = np.maximum(union, (alfa > 0).astype(np.uint8))
            if all(f <= max_oculto for f in fracciones_ocultas(propuesta, cajas)):
                break
        else:
            continue
        tono = rng.uniform(25, 100)
        # Gradiente espacial y ruido suave: conserva una textura reproducible.
        textura = (tono + 12 * np.sin(np.arange(ancho)[None, :] * 0.3)
                   + rng.normal(0, 3, (alto, ancho)))
        tinte = rng.uniform(0.85, 1.15, 3)
        obstaculo = np.clip(textura[:, :, None] * tinte, 0, 255)
        salida = salida * (1 - alfa[:, :, None]) + obstaculo * alfa[:, :, None]
        union = propuesta
    return np.clip(salida, 0, 255).astype(np.uint8), union


def ampliar_copia(imagen, cajas, secuencia, indice, semilla, config=None, previas=()):
    """Aplica extras tras la geometría y devuelve imagen y un registro auditable.

    Solo la copia 0 puede recibir el refuerzo difficult. Lluvia/sombra son
    excluyentes; la lluvia no se acumula con el refuerzo ni con otra oclusión.
    No aumenta el número de muestras ni altera las etiquetas difficult.
    """
    config = config or ConfigAumento()
    rng = np.random.RandomState(semilla ^ 0x27A51)
    salida = imagen.copy()
    registro = {'aplicadas': [], 'max_fraccion_oculta': 0.0}
    exterior = secuencia in config.exteriores
    sorteo = rng.rand()
    p_lluvia = config.p_lluvia if config.lluvia else 0
    lluvia = exterior and sorteo < p_lluvia and 'Oclusion' not in previas
    if lluvia:
        salida = lluvia_suave(salida, semilla)
        registro['aplicadas'].append('LluviaSuave')
    elif exterior and config.sombras and p_lluvia <= sorteo < p_lluvia + config.p_sombra:
        salida = sombra_local(salida, semilla)
        registro['aplicadas'].append('SombraLocal')

    if config.difficult and indice == 0 and any(c.get('difficult') for c in cajas) and not lluvia:
        if rng.rand() < config.p_difficult:
            if rng.rand() < 0.5 or 'MotionBlur' in previas:
                factor = float(rng.uniform(0.7, 0.85))
                salida = np.clip(salida.astype(np.float32) * factor, 0, 255).astype(np.uint8)
                registro['aplicadas'].append('DifficultOscuro')
                registro['factor_oscuro'] = factor
            else:
                salida = transformar(salida, alb.MotionBlur(blur_limit=(7, 11), p=1), semilla)
                registro['aplicadas'].append('DifficultMovimiento')

    if config.oclusion and not lluvia and rng.rand() < config.p_oclusion:
        salida, mascara = oclusion_texturada(salida, cajas, semilla, config.max_oculto)
        if mascara.any():
            registro['aplicadas'].append('OclusionTexturada')
            registro['max_fraccion_oculta'] = max(fracciones_ocultas(mascara, cajas), default=0.)
    return salida, registro


def configuracion_serializable(config):
    return asdict(config)
