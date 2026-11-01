"""Análisis adicionales para responder a la revisión de la entrega 1.

1. Intervalo de extracción: redundancia entre fotogramas extraídos según el intervalo.
2. Nuestros vídeos frente a validación y test: tamaño de las cajas, posición, brillo, color, robots por imagen.
3. Ancho y alto de las cajas frente a su posición (perspectiva), normales y difficult.
"""
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(sys.argv[1])
SALIDA = Path(sys.argv[2])
SALIDA.mkdir(parents=True, exist_ok=True)
W1 = REPO / 'ENTREGA 1' / 'WEEK1'
W2 = REPO / 'ENTREGA 1' / 'WEEK2'

NARANJA, VERDE, AZUL = '#D9692B', '#2A9D8F', '#1F5FA8'
TINTA, GRIS = '#1F2937', '#C9CED6'
COLORES = {'Nuestros vídeos': NARANJA, 'Validación': VERDE, 'Test': AZUL}
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#E5E7EB', 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'axes.edgecolor': '#9CA3AF', 'axes.labelcolor': TINTA, 'xtick.color': TINTA,
                     'ytick.color': TINTA, 'axes.titleweight': 'bold', 'savefig.dpi': 220})
res = {}
coma = matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ','))


def leer_xml(ruta):
    r = ET.parse(ruta).getroot()
    W = int(r.find('size/width').text)
    H = int(r.find('size/height').text)
    cajas = []
    for o in r.iter('object'):
        b = o.find('bndbox')
        x0, y0, x1, y1 = (float(b.find(k).text) for k in ('xmin', 'ymin', 'xmax', 'ymax'))
        d = o.find('difficult')
        cajas.append(dict(xmin=x0, ymin=y0, xmax=x1, ymax=y1, difficult=int(d is not None and d.text.strip() == '1')))
    return W, H, cajas


def cargar(conjunto, xmls):
    imgs, cajas = [], []
    for x in xmls:
        W, H, cs = leer_xml(x)
        seq = x.parent.parent.name
        jpg = x.parent.parent / 'images' / (x.stem + '.jpg')
        imgs.append(dict(conjunto=conjunto, seq=seq, xml=str(x), jpg=str(jpg), W=W, H=H, robots=len(cs)))
        for c in cs:
            c.update(conjunto=conjunto, seq=seq, W=W, H=H)
            cajas.append(c)
    return imgs, cajas


xml_nuestros = sorted(x for x in (W1 / 'ANOTACION').glob('[A-E]_*/*/labels/*.xml'))
xml_val = sorted((W2 / 'DATOS_ASIGNATURA' / 'data_val').glob('*/labels/*.xml'))
xml_test = sorted((W2 / 'DATOS_ASIGNATURA' / 'data_test').glob('*/labels/*.xml'))
I, C = [], []
for nombre, xs in (('Nuestros vídeos', xml_nuestros), ('Validación', xml_val), ('Test', xml_test)):
    a, b = cargar(nombre, xs)
    I += a
    C += b
imgs = pd.DataFrame(I)
cajas = pd.DataFrame(C)
cajas['w'] = cajas.xmax - cajas.xmin
cajas['h'] = cajas.ymax - cajas.ymin
cajas['cy'] = (cajas.ymin + cajas.ymax) / 2 / cajas.H
cajas['cx'] = (cajas.xmin + cajas.xmax) / 2 / cajas.W
cajas['borde'] = (cajas.xmin <= 2) | (cajas.ymin <= 2) | (cajas.xmax >= cajas.W - 2) | (cajas.ymax >= cajas.H - 2)
print(imgs.groupby('conjunto').agg(imagenes=('xml', 'size'), robots=('robots', 'sum')))

# --- brillo y tono de cada imagen -------------------------------------------------------------
def metricas(ruta):
    bgr = cv2.imread(ruta)
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    b, g, r = bgr.reshape(-1, 3).mean(axis=0)
    return gris.mean(), gris.std(), b - r, g - r


m = np.array([metricas(p) for p in imgs.jpg])
imgs['brillo'], imgs['contraste'], imgs['b_r'], imgs['g_r'] = m.T

# --- 2. comparación de conjuntos --------------------------------------------------------------
dom = {}
for n in COLORES:
    ii, cc = imgs[imgs.conjunto == n], cajas[cajas.conjunto == n]
    dom[n] = dict(
        secuencias=int(ii.seq.nunique()), imagenes=int(len(ii)), robots=int(len(cc)),
        robots_por_imagen=round(float(ii.robots.mean()), 2), negativas_pct=round(100 * float((ii.robots == 0).mean()), 1),
        difficult_pct=round(100 * float(cc.difficult.mean()), 1),
        ancho_mediana=round(float(cc.w.median()), 0), alto_mediana=round(float(cc.h.median()), 0),
        ancho_p10=round(float(cc.w.quantile(0.1)), 0),
        ancho_menor_30_pct=round(100 * float((cc.w < 30).mean()), 1),
        ancho_menor_50_pct=round(100 * float((cc.w < 50).mean()), 1),
        area_pequena_coco_pct=round(100 * float((cc.w * cc.h < 32 ** 2).mean()), 1),
        aspecto_mediana=round(float((cc.w / cc.h).median()), 2),
        cy_mediana=round(float(cc.cy.median()), 2), cy_p10=round(float(cc.cy.quantile(0.1)), 2),
        cy_p90=round(float(cc.cy.quantile(0.9)), 2),
        borde_pct=round(100 * float(cc.borde.mean()), 1),
        brillo_mediana=round(float(ii.brillo.median()), 1), brillo_p5=round(float(ii.brillo.quantile(0.05)), 1),
        brillo_p95=round(float(ii.brillo.quantile(0.95)), 1),
        b_r_mediana=round(float(ii.b_r.median()), 1), b_r_p5=round(float(ii.b_r.quantile(0.05)), 1),
        b_r_p95=round(float(ii.b_r.quantile(0.95)), 1),
        b_r_abs_mayor_12_pct=round(100 * float((ii.b_r.abs() > 12).mean()), 1),
    )
# tono por secuencia: cuántas secuencias tienen un tono medio (B-R) fuera de +-12
for n in COLORES:
    s = imgs[imgs.conjunto == n].groupby('seq')[['b_r', 'g_r', 'brillo']].mean()
    dom[n]['secuencias_tono'] = {k: [round(float(v.b_r), 1), round(float(v.g_r), 1), round(float(v.brillo), 1)]
                                 for k, v in s.iterrows()}
res['dominio'] = dom

fig, ejes = plt.subplots(2, 2, figsize=(8.2, 5.4))
bins_w = np.logspace(np.log10(8), np.log10(1000), 34)
ax = ejes[0, 0]
for n, col in COLORES.items():
    w = cajas[cajas.conjunto == n].w
    ax.hist(w, bins=bins_w, histtype='step', linewidth=1.8, color=col, density=True, label=n)
ax.set_xscale('log')
ax.axvline(30, color=TINTA, linestyle=':', linewidth=1)
ax.text(31, ax.get_ylim()[1] * 0.92, '30 px', fontsize=8, color=TINTA)
ax.set(title='Ancho de las cajas', xlabel='Ancho (px, escala logarítmica)', ylabel='Densidad')
ax.set_xticks([10, 30, 100, 300, 1000])
ax.set_xticklabels(['10', '30', '100', '300', '1000'])
ax.legend(frameon=False, fontsize=8, loc='upper right')

ax = ejes[0, 1]
bins = np.linspace(0, 1, 26)
for n, col in COLORES.items():
    ax.hist(cajas[cajas.conjunto == n].cy, bins=bins, histtype='step', linewidth=1.8, color=col, density=True)
ax.set(title='Altura del centro de la caja', xlabel='Centro vertical (0 = arriba, 1 = abajo)', ylabel='Densidad')

ax = ejes[1, 0]
bins = np.linspace(20, 200, 37)
for n, col in COLORES.items():
    ax.hist(imgs[imgs.conjunto == n].brillo, bins=bins, histtype='step', linewidth=1.8, color=col, density=True)
ax.set(title='Brillo medio de cada imagen', xlabel='Nivel de gris medio (0-255)', ylabel='Densidad')

ax = ejes[1, 1]
bins = np.linspace(-40, 70, 45)
for n, col in COLORES.items():
    ax.hist(imgs[imgs.conjunto == n].b_r, bins=bins, histtype='step', linewidth=1.8, color=col, density=True)
ax.axvspan(-24, 24, color=GRIS, alpha=0.35, linewidth=0)
ax.text(25, ax.get_ylim()[1] * 0.9, 'alcance del\ndesplazamiento RGB', ha='left', va='top', fontsize=8, color=TINTA)
ax.set(title='Tono de cada imagen (azul menos rojo)', xlabel='Media de B − media de R', ylabel='Densidad')
for ax in ejes.flat:
    ax.yaxis.set_major_formatter(coma)
ejes[0, 1].xaxis.set_major_formatter(coma)
plt.tight_layout()
fig.savefig(SALIDA / 'dominio_conjuntos.png')
plt.close(fig)

# --- 3. ancho y alto frente a la posición -----------------------------------------------------
n = cajas[cajas.conjunto == 'Nuestros vídeos'].copy()
libres = n[~n.borde]
pers = {}
pers['cajas'] = int(len(n))
pers['borde'] = int(n.borde.sum())
pers['corr_ymax_logalto'] = round(float(np.corrcoef(libres.ymax, np.log(libres.h))[0, 1]), 2)
pers['corr_ymax_logancho'] = round(float(np.corrcoef(libres.ymax, np.log(libres.w))[0, 1]), 2)
pers['corr_logancho_logalto'] = round(float(np.corrcoef(np.log(n.w), np.log(n.h))[0, 1]), 2)
tercios = pd.cut(libres.ymax, [0, 360, 480, 721], labels=['base < 360 px', '360-480 px', 'base > 480 px'])
pers['por_banda'] = {str(k): dict(cajas=int(len(g)), ancho_mediana=float(g.w.median()), alto_mediana=float(g.h.median()))
                     for k, g in libres.groupby(tercios, observed=True)}
for grupo, g in (('normal', n[n.difficult == 0]), ('difficult', n[n.difficult == 1]),
                 ('borde', n[n.borde]), ('sin_borde', n[~n.borde])):
    pers[grupo] = dict(cajas=int(len(g)), ancho_mediana=float(g.w.median()), alto_mediana=float(g.h.median()),
                       aspecto_mediana=round(float((g.w / g.h).median()), 2),
                       aspecto_p10=round(float((g.w / g.h).quantile(0.1)), 2),
                       aspecto_p90=round(float((g.w / g.h).quantile(0.9)), 2))
pers['difficult_en_borde_pct'] = round(100 * float(n[n.borde].difficult.mean()), 1)
pers['difficult_sin_borde_pct'] = round(100 * float(n[~n.borde].difficult.mean()), 1)
res['perspectiva'] = pers

fig, ejes = plt.subplots(1, 2, figsize=(8.2, 3.3))
ax = ejes[0]
for d, col, lab in ((0, '#2A78D6', 'Normal'), (1, NARANJA, 'Difficult')):
    g = libres[libres.difficult == d]
    ax.scatter(g.ymax, g.h, s=7, color=col, alpha=0.45, edgecolors='none', label=f'{lab} ({len(g)})')
ax.set(yscale='log', title='Alto frente a posición de la base', xlabel='Base de la caja (px desde arriba)',
       ylabel='Alto de la caja (px)')
ax.set_yticks([30, 50, 100, 200, 400])
ax.set_yticklabels(['30', '50', '100', '200', '400'])
ax.minorticks_off()
ax.legend(frameon=False, fontsize=8, loc='upper left', markerscale=2)
ax = ejes[1]
for d, col, lab in ((0, '#2A78D6', 'Normal'), (1, NARANJA, 'Difficult')):
    g = n[n.difficult == d]
    ax.scatter(g.w, g.h, s=7, color=col, alpha=0.45, edgecolors='none')
lim = np.array([15, 900])
for r, t in ((0.5, '1:2'), (1, '1:1'), (2, '2:1')):
    ax.plot(lim, lim / r, color='#6B7280', linewidth=0.8, linestyle='--')
    x = 600 if r > 1 else 17
    ax.text(x, x / r * 1.12, t, fontsize=8, color='#4B5563', ha='right' if r > 1 else 'left', va='bottom')
ax.set(xscale='log', yscale='log', xlim=(15, 900), ylim=(15, 700), title='Ancho frente a alto',
       xlabel='Ancho de la caja (px)', ylabel='Alto de la caja (px)')
for f in (ax.set_xticks, ax.set_yticks):
    f([30, 100, 300])
ax.set_xticklabels(['30', '100', '300'])
ax.set_yticklabels(['30', '100', '300'])
ax.minorticks_off()
plt.tight_layout()
fig.savefig(SALIDA / 'perspectiva_ancho_alto.png')
plt.close(fig)

if (SALIDA / 'analisis_revision.json').exists():
    previo = json.loads((SALIDA / 'analisis_revision.json').read_text(encoding='utf-8'))
    res['intervalo'] = previo['intervalo']
    (SALIDA / 'analisis_revision.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    sys.exit(0)
# --- 1. intervalo de extracción ---------------------------------------------------------------
mini_por_video = {}
tmp = SALIDA / '_videos'
tmp.mkdir(exist_ok=True)
for z in sorted((W1 / 'DATASET PIDS').glob('ROBOMASTER_VIDEO_*.zip')):
    with zipfile.ZipFile(z) as f:
        nombre = [x for x in f.namelist() if x.lower().endswith('.mp4')][0]
        destino = tmp / Path(nombre).name
        if not destino.exists():
            f.extract(nombre, tmp)
    cap = cv2.VideoCapture(str(destino))
    minis = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        minis.append(cv2.resize(fr, (32, 18), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    cap.release()
    gris = np.stack(minis) @ np.array([0.114, 0.587, 0.299], dtype=np.float32) * 255
    mini_por_video[z.stem] = gris
    print(z.stem, len(minis), 'fotogramas')

intervalos = {}
total = sum(len(g) for g in mini_por_video.values())
for k in (6, 12, 24, 48, 96):
    difs, n_imgs = [], 0
    for g in mini_por_video.values():
        idx = np.arange(k, len(g), k)      # como en la extracción: fotogramas k, 2k, ...
        n_imgs += len(g) // k
        s = g[idx]
        difs += list(np.abs(s[1:] - s[:-1]).mean(axis=(1, 2)))
    difs = np.array(difs)
    intervalos[k] = dict(segundos=round(k / 30.303, 2), imagenes=int(n_imgs),
                         casi_duplicadas=int((difs < 5).sum()), casi_duplicadas_pct=round(100 * float((difs < 5).mean()), 1),
                         diferencia_mediana=round(float(np.median(difs)), 1),
                         robots_estimados=int(round(n_imgs * 1420 / 808)))
res['intervalo'] = {'fotogramas_total': int(total), 'por_intervalo': intervalos}
(SALIDA / 'analisis_revision.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(res, ensure_ascii=False, indent=1))
