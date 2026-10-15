"""Regresiones sobre selección de muestras, etiquetas y visibilidad de robots."""
from dataclasses import replace
import copy
import random

import numpy as np

from herramientas.aumento_robusto import (
    ConfigAumento, ampliar_copia, configurar, fracciones_ocultas,
    lluvia_suave, oclusion_texturada, sombra_local,
)


IMAGEN = np.full((180, 320, 3), 150, np.uint8)
CAJAS = [dict(xmin=90, ymin=70, xmax=130, ymax=110, difficult=1),
         dict(xmin=132, ymin=60, xmax=170, ymax=120, difficult=0)]


def test_exteriores_y_exclusion_de_lluvia_con_otros_efectos():
    cfg = ConfigAumento(p_lluvia=1, p_sombra=0, p_difficult=1, p_oclusion=1)
    _, r = ampliar_copia(IMAGEN, CAJAS, 'V04', 0, 2, cfg)
    assert r['aplicadas'] == ['LluviaSuave']
    for sec in ('V01', 'V02', 'V03', 'V05', 'V06', 'V07', 'V08', 'V10'):
        _, r = ampliar_copia(IMAGEN, CAJAS, sec, 0, 2, cfg)
        assert not {'LluviaSuave', 'SombraLocal'} & set(r['aplicadas'])
    _, r = ampliar_copia(IMAGEN, CAJAS, 'V09', 0, 2, cfg, previas=['Oclusion'])
    assert 'LluviaSuave' not in r['aplicadas']
    cfg = replace(cfg, p_lluvia=0, p_sombra=1)
    _, r = ampliar_copia(IMAGEN, CAJAS, 'V09', 1, 3, cfg)
    assert 'SombraLocal' in r['aplicadas']


def test_difficult_solo_una_copia_y_sin_duplicar_motionblur():
    cfg = replace(configurar('difficult_v1'), p_difficult=1)
    for indice in (1, 2):
        im, r = ampliar_copia(IMAGEN, CAJAS, 'V01', indice, 3, cfg)
        assert not r['aplicadas'] and np.array_equal(im, IMAGEN)
    normales = [dict(c, difficult=0) for c in CAJAS]
    _, r = ampliar_copia(IMAGEN, normales, 'V01', 0, 3, cfg)
    assert not r['aplicadas']
    for seed in range(10):
        _, r = ampliar_copia(IMAGEN, CAJAS, 'V01', 0, seed, cfg, previas=['MotionBlur'])
        assert r['aplicadas'] == ['DifficultOscuro']


def test_oclusion_acumulada_nunca_supera_limite_incluidas_cajas_pequenas():
    cajas = CAJAS + [dict(xmin=158, ymin=90, xmax=168, ymax=100, difficult=1)]
    originales = copy.deepcopy(cajas)
    for seed in range(60):
        im, mask = oclusion_texturada(IMAGEN, cajas, seed)
        assert max(fracciones_ocultas(mask, cajas)) <= 0.25
        assert im.shape == IMAGEN.shape and im.dtype == np.uint8
        assert np.array_equal(im[mask == 0], IMAGEN[mask == 0])
    assert cajas == originales
    assert np.all(IMAGEN == 150)


def test_reproducibilidad_y_estado_aleatorio_incluso_con_negativos():
    for f in (lluvia_suave, sombra_local):
        original = IMAGEN.copy()
        random.seed(7)
        np.random.seed(7)
        py, np_state = random.getstate(), np.random.get_state()
        a, b = f(IMAGEN, 18), f(IMAGEN, 18)
        assert np.array_equal(a, b)
        assert np.array_equal(IMAGEN, original)
        assert py == random.getstate()
        assert np.array_equal(np_state[1], np.random.get_state()[1])
    for cajas in (CAJAS, []):
        cfg = ConfigAumento()
        a, ra = ampliar_copia(IMAGEN, cajas, 'V04', 0, 18, cfg)
        b, rb = ampliar_copia(IMAGEN, cajas, 'V04', 0, 18, cfg)
        assert np.array_equal(a, b) and ra == rb
