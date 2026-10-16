"""Compara lr=0,0001 y lr=0,001 a partir de métricas ya calculadas en validación."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / 'ENTREGA 1/WEEK2'
DESTINO = BASE / 'comparaciones/lr001'


def leer_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def generar():
    DESTINO.mkdir(parents=True, exist_ok=True)
    experimentos = ['faster_rcnn_v1_aug', 'faster_rcnn_v1_aug_lr001']
    historias = [leer_csv(BASE / 'resultados_train' / e / 'historial.csv') for e in experimentos]
    mapas = [{r['grupo']: r for r in leer_csv(BASE / 'resultados_test' / (e + '_val') / 'map.csv')}
             for e in experimentos]
    videos = [{r['grupo']: r for r in leer_csv(BASE / 'resultados_test' / (e + '_val') / 'errores_por_video.csv')}
              for e in experimentos]
    assert all(len(h) == 30 for h in historias)
    assert set(videos[0]) == set(videos[1])
    for grupo in videos[0]:
        for k in ('imagenes', 'robots', 'robots_normales', 'robots_difficult'):
            assert videos[0][grupo][k] == videos[1][grupo][k], (grupo, k)
    filas = []
    for grupo, claves in [('todos', ('map_50', 'map', 'map_75', 'map_small')),
                         ('normales', ('map_50', 'map')),
                         ('difficult', ('map_50', 'map'))]:
        for k in claves:
            a, b = (float(m[grupo][k]) for m in mapas)
            filas.append(dict(grupo=grupo, metrica=k, lr0001=a, lr001=b, diferencia_puntos=round(100*(b-a), 4)))
    por_video = []
    for grupo in videos[0]:
        a, b = videos[0][grupo], videos[1][grupo]
        por_video.append(dict(secuencia=grupo, ap50_lr0001=float(a['map_50']), ap50_lr001=float(b['map_50']),
            diferencia_puntos=round(100*(float(b['map_50'])-float(a['map_50'])), 4),
            fp_lr0001=int(a['fp']), fp_lr001=int(b['fp']), fn_lr0001=int(a['fn']), fn_lr001=int(b['fn']),
            fn_difficult_lr0001=int(a['fn_difficult']), fn_difficult_lr001=int(b['fn_difficult'])))
    for nombre, datos in [('metricas_comparadas.csv', filas), ('secuencias_comparadas.csv', por_video)]:
        with (DESTINO / nombre).open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(datos[0]))
            w.writeheader(); w.writerows(datos)

    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
        'axes.spines.top':False, 'axes.spines.right':False, 'axes.grid':True,
        'grid.alpha':0.2, 'axes.titleweight':'bold', 'axes.axisbelow':True})
    colores, etiquetas = ['#25476A', '#C46728'], ['lr inicial 0,0001', 'lr inicial 0,001']
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.2), constrained_layout=True)
    for ax, clave, titulo in zip(axes.flat, ['train_loss', 'valid_loss', 'valid_map_50', 'valid_map'],
        ['Pérdida de entrenamiento', 'Pérdida de validación', 'AP a IoU 0,50 en validación', 'AP a IoU 0,50 a 0,95 en validación']):
        for h, color, etiqueta in zip(historias, colores, etiquetas):
            xs = [int(r['epoch']) for r in h]; ys = [float(r[clave]) for r in h]
            ax.plot(xs, ys, color=color, label=etiqueta, linewidth=2)
            if clave.startswith('valid_map'):
                j = int(np.argmax([float(r['valid_map_50']) for r in h]))
                ax.scatter(xs[j], ys[j], s=42, color=color, zorder=5)
                ax.annotate('época '+str(xs[j]), (xs[j], ys[j]), xytext=(0, -17 if j>10 else 10),
                            textcoords='offset points', ha='center', fontsize=8, color=color)
        ax.set_title(titulo, fontsize=11); ax.set_xlabel('Época'); ax.set_ylabel('Pérdida' if 'loss' in clave else 'AP')
        ax.set_xlim(1,30)
    axes[0,0].legend(frameon=False, fontsize=9)
    fig.savefig(DESTINO / 'curvas_comparadas.png', dpi=240)
    fig.savefig(DESTINO / 'curvas_comparadas.pdf')
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 3.2), constrained_layout=True)
    for h, color, etiqueta in zip(historias, colores, etiquetas):
        ax.step([int(r['epoch']) for r in h], [float(r['lr']) for r in h], where='mid', color=color, label=etiqueta, linewidth=2)
    ax.set_yscale('log'); ax.set_xlabel('Época'); ax.set_ylabel('Tasa de aprendizaje usada')
    ax.set_title('ReduceLROnPlateau con pérdida de validación'); ax.legend(frameon=False)
    fig.savefig(DESTINO / 'lr_comparado.png', dpi=240); plt.close(fig)
    datos = sorted(por_video[1:], key=lambda r:r['diferencia_puntos'])
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ys = np.arange(len(datos)); vals = [r['diferencia_puntos'] for r in datos]
    ax.barh(ys, vals, color=['#B54F40' if v<0 else '#337C68' for v in vals])
    ax.set_yticks(ys, [r['secuencia'].replace('PIDS','') for r in datos], fontsize=9)
    ax.axvline(0, color='#555', linewidth=1); ax.set_xlabel('Cambio de AP@0,50 en puntos porcentuales')
    ax.set_title('Efecto del cambio de lr por secuencia de validación')
    for y, v in zip(ys, vals): ax.text(v + (0.04 if v>=0 else -0.04), y, f'{v:+.2f}', va='center', ha='left' if v>=0 else 'right', fontsize=9)
    ax.set_xlim(-1.2,4.1); fig.savefig(DESTINO / 'secuencias_comparadas.png', dpi=240); plt.close(fig)

    resumen = dict(experimentos=experimentos, conjunto='val', semilla=0,
        mejores_epocas=[max(h, key=lambda r:float(r['valid_map_50'])) for h in historias],
        metricas=filas, por_video=por_video,
        notas=['Los puntos de las curvas se seleccionan por AP50, no por AP 0,50:0,95.',
               'Las evaluaciones finales y el historial por época se presentan por separado.',
               'Una única semilla; diferencias pequeñas no prueban una mejora estable.',
               'Hay etiquetas incompletas en validación; los FP son recuentos frente a esas etiquetas.'])
    (DESTINO / 'comparacion.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return resumen


if __name__ == '__main__':
    print(json.dumps(generar()['mejores_epocas'], ensure_ascii=False))
