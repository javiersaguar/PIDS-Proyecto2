"""Monta la web de figuras interactivas (GitHub Pages) en una carpeta.

Uso: python herramientas/construir_web.py <destino>

- Copia la página única `web/index.html` y `plotly.min.js`.
- Extrae los datos de las tres figuras interactivas del EDA de sus HTML
  (los genera `visualizaciones_eda.py`) y los guarda como JSON.
- Construye las figuras del Bloque 2 a partir de los CSV de
  `ENTREGA 1/WEEK2/resultados_train/` y `resultados_test/`.
- Copia también la carpeta del EDA tal cual, para no romper enlaces antiguos.

Solo usa la biblioteca estándar: se ejecuta en GitHub Actions sin instalar nada.
"""

import csv
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EDA = RAIZ / 'ENTREGA 1' / 'WEEK1' / 'resultados_eda'
WEEK2 = RAIZ / 'ENTREGA 1' / 'WEEK2'

AZUL, NARANJA, TINTA, GRIS = '#2463A6', '#C65D23', '#172B40', '#8496A8'

# Experimentos en el orden en que se hicieron: (carpeta, nombre corto, color)
EXPERIMENTOS = [
    ('faster_rcnn_v1_sin_aug', 'Sin aumento · lr 0,0001', '#A6B4C2'),
    ('faster_rcnn_v1_aug', 'Con aumento · lr 0,0001', '#6E9BCB'),
    ('faster_rcnn_v1_aug_lr001', 'Con aumento · lr 0,001', AZUL),
    ('faster_rcnn_v1_aug_lr001_res1024', 'lr 0,001 · resolución 1024', NARANJA),
]


def extraer_figura(html: Path) -> dict:
    """Recupera data, layout, config y frames de un HTML generado por plotly.write_html."""
    texto = html.read_text(encoding='utf-8')
    decodificador = json.JSONDecoder()

    def valores(desde, cuantos):
        salida, i = [], desde
        for _ in range(cuantos):
            while texto[i] in ' \n\r\t,':
                i += 1
            valor, i = decodificador.raw_decode(texto, i)
            salida.append(valor)
        return salida

    inicio = texto.index('Plotly.newPlot(') + len('Plotly.newPlot(')
    _, data, layout, config = valores(inicio, 4)
    figura = {'data': data, 'layout': layout, 'config': config, 'frames': []}
    marca = texto.find('Plotly.addFrames(')
    if marca >= 0:
        i = texto.index(',', marca) + 1
        figura['frames'] = valores(i, 1)[0]
    return figura


def leer_csv(ruta: Path) -> list:
    with open(ruta, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def estilo(layout: dict, alto: int) -> dict:
    base = {
        'template': 'plotly_white', 'height': alto, 'autosize': True, 'separators': ',.',
        'font': {'family': 'Arial, sans-serif', 'size': 13, 'color': TINTA},
        'margin': {'l': 60, 'r': 20, 't': 40, 'b': 120}, 'paper_bgcolor': 'white',
        'hoverlabel': {'bgcolor': 'white', 'font': {'size': 13}},
        'legend': {'orientation': 'h', 'x': 0, 'y': -0.16, 'yanchor': 'top'},
    }
    base.update(layout)
    return base


def curvas_por_experimento() -> dict:
    """Época a época de un experimento: pérdidas de entrenamiento y validación, y AP de validación.

    Un desplegable elige el experimento; la línea punteada marca la mejor época (mayor AP@0,5).
    """
    series = [('train_loss', 'Pérdida de entrenamiento', 'x', 'y', AZUL, 'solid'),
              ('valid_loss', 'Pérdida de validación', 'x', 'y', NARANJA, 'solid'),
              ('valid_map_50', 'AP@0,5 (validación)', 'x2', 'y2', AZUL, 'solid'),
              ('valid_map', 'AP 0,50:0,95 (validación)', 'x2', 'y2', NARANJA, 'dash')]
    data, botones = [], []
    por_defecto = 2                       # lr 0,001, el modelo de referencia
    for k, (carpeta, nombre, _) in enumerate(EXPERIMENTOS):
        filas = leer_csv(WEEK2 / 'resultados_train' / carpeta / 'historial.csv')
        epocas = [int(f['epoch']) for f in filas]
        tasas = [float(f['lr']) for f in filas]
        mejor = max(range(len(filas)), key=lambda i: float(filas[i]['valid_map_50']))
        for columna, etiqueta, x, y, color, trazo in series:
            data.append({
                'type': 'scatter', 'mode': 'lines+markers', 'name': etiqueta, 'visible': k == por_defecto,
                'x': epocas, 'y': [round(float(f[columna]), 4) for f in filas], 'xaxis': x, 'yaxis': y,
                'customdata': [f'{t:.0e}'.replace('e-0', 'e-') for t in tasas],
                'line': {'color': color, 'width': 2, 'dash': trazo}, 'marker': {'size': 4},
                'hovertemplate': f'{etiqueta}<br>Época %{{x}} · %{{y:.3f}}<br>Tasa de aprendizaje %{{customdata}}<extra></extra>',
            })
        lineas = [{'type': 'line', 'xref': eje, 'yref': 'paper', 'x0': epocas[mejor], 'x1': epocas[mejor],
                   'y0': 0, 'y1': 1, 'line': {'color': GRIS, 'width': 1, 'dash': 'dot'}} for eje in ('x', 'x2')]
        nota = {'text': f'mejor época: {epocas[mejor]}', 'x': epocas[mejor], 'xref': 'x2', 'y': 0.02,
                'yref': 'paper', 'xanchor': 'left', 'showarrow': False, 'font': {'size': 11, 'color': GRIS}}
        visibles = [j // len(series) == k for j in range(len(EXPERIMENTOS) * len(series))]
        botones.append({'label': nombre, 'method': 'update',
                        'args': [{'visible': visibles}, {'shapes': lineas, 'annotations': TITULOS_EPOCAS + [nota]}]})
    inicial = botones[por_defecto]['args'][1]
    layout = estilo({
        'xaxis': {'title': {'text': 'Época'}, 'domain': [0, 0.45], 'anchor': 'y'},
        'yaxis': {'title': {'text': 'Pérdida'}, 'rangemode': 'tozero', 'anchor': 'x'},
        'xaxis2': {'title': {'text': 'Época'}, 'domain': [0.57, 1], 'anchor': 'y2'},
        'yaxis2': {'title': {'text': 'AP en validación'}, 'autorange': True, 'anchor': 'x2'},
        'shapes': inicial['shapes'], 'annotations': inicial['annotations'],
        'margin': {'l': 60, 'r': 20, 't': 90, 'b': 120},
        'updatemenus': [{'type': 'dropdown', 'buttons': botones, 'active': por_defecto,
                         'x': 0, 'xanchor': 'left', 'y': 1.2, 'yanchor': 'top', 'showactive': True}],
    }, 560)
    return {'data': data, 'layout': layout}


TITULOS_EPOCAS = [
    {'text': '<b>Pérdida por época</b>', 'x': 0.225, 'y': 1.04, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
    {'text': '<b>AP en validación por época</b>', 'x': 0.785, 'y': 1.04, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
]


def evaluacion_test():
    """Resultado final en test, solo si ya existe alguna carpeta resultados_test/<experimento>_test.

    Compara el AP@0,5 por grupo en validación y en test, y añade la curva del umbral de
    confianza cuando test.ipynb ha guardado umbral_confianza.csv.
    """
    evaluados = [(c, n) for c, n, _ in EXPERIMENTOS if (WEEK2 / 'resultados_test' / f'{c}_test' / 'map.csv').exists()]
    if not evaluados:
        return None
    carpeta, nombre = evaluados[-1]
    grupos = [('todos', 'Todos'), ('normales', 'Normales'), ('difficult', 'Difficult')]
    data = []
    for conjunto, color in (('val', '#A6B4C2'), ('test', AZUL)):
        mapa = {f['grupo']: f for f in leer_csv(WEEK2 / 'resultados_test' / f'{carpeta}_{conjunto}' / 'map.csv')}
        data.append({'type': 'bar', 'name': 'Validación' if conjunto == 'val' else 'Test', 'marker': {'color': color},
                     'x': [g[1] for g in grupos], 'y': [float(mapa[g[0]]['map_50']) for g in grupos],
                     'hovertemplate': '%{x}: AP@0,5 %{y:.3f}<extra></extra>'})
    layout = {'barmode': 'group', 'xaxis': {'domain': [0, 0.45], 'anchor': 'y'},
              'yaxis': {'title': {'text': f'AP@0,5 · {nombre}'}, 'range': [0, 1], 'anchor': 'x'}}
    umbral = WEEK2 / 'resultados_test' / f'{carpeta}_test' / 'umbral_confianza.csv'
    if umbral.exists():
        filas = leer_csv(umbral)
        for columna, etiqueta, color, trazo in (('precision', 'Precisión', AZUL, 'solid'),
                                                ('recall', 'Exhaustividad', NARANJA, 'solid'),
                                                ('f1', 'F1', TINTA, 'solid'),
                                                ('recall_difficult', 'Exhaustividad difficult', NARANJA, 'dash')):
            data.append({'type': 'scatter', 'mode': 'lines+markers', 'name': etiqueta, 'xaxis': 'x2', 'yaxis': 'y2',
                         'x': [float(f['umbral']) for f in filas], 'y': [float(f[columna]) for f in filas],
                         'line': {'color': color, 'width': 2, 'dash': trazo}, 'marker': {'size': 4},
                         'hovertemplate': f'{etiqueta}<br>Umbral %{{x:.2f}} · %{{y:.3f}}<extra></extra>'})
        layout.update({'xaxis2': {'title': {'text': 'Umbral de confianza'}, 'domain': [0.57, 1], 'anchor': 'y2'},
                       'yaxis2': {'range': [0, 1.02], 'anchor': 'x2'}})
    else:
        layout['xaxis']['domain'] = [0, 1]
    return {'data': data, 'layout': estilo(layout, 500)}


def curvas_entrenamiento() -> dict:
    """AP@0,5 y pérdida de validación por época de los cuatro experimentos."""
    data = []
    for carpeta, nombre, color in EXPERIMENTOS:
        filas = leer_csv(WEEK2 / 'resultados_train' / carpeta / 'historial.csv')
        epocas = [int(f['epoch']) for f in filas]
        for eje, columna, muestra in (('y', 'valid_map_50', True), ('y2', 'valid_loss', False)):
            data.append({
                'type': 'scatter', 'mode': 'lines+markers', 'name': nombre, 'legendgroup': nombre,
                'showlegend': muestra, 'x': epocas, 'y': [round(float(f[columna]), 4) for f in filas],
                'xaxis': 'x' if eje == 'y' else 'x2', 'yaxis': eje,
                'line': {'color': color, 'width': 2}, 'marker': {'size': 4},
                'hovertemplate': f'{nombre}<br>Época %{{x}}<br>%{{y:.3f}}<extra></extra>',
            })
    layout = estilo({
        'xaxis': {'title': {'text': 'Época'}, 'domain': [0, 0.45], 'anchor': 'y'},
        'yaxis': {'title': {'text': 'AP@0,5 en validación'}, 'range': [0.5, 1], 'anchor': 'x'},
        'xaxis2': {'title': {'text': 'Época'}, 'domain': [0.57, 1], 'anchor': 'y2'},
        'yaxis2': {'title': {'text': 'Pérdida en validación'}, 'anchor': 'x2'},
        'annotations': [
            {'text': '<b>AP@0,5 por época</b>', 'x': 0.23, 'y': 1.08, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
            {'text': '<b>Pérdida por época</b>', 'x': 0.77, 'y': 1.08, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
        ],
    }, 540)
    return {'data': data, 'layout': layout}


def resultados_por_grupo() -> dict:
    """AP@0,5 por grupo de robots y recuento de errores con confianza 0,5."""
    grupos = [('todos', 'Todos'), ('normales', 'Normales'), ('difficult', 'Difficult')]
    data = []
    for carpeta, nombre, color in EXPERIMENTOS:
        mapa = {f['grupo']: f for f in leer_csv(WEEK2 / 'resultados_test' / f'{carpeta}_val' / 'map.csv')}
        total = leer_csv(WEEK2 / 'resultados_test' / f'{carpeta}_val' / 'errores_por_video.csv')[0]
        data.append({
            'type': 'bar', 'name': nombre, 'legendgroup': nombre, 'marker': {'color': color},
            'x': [g[1] for g in grupos], 'y': [float(mapa[g[0]]['map_50']) for g in grupos],
            'hovertemplate': f'{nombre}<br>%{{x}}: AP@0,5 %{{y:.3f}}<extra></extra>',
        })
        data.append({
            'type': 'bar', 'name': nombre, 'legendgroup': nombre, 'showlegend': False,
            'marker': {'color': color}, 'xaxis': 'x2', 'yaxis': 'y2',
            'x': ['Falsos positivos', 'Robots perdidos', 'Perdidos difficult'],
            'y': [int(total['fp']), int(total['fn']), int(total['fn_difficult'])],
            'hovertemplate': f'{nombre}<br>%{{x}}: %{{y}}<extra></extra>',
        })
    layout = estilo({
        'barmode': 'group',
        'xaxis': {'domain': [0, 0.5], 'anchor': 'y'},
        'yaxis': {'title': {'text': 'AP@0,5 en validación'}, 'range': [0, 1]},
        'xaxis2': {'domain': [0.58, 1], 'anchor': 'y2'},
        'yaxis2': {'title': {'text': 'Número (confianza ≥ 0,5)'}, 'anchor': 'x2'},
        'annotations': [
            {'text': '<b>AP@0,5 por grupo de robots</b>', 'x': 0.25, 'y': 1.08, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
            {'text': '<b>Errores en validación</b>', 'x': 0.79, 'y': 1.08, 'xref': 'paper', 'yref': 'paper', 'showarrow': False},
        ],
    }, 560)
    return {'data': data, 'layout': layout}


def resultados_por_secuencia() -> dict:
    """AP@0,5 de cada experimento en las once secuencias de validación."""
    data = []
    for carpeta, nombre, color in EXPERIMENTOS:
        filas = [f for f in leer_csv(WEEK2 / 'resultados_test' / f'{carpeta}_val' / 'errores_por_video.csv')
                 if f['grupo'] != 'Total']
        data.append({
            'type': 'bar', 'orientation': 'h', 'name': nombre, 'marker': {'color': color},
            'y': [f['grupo'].replace('PIDS', '') for f in filas], 'x': [float(f['map_50']) for f in filas],
            'customdata': [[int(f['robots']), int(f['robots_difficult']), int(f['fp']), int(f['fn'])] for f in filas],
            'hovertemplate': (f'{nombre}<br>%{{y}}: AP@0,5 %{{x:.3f}}<br>'
                              'Robots %{customdata[0]} (difficult %{customdata[1]})<br>'
                              'FP %{customdata[2]} · perdidos %{customdata[3]}<extra></extra>'),
        })
    layout = estilo({
        'barmode': 'group', 'bargroupgap': 0.1,
        'xaxis': {'title': {'text': 'AP@0,5 en validación'}, 'range': [0.7, 1]},
        'yaxis': {'autorange': 'reversed', 'automargin': True}, 'margin': {'l': 20, 'r': 20, 't': 20, 'b': 110},
        'legend': {'orientation': 'h', 'x': 0, 'y': -0.09, 'yanchor': 'top'},
    }, 760)
    return {'data': data, 'layout': layout}


def construir(destino: Path) -> None:
    if destino.exists():
        shutil.rmtree(destino)
    datos = destino / 'datos'
    datos.mkdir(parents=True)
    shutil.copy(RAIZ / 'web' / 'index.html', destino / 'index.html')
    shutil.copy(EDA / 'interactivos' / 'plotly.min.js', destino / 'plotly.min.js')

    figuras = {nombre: extraer_figura(EDA / 'interactivos' / f'{nombre}.html')
               for nombre in ('mapas_calor_por_video', 'mapas_calor_temporales', 'robots_por_fotograma')}
    figuras['curvas_por_experimento'] = curvas_por_experimento()
    figuras['curvas_entrenamiento'] = curvas_entrenamiento()
    figuras['resultados_por_grupo'] = resultados_por_grupo()
    figuras['resultados_por_secuencia'] = resultados_por_secuencia()
    test = evaluacion_test()              # Sin evaluación en test todavía, la página lo indica
    if test:
        figuras['evaluacion_test'] = test
    for nombre, figura in figuras.items():
        (datos / f'{nombre}.json').write_text(json.dumps(figura, ensure_ascii=False, separators=(',', ':')),
                                              encoding='utf-8')

    # Copia de las páginas antiguas del EDA, para que sus enlaces sigan funcionando
    (destino / 'eda').mkdir()
    for parte in ('interactivos', 'para_informe'):
        shutil.copytree(EDA / parte, destino / 'eda' / parte)
    shutil.copy(EDA / 'README.md', destino / 'eda' / 'README.md')
    print(f'Web en {destino}: {len(figuras)} figuras')


if __name__ == '__main__':
    construir(Path(sys.argv[1] if len(sys.argv) > 1 else '_site').resolve())
