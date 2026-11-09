"""Figuras añadidas por la revisión de la entrega 2 y para el Bloque 3.

    python herramientas/figuras_revision_entrega2.py

Crea en docs/informes/figuras/:
- sistema_entrenamiento.png: esquema de bloques del entrenamiento, solo con módulos y sus
  entradas y salidas (comentario C2.1);
- curva_pr.png: curva precisión-exhaustividad en test del modelo final y de Faster R-CNN
  MobileNet, con los puntos de umbral_confianza.csv (comentario C2.7);
- bloque3/laboratorio.jpg: tres imágenes de la cámara del robot en el laboratorio. Necesita
  ENTREGA 2/WEEK3/evidencias/, que no se versiona; si falta, se deja la figura que haya.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
FIG = RAIZ / 'docs/informes/figuras'
TEST = RAIZ / 'ENTREGA 1/WEEK2/resultados_test'
EVIDENCIAS = RAIZ / 'ENTREGA 2/WEEK3/evidencias'
TINTA, SUAVE = '#1F2937', '#4B5563'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#E5E7EB',
                     'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.edgecolor': '#9CA3AF',
                     'axes.titleweight': 'bold', 'axes.titlesize': 10})


def coma(v, dec=2):
    return f'{v:.{dec}f}'.replace('.', ',')


# --- C2.1: esquema de bloques -------------------------------------------------------------
def sistema():
    fig, ax = plt.subplots(figsize=(9.9, 4.7))
    ax.set_xlim(0, 20.9)
    ax.set_ylim(-0.2, 7.4)
    ax.axis('off')
    ax.grid(False)
    w, h = 3.5, 0.95
    col = [0.2, 5.8, 11.4, 17.0]
    fila = {'A': 5.75, 'B': 3.35, 'C': 0.95}
    grupos = {'ent': ('#E8F0F8', '#2C6188'), 'val': ('#EAF5EE', '#2E7D4F'), 'test': ('#FBEFE6', '#B35C1E')}
    modulos = {
        'datos': ('A', 0, 'Datos de\nentrenamiento', 'ent'),
        'lotes': ('A', 1, 'Carga en lotes', 'ent'),
        'detector': ('A', 2, 'Detector', 'ent'),
        'perdida': ('A', 3, 'Función de pérdida', 'ent'),
        'optim': ('B', 3, 'Optimizador\nSGD', 'ent'),
        'evalua': ('B', 2, 'Evaluación en\nvalidación', 'val'),
        'seleccion': ('B', 1, 'Selección\ndel modelo', 'val'),
        'val': ('C', 2, 'Datos de\nvalidación', 'val'),
        'test': ('C', 0, 'Evaluación\nen test', 'test'),
        'datos_test': ('C', 1, 'Datos de test', 'test'),
    }
    pos = {}
    for k, (f, c, texto, g) in modulos.items():
        x, y = col[c], fila[f]
        fondo, borde = grupos[g]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                    fc=fondo, ec=borde, lw=1.3))
        ax.text(x + w / 2, y + h / 2, texto, ha='center', va='center', fontsize=8.8,
                fontweight='bold', color=TINTA, linespacing=1.05)
        pos[k] = (x, y)

    def borde(k, lado):
        x, y = pos[k]
        return {'d': (x + w, y + h / 2), 'i': (x, y + h / 2), 'ar': (x + w / 2, y + h),
                'ab': (x + w / 2, y)}[lado]

    def flecha(a, b, texto, dx=0, dy=0, ha='center', va='bottom', curva=0.0, color='#4B5563'):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=12, color=color, lw=1.1,
                                     connectionstyle=f'arc3,rad={curva}', shrinkA=2, shrinkB=2))
        mx, my = (a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy
        ax.text(mx, my, texto, ha=ha, va=va, fontsize=7.4, color=SUAVE, style='italic', linespacing=1.05)

    flecha(borde('datos', 'd'), borde('lotes', 'i'), 'imágenes y\ncajas', dy=0.08)
    flecha(borde('lotes', 'd'), borde('detector', 'i'), 'lotes de 8\nimágenes y cajas', dy=0.08)
    flecha(borde('detector', 'd'), borde('perdida', 'i'), 'cajas y\nconfianzas', dy=0.08)
    flecha(borde('perdida', 'ab'), borde('optim', 'ar'), 'gradientes de\nla pérdida', dx=0.12, ha='left', va='center')
    flecha((pos['optim'][0], pos['optim'][1] + h * 0.85), (pos['detector'][0] + w * 0.8, pos['detector'][1]),
           'pesos\nnuevos', dx=0.2, dy=0.05, ha='left', va='center')
    flecha((pos['detector'][0] + w * 0.3, pos['detector'][1]), (pos['evalua'][0] + w * 0.3, pos['evalua'][1] + h),
           'pesos al final\nde cada época', dx=-0.12, ha='right', va='center')
    flecha(borde('val', 'ar'), borde('evalua', 'ab'), 'imágenes de secuencias\nno vistas y sus cajas',
           dx=0.12, ha='left', va='center')
    flecha(borde('evalua', 'd'), borde('optim', 'i'), 'pérdida de\nvalidación', dy=0.08)
    ax.text(pos['optim'][0] + w / 2, pos['optim'][1] - 0.15, 'ajusta la tasa con\nla pérdida de validación',
            ha='center', va='top', fontsize=7.4, color=SUAVE, style='italic')
    flecha(borde('evalua', 'i'), borde('seleccion', 'd'), 'AP@0,5 de\ncada época', dy=0.08)
    flecha((pos['seleccion'][0], pos['seleccion'][1] + h * 0.3), (pos['test'][0] + w * 0.75, pos['test'][1] + h),
           'mejor modelo\ny umbral', dx=-0.2, dy=0.15, ha='right', va='center')
    flecha(borde('datos_test', 'i'), borde('test', 'd'), 'imágenes de\notros grupos', dy=0.08)
    ax.text(pos['test'][0] + w / 2, pos['test'][1] - 0.18, 'métricas finales: AP, precisión,\nexhaustividad y F1',
            ha='center', va='top', fontsize=7.4, color=SUAVE, style='italic')
    for g, (texto, x, y) in {'ent': ('Cada lote: entrenamiento', 0.2, 7.05),
                             'val': ('Cada época: validación', 7.4, 7.05),
                             'test': ('Una vez: test', 14.4, 7.05)}.items():
        fondo, bordeg = grupos[g]
        ax.add_patch(FancyBboxPatch((x, y - 0.12), 0.38, 0.3, boxstyle='round,pad=0.01', fc=fondo, ec=bordeg))
        ax.text(x + 0.55, y + 0.03, texto, va='center', fontsize=8.2, color=TINTA)
    fig.savefig(FIG / 'sistema_entrenamiento.png', dpi=240, bbox_inches='tight')
    plt.close(fig)


# --- C2.7: curva precisión-exhaustividad ---------------------------------------------------
def leer(modelo):
    with open(TEST / f'{modelo}_aug_robusto_v1_lr001_test' / 'umbral_confianza.csv', encoding='utf-8') as f:
        filas = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    return sorted(filas, key=lambda r: r['umbral'])


def curva_pr():
    modelos = [('faster_rcnn_v2', 'Faster R-CNN v2 (modelo final)', '#1F5FA8', 0.95),
               ('faster_rcnn_v3', 'Faster R-CNN MobileNet', '#D9692B', 0.55)]
    fig, ejes = plt.subplots(1, 2, figsize=(8.4, 3.3), gridspec_kw={'width_ratios': [1, 1.25]})
    for ax, zoom in zip(ejes, (False, True)):
        for modelo, nombre, color, elegido in modelos:
            f = leer(modelo)
            r, p = [x['recall'] for x in f], [x['precision'] for x in f]
            ax.plot(r, p, '-o', color=color, lw=1.8, ms=3.2 if zoom else 2.2, label=nombre)
            e = next(x for x in f if abs(x['umbral'] - elegido) < 1e-6)
            ax.plot(e['recall'], e['precision'], 'o', ms=8, mfc='white', mec=color, mew=2)
            if zoom:
                for x in f:
                    es_elegido = abs(x['umbral'] - elegido) < 1e-6
                    cerca = abs(x['umbral'] - elegido) < 0.1      # su etiqueta pisaría la del elegido
                    if es_elegido or (x['umbral'] in (0.05, 0.25, 0.5, 0.75) and not cerca):
                        ax.annotate(coma(x['umbral']), (x['recall'], x['precision']), xytext=(6, 4),
                                    textcoords='offset points', fontsize=7, color=color)
        if zoom:
            ax.set(xlim=(0.89, 0.982), ylim=(0.6, 0.97), title='Detalle con el umbral de cada punto')
        else:
            ax.set(xlim=(0, 1.02), ylim=(0, 1.02), title='Curva completa')
            ax.plot([1], [1], marker='*', ms=11, color='#9CA3AF', clip_on=False)
            ax.annotate('detector ideal', (1, 1), xytext=(0.5, 0.42), textcoords='data', fontsize=7.5,
                        color=SUAVE, arrowprops=dict(arrowstyle='-', color='#9CA3AF', lw=0.8))
            ax.add_patch(plt.Rectangle((0.89, 0.6), 0.092, 0.37, fill=False, ec='#9CA3AF', ls='--', lw=0.9))
            ax.legend(frameon=False, fontsize=7.6, loc='lower left')
        ax.set(xlabel='Exhaustividad', ylabel='Precisión')
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: coma(v)))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: coma(v)))
    ejes[1].text(0.892, 0.615, 'círculo blanco: umbral fijado en validación', fontsize=7.2, color=SUAVE)
    plt.tight_layout()
    fig.savefig(FIG / 'curva_pr.png', dpi=240)
    plt.close(fig)


# --- Bloque 3: imágenes del laboratorio -----------------------------------------------------
LABORATORIO = [
    ('20261104_164735/002_P1_confirmado_yaw+4.jpg', 'a) Rival detectado y centrado'),
    ('20261105_181923/001_P1_barrido_yaw+0.jpg', 'b) Foto del robot en su caja'),
    ('20261105_192026/004_P1_sin_confirmar_yaw+38.jpg', 'c) Imagen corrupta del vídeo'),
]


def laboratorio():
    rutas = [EVIDENCIAS / r for r, _ in LABORATORIO]
    if not all(r.is_file() for r in rutas):
        print('Faltan evidencias del laboratorio; no se rehace bloque3/laboratorio.jpg')
        return
    ancho, alto, pie, sep = 760, 428, 40, 12
    lienzo = Image.new('RGB', (3 * ancho + 2 * sep, alto + pie), 'white')
    dibujo = ImageDraw.Draw(lienzo)
    try:
        letra = ImageFont.truetype('DejaVuSans.ttf', 24)
    except OSError:
        letra = ImageFont.truetype(str(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf'), 24)
    for i, (ruta, (_, texto)) in enumerate(zip(rutas, LABORATORIO)):
        im = Image.open(ruta).convert('RGB').resize((ancho, alto), Image.LANCZOS)
        x = i * (ancho + sep)
        lienzo.paste(im, (x, 0))
        dibujo.text((x + ancho / 2, alto + pie / 2), texto, fill=TINTA, font=letra, anchor='mm')
    (FIG / 'bloque3').mkdir(exist_ok=True)
    lienzo.save(FIG / 'bloque3' / 'laboratorio.jpg', quality=88)


if __name__ == '__main__':
    sistema()
    curva_pr()
    laboratorio()
    print('Figuras en', FIG)
