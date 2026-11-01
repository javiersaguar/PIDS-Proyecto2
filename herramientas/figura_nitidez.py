"""Figura complementaria del EDA: nitidez por vídeo, cajas difficult según la nitidez relativa y robots por imagen.

Uso: python figura_nitidez.py <metricas_imagenes.csv> <salida.png>
"""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

NARANJA, AZUL, VERDE, GRIS = '#D9692B', '#1F5FA8', '#2A9D8F', '#9AA3AF'
TINTA = '#1F2937'
plt.rcParams.update({'font.size': 8.5, 'axes.titlesize': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#E5E7EB', 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'axes.edgecolor': '#9CA3AF', 'axes.labelcolor': TINTA, 'xtick.color': TINTA,
                     'ytick.color': TINTA, 'axes.titleweight': 'bold', 'savefig.dpi': 220})
coma = FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ','))

m = pd.read_csv(sys.argv[1])
assert len(m) == 808 and m.robots.sum() == 1420 and m.difficult.sum() == 375
SEC = sorted(m.secuencia.unique())
EXT = {'V04', 'V09'}

fig, ax = plt.subplots(1, 3, figsize=(6.7, 2.45), gridspec_kw={'width_ratios': [1.55, 1, 0.9]})

# (a) nitidez por vídeo
a = ax[0]
bp = a.boxplot([m[m.secuencia == s].nitidez for s in SEC], widths=0.62, showfliers=False, patch_artist=True,
               medianprops={'color': TINTA, 'linewidth': 1.4}, whiskerprops={'color': GRIS}, capprops={'color': GRIS},
               boxprops={'edgecolor': GRIS})
for caja, s in zip(bp['boxes'], SEC):
    caja.set_facecolor(VERDE if s in EXT else '#D5DAE1')
a.set_xticks(range(1, len(SEC) + 1), [s[1:] for s in SEC], fontsize=7.5)
a.set(yscale='log', xlabel='Vídeo (en verde, los exteriores)', ylabel='Varianza del Laplaciano', title='Nitidez por vídeo')
a.grid(axis='x', visible=False)
a.yaxis.set_major_formatter(coma)

# (b) cajas difficult según la nitidez relativa dentro de su vídeo (imágenes con algún robot)
b = m[m.robots > 0].copy()
b['cuartil'] = pd.qcut(b.nitidez_rel, 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
t = b.groupby('cuartil', observed=True).agg(cajas=('robots', 'sum'), dif=('difficult', 'sum'), n=('robots', 'size'),
                                            con=('difficult', lambda s: (s > 0).sum()))
t['pct'] = 100 * t.dif / t.cajas
t['pct_img'] = 100 * t.con / t.n
bb = ax[1]
barras = bb.bar(range(4), t.pct, color=NARANJA, width=0.62)
bb.bar_label(barras, labels=[f'{v:.1f}'.replace('.', ',') for v in t.pct], fontsize=7.5, padding=2, color=TINTA)
bb.set_xticks(range(4), ['Q1\nmenos\nnítida', 'Q2', 'Q3', 'Q4\nmás\nnítida'], fontsize=7.5)
bb.set(ylim=(0, 64), ylabel='% de cajas difficult', title='Dificultad y nitidez', xlabel='Cuartil de nitidez relativa')
bb.grid(axis='x', visible=False)
bb.yaxis.set_major_formatter(coma)

# (c) robots por imagen
c = ax[2]
conteo = m.robots.value_counts().sort_index()
barras = c.bar(conteo.index, conteo.values, color=AZUL, width=0.62)
c.bar_label(barras, labels=[f'{100 * v / len(m):.1f}'.replace('.', ',') + ' %' for v in conteo.values], fontsize=7, padding=2,
            color=TINTA)
c.set(xticks=conteo.index, xlabel='Robots en la imagen', ylabel='Imágenes', title='Robots por imagen', ylim=(0, 390))
c.grid(axis='x', visible=False)

plt.tight_layout(pad=0.6, w_pad=1.3)
fig.savefig(sys.argv[2])
resumen = {
    'por_cuartil': {k: {'cajas': int(r.cajas), 'difficult': int(r.dif), 'pct_cajas_difficult': round(r.pct, 1),
                        'imagenes': int(r.n), 'pct_imagenes_con_difficult': round(r.pct_img, 1)} for k, r in t.iterrows()},
    'umbrales_nitidez_rel': [round(x, 3) for x in b.nitidez_rel.quantile([.25, .5, .75])],
    'mediana_nitidez_exteriores': {s: round(m[m.secuencia == s].nitidez.median(), 1) for s in sorted(EXT)},
    'mediana_nitidez_interiores': {s: round(m[m.secuencia == s].nitidez.median(), 1) for s in SEC if s not in EXT},
    'robots_por_imagen': {int(k): int(v) for k, v in conteo.items()},
}
print(json.dumps(resumen, ensure_ascii=False, indent=1))
