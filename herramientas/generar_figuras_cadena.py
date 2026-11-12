"""Figuras de la memoria con los resultados de la cadena de entrenamientos (validación y test).

Lee ENTREGA 1/WEEK2/cadena/resumen.csv (validación), resumen_test.csv (test, si existe) y los historiales,
y escribe en docs/informes/figuras/. Uso: python herramientas/generar_figuras_cadena.py
"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
WEEK2 = RAIZ / 'ENTREGA 1' / 'WEEK2'
SALIDA = RAIZ / 'docs' / 'informes' / 'figuras'
PERFIL = 'robusto_v1'

# Los siete modelos con lr 0,001, de la mayor a la menor precisión en validación
NOMBRES = {'faster_rcnn_v2': 'Faster R-CNN v2', 'retinanet_v2': 'RetinaNet v2', 'faster_rcnn_v1': 'Faster R-CNN v1',
           'retinanet_v1': 'RetinaNet v1', 'faster_rcnn_v3': 'Faster R-CNN MobileNet', 'ssd_v1': 'SSD300 VGG16',
           'ssd_v2': 'SSDlite320'}
COLORES = {'faster_rcnn_v2': '#2463A6', 'retinanet_v2': '#C65D23', 'faster_rcnn_v1': '#6E9BCB', 'retinanet_v1': '#E0A070',
           'faster_rcnn_v3': '#2E8B57', 'ssd_v1': '#8E6BB5', 'ssd_v2': '#8496A8'}
TINTA = '#172B40'
# Etiquetas cortas para el eje de las barras
CORTAS = {'faster_rcnn_v2': 'Faster\nR-CNN v2', 'retinanet_v2': 'RetinaNet\nv2', 'faster_rcnn_v1': 'Faster\nR-CNN v1',
          'retinanet_v1': 'RetinaNet\nv1', 'faster_rcnn_v3': 'Faster\nR-CNN\nMobile', 'ssd_v1': 'SSD300\nVGG16',
          'ssd_v2': 'SSDlite\n320'}


def leer(ruta):
    with open(ruta, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def coma(ax):
    """Eje vertical con coma decimal, como en el resto de la memoria."""
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.2f}'.replace('.', ',')))


def estilo():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': '#CDD6DF', 'axes.labelcolor': TINTA,
                         'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': 'white'})


def curvas_arquitecturas():
    """AP@0,5 de validación por época de las siete arquitecturas (lr 0,001); el punto marca la mejor época."""
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    for modelo, nombre in NOMBRES.items():
        filas = leer(WEEK2 / 'resultados_train' / f'{modelo}_aug_{PERFIL}_lr001' / 'historial.csv')
        epocas = [int(f['epoch']) for f in filas]
        ap = [float(f['valid_map_50']) for f in filas]
        mejor = max(range(len(ap)), key=ap.__getitem__)
        ax.plot(epocas, ap, color=COLORES[modelo], linewidth=1.8, label=nombre)
        ax.plot(epocas[mejor], ap[mejor], 'o', color=COLORES[modelo], markersize=6)
    ax.set_ylim(0.86, 0.96)
    coma(ax)
    ax.set_xlim(1, 12)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel('Época')
    ax.set_ylabel('AP@0,5 en validación')
    ax.grid(axis='y', color='#E5EBF0')
    ax.text(0.99, 0.02, 'SSDlite320 (0,57–0,68) y los primeros valores de SSD300 y RetinaNet quedan fuera de escala',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=8, color='#53677A')
    ax.legend(fontsize=8.5, frameon=False, loc='upper left', bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    fig.savefig(SALIDA / 'curvas_arquitecturas.png', dpi=200)
    plt.close(fig)


def precision_latencia():
    """AP@0,5 en validación frente al tiempo por imagen (escala logarítmica); las variantes de lr, en pequeño."""
    filas = leer(WEEK2 / 'cadena' / 'resumen.csv')
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for f in filas:
        modelo = f['modelo']
        principal = float(f['lr']) == 0.001
        ax.scatter(float(f['ms_una_a_una']), float(f['ap50_todos']), s=70 if principal else 22, color=COLORES[modelo],
                   alpha=1 if principal else 0.55, zorder=3 if principal else 2, edgecolor='white' if principal else 'none')
        if principal:
            desplazamiento = {'ssd_v2': (6, 0), 'ssd_v1': (6, -2), 'faster_rcnn_v3': (6, 4), 'retinanet_v2': (-9, -2),
                              'retinanet_v1': (-8, -12), 'faster_rcnn_v1': (9, -4), 'faster_rcnn_v2': (-8, 7)}[modelo]
            ax.annotate(NOMBRES[modelo], (float(f['ms_una_a_una']), float(f['ap50_todos'])), textcoords='offset points',
                        xytext=desplazamiento, ha='left' if desplazamiento[0] > 0 else 'right', fontsize=8.5, color=TINTA)
    ax.set_xscale('log')
    ax.set_xticks([4, 10, 20, 50, 100])
    ax.set_xticklabels(['4', '10', '20', '50', '100'])
    ax.set_ylim(0.88, 0.96)
    coma(ax)
    ax.set_xlabel('Tiempo por imagen, de una en una (ms, escala logarítmica)')
    ax.set_ylabel('AP@0,5 en validación')
    ax.grid(color='#E5EBF0')
    ax.text(0.01, 0.02, 'SSDlite320 (AP@0,5 0,68) queda fuera de escala. Círculos pequeños: lr 0,0005 y 0,002.',
            transform=ax.transAxes, fontsize=8, color='#53677A')
    fig.tight_layout()
    fig.savefig(SALIDA / 'precision_latencia.png', dpi=200)
    plt.close(fig)


def validacion_vs_test():
    """AP@0,5 en validación y en test, para todos los robots y para los difficult."""
    ruta = WEEK2 / 'cadena' / 'resumen_test.csv'
    if not ruta.exists():
        print('Sin resumen_test.csv: no se dibuja validacion_vs_test.png')
        return
    val = {f['modelo']: f for f in leer(WEEK2 / 'cadena' / 'resumen.csv') if float(f['lr']) == 0.001}
    test = {f['modelo']: f for f in leer(ruta) if float(f['lr']) == 0.001}
    modelos = [m for m in NOMBRES if m in test]
    fig, ejes = plt.subplots(1, 2, figsize=(10, 4.3), sharey=False)
    for ax, columna, titulo in ((ejes[0], 'ap50_todos', 'Todos los robots'), (ejes[1], 'ap50_difficult', 'Solo difficult')):
        x = range(len(modelos))
        ax.bar([i - 0.2 for i in x], [float(val[m][columna]) for m in modelos], width=0.4, color='#A6B4C2', label='Validación')
        ax.bar([i + 0.2 for i in x], [float(test[m][columna]) for m in modelos], width=0.4, color='#2463A6', label='Test')
        ax.set_xticks(list(x))
        ax.set_xticklabels([CORTAS[m] for m in modelos], fontsize=7.5)
        ax.set_title(titulo, fontsize=10, color=TINTA)
        ax.set_ylabel('AP@0,5')
        ax.grid(axis='y', color='#E5EBF0')
        ax.set_axisbelow(True)
    ejes[0].set_ylim(0.6, 1.0)
    ejes[1].set_ylim(0.2, 0.7)
    coma(ejes[0])
    coma(ejes[1])
    ejes[0].legend(frameon=False, fontsize=8.5, loc='upper right')
    fig.tight_layout()
    fig.savefig(SALIDA / 'validacion_vs_test.png', dpi=200)
    plt.close(fig)


def etiqueta_exp(modelo, lr):
    return f"{NOMBRES[modelo]} · lr {f'{lr:.4f}'.rstrip('0').replace('.', ',') if lr < 0.001 else f'{lr:.3f}'.replace('.', ',')}"


def tasa_aprendizaje():
    """AP@0,5 de validación por época con las tres tasas, para los tres modelos que se repitieron."""
    val = {(f['modelo'], float(f['lr'])): f for f in leer(WEEK2 / 'cadena' / 'resumen.csv')}
    estilos = {0.0005: ('#6E9BCB', ':', 'lr 0,0005'), 0.001: ('#2463A6', '-', 'lr 0,001'), 0.002: ('#C65D23', '--', 'lr 0,002')}
    fig, ejes = plt.subplots(1, 3, figsize=(8.6, 3.6), sharey=True)
    for ax, modelo in zip(ejes, ['faster_rcnn_v2', 'retinanet_v2', 'faster_rcnn_v1']):
        for lr, (color, trazo, etiqueta) in estilos.items():
            filas = leer(WEEK2 / 'resultados_train' / f"{modelo}_aug_{PERFIL}_lr{str(lr).replace('0.', '')}" / 'historial.csv')
            ap = [float(f['valid_map_50']) for f in filas]
            mejor = max(range(len(ap)), key=ap.__getitem__)
            ax.plot(range(1, len(ap) + 1), ap, color=color, linestyle=trazo, linewidth=1.8, label=etiqueta)
            ax.plot(mejor + 1, ap[mejor], 'D', color=color, markersize=6.5, markeredgecolor='white')
        ax.set_title(NOMBRES[modelo], fontsize=10, color=TINTA)
        ax.set_xlabel('Época')
        ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
        ax.set_ylim(0.928, 0.955)
        ax.set_yticks([0.93, 0.935, 0.94, 0.945, 0.95])
        ax.grid(axis='y', color='#E5EBF0')
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.3f}'.replace('.', ',')))
    ejes[0].set_ylabel('AP@0,5 en validación')
    ejes[0].legend(fontsize=8.5, frameon=False, loc='lower right')
    fig.tight_layout()
    fig.savefig(SALIDA / 'tasa_aprendizaje.png', dpi=200)
    plt.close(fig)


def coste_entrenamiento():
    """Minutos de entrenamiento (total y hasta el mejor checkpoint, estimado) de los 13 entrenamientos."""
    filas = sorted(leer(WEEK2 / 'cadena' / 'resumen.csv'), key=lambda f: -float(f['minutos_train']))
    etiquetas = [etiqueta_exp(f['modelo'], float(f['lr'])) for f in filas]
    total = [float(f['minutos_train']) for f in filas]
    hasta = [t * int(f['mejor_epoca']) / int(f['epocas']) for t, f in zip(total, filas)]
    colores = [COLORES[f['modelo']] for f in filas]
    y = list(range(len(filas)))
    fig, ejes = plt.subplots(1, 2, figsize=(8.4, 4.4), gridspec_kw={'width_ratios': [1.5, 1]})
    ax = ejes[0]
    ax.barh(y, total, color='#D5DCE4', height=0.68, label='Entrenamiento completo')
    ax.barh(y, hasta, color=colores, height=0.68, label='Hasta el mejor checkpoint (estimado)')
    for yi, t in zip(y, total):
        ax.text(t + 2, yi, f'{t:.0f}'.replace('.', ','), va='center', fontsize=8, color=TINTA)
    ax.set_yticks(y)
    ax.set_yticklabels(etiquetas, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel('Minutos')
    ax.set_xlim(0, 215)
    ax.grid(axis='x', color='#E5EBF0')
    ax.set_axisbelow(True)
    ax.legend(fontsize=7.5, frameon=False, loc='lower right')
    ax = ejes[1]
    for yi, f in zip(y, filas):
        ax.plot([1, int(f['epocas'])], [yi, yi], color='#D5DCE4', linewidth=6, solid_capstyle='butt')
        ax.plot(int(f['mejor_epoca']), yi, 'D', color=COLORES[f['modelo']], markersize=7, markeredgecolor='white')
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.invert_yaxis()
    ax.set_xlabel('Época (rombo: mejor checkpoint)')
    ax.set_xlim(0.5, 15.5)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.grid(axis='x', color='#E5EBF0')
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(SALIDA / 'coste_entrenamiento.png', dpi=200)
    plt.close(fig)


def errores_test():
    """Errores en test de los siete modelos y curvas de umbral del modelo final."""
    ruta = WEEK2 / 'cadena' / 'resumen_test.csv'
    if not ruta.exists():
        print('Sin resumen_test.csv: no se dibuja errores_test.png')
        return
    test = {f['modelo']: f for f in leer(ruta) if float(f['lr']) == 0.001}
    modelos = [m for m in NOMBRES if m in test]
    fig, ejes = plt.subplots(1, 2, figsize=(8.6, 4.0), gridspec_kw={'width_ratios': [1.2, 1]})
    ax = ejes[0]
    x = range(len(modelos))
    series = [('Falsos positivos', lambda f: float(f['fp']), '#C65D23'), ('Robots normales perdidos', lambda f: float(f['fn']) - float(f['fn_difficult']), '#2463A6'),
              ('Robots difficult perdidos', lambda f: float(f['fn_difficult']), '#8E6BB5')]
    for k, (nombre, fn, color) in enumerate(series):
        valores = [fn(test[m]) for m in modelos]
        barras = ax.bar([i + (k - 1) * 0.27 for i in x], valores, width=0.27, color=color, label=nombre)
        for b, v in zip(barras, valores):
            if v < 300:
                ax.text(b.get_x() + b.get_width() / 2, v + 6, f'{v:.0f}', ha='center', fontsize=6.5, color=TINTA)
    ax.set_xticks(list(x))
    ax.set_xticklabels([CORTAS[m] for m in modelos], fontsize=7.5)
    ax.set_ylabel('Errores en test (1721 robots)')
    ax.grid(axis='y', color='#E5EBF0')
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc='upper left')
    ax = ejes[1]
    detalle = WEEK2 / 'resultados_test' / f'faster_rcnn_v2_aug_{PERFIL}_lr001_test' / 'umbral_confianza.csv'
    filas = leer(detalle)
    u = [float(f['umbral']) for f in filas]
    for columna, nombre, color, trazo in (('precision', 'Precisión', '#2463A6', '-'), ('recall', 'Exhaustividad', '#C65D23', '-'),
                                          ('recall_difficult', 'Exhaustividad difficult', '#8E6BB5', '--'), ('f1', 'F1', TINTA, '-')):
        ax.plot(u, [float(f[columna]) for f in filas], color=color, linestyle=trazo, linewidth=1.8, label=nombre)
    ax.axvline(0.95, color='#788797', linestyle=':', linewidth=1.3)
    ax.text(0.935, 0.53, 'umbral fijado' + chr(10) + 'en validación', ha='right', fontsize=7.5, color='#53677A')
    ax.set_ylim(0.4, 1.0)
    ax.set_xlabel('Umbral de confianza')
    ax.set_title('Faster R-CNN v2 (modelo final)', fontsize=9.5, color=TINTA)
    ax.grid(color='#E5EBF0')
    ax.legend(fontsize=7.5, frameon=False, loc='lower center', ncol=2)
    coma(ax)
    fig.tight_layout()
    fig.savefig(SALIDA / 'errores_test.png', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    estilo()
    SALIDA.mkdir(parents=True, exist_ok=True)
    curvas_arquitecturas()
    precision_latencia()
    validacion_vs_test()
    tasa_aprendizaje()
    coste_entrenamiento()
    errores_test()
    print('Figuras en', SALIDA)
