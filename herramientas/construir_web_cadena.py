"""Figuras interactivas de la cadena de entrenamientos (arquitecturas, tasa de aprendizaje, coste y test).

Uso: python herramientas/construir_web_cadena.py   (escribe web/Bloque2/datos_cadena.js)

Lee ENTREGA 1/WEEK2/cadena/resumen.csv (validación), resumen_test.csv, test_registro.json, los historiales
de resultados_train/ y el detalle de test de los modelos final y rápido. Cada figura se describe como
{'controles': [...], 'variantes': {'i|j': {'data': [...], 'layout': {...}}}}: web/Bloque2/graficas_cadena.js
la dibuja con Plotly y cambia de variante cuando se mueven los selectores.

Solo usa la biblioteca estándar. No hay valores inventados: todo sale de los CSV del repositorio.
"""

import csv
import json
import math
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEEK2 = RAIZ / 'ENTREGA 1' / 'WEEK2'
CADENA = WEEK2 / 'cadena'
PERFIL = 'robusto_v1'
SALIDA = RAIZ / 'web' / 'Bloque2' / 'datos_cadena.js'

# De la mayor a la menor precisión en validación con lr 0,001
MODELOS = ['faster_rcnn_v2', 'retinanet_v2', 'faster_rcnn_v1', 'retinanet_v1', 'faster_rcnn_v3', 'ssd_v1', 'ssd_v2']
NOMBRES = {'faster_rcnn_v2': 'Faster R-CNN v2', 'retinanet_v2': 'RetinaNet v2', 'faster_rcnn_v1': 'Faster R-CNN v1',
           'retinanet_v1': 'RetinaNet v1', 'faster_rcnn_v3': 'Faster R-CNN MobileNet', 'ssd_v1': 'SSD300 VGG16',
           'ssd_v2': 'SSDlite320'}
COLORES = {'faster_rcnn_v2': '#2463A6', 'retinanet_v2': '#C65D23', 'faster_rcnn_v1': '#6E9BCB', 'retinanet_v1': '#E0A070',
           'faster_rcnn_v3': '#2E8B57', 'ssd_v1': '#8E6BB5', 'ssd_v2': '#8496A8'}
COLOR_LR = {0.0005: '#6E9BCB', 0.001: '#2463A6', 0.002: '#C65D23'}
DASH_LR = {0.0005: 'dot', 0.001: 'solid', 0.002: 'dash'}
GRIS, AZUL, NARANJA, MORADO, VERDE = '#A6B4C2', '#2463A6', '#C65D23', '#8E6BB5', '#2E8B57'
MODELOS_LR = ['faster_rcnn_v2', 'retinanet_v2', 'faster_rcnn_v1']  # los que se repitieron con tres tasas


def leer_csv(ruta):
    with open(ruta, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(texto):
    """Número o None si está vacío, es nan o es el -1 con que se marca «sin robots de ese grupo»."""
    try:
        valor = float(texto)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(valor) or valor == -1.0 else valor


def coma(valor, decimales=4):
    """Texto con coma decimal, como el resto de la memoria."""
    return f'{valor:.{decimales}f}'.replace('.', ',')


def lr_txt(lr):
    return coma(lr, 4).rstrip('0').rstrip(',') if lr < 0.001 else coma(lr, 3)


def nombre_exp(modelo, lr):
    return f'{NOMBRES[modelo]} · lr {lr_txt(lr)}'


def id_exp(modelo, lr):
    return f'{modelo}_aug_{PERFIL}_lr{str(lr).replace("0.", "").replace(".", "")}'


def f1_de(precision, recall):
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


# --------------------------------------------------------------------------- datos

def cargar():
    """Filas de validación y de test enriquecidas con el F1 y los errores al umbral fijado en validación."""
    val = []
    for f in leer_csv(CADENA / 'resumen.csv'):
        fila = {k: (num(v) if k not in ('experimento', 'modelo') else v) for k, v in f.items()}
        fila['modelo'] = f['modelo']
        fila['lr'] = float(f['lr'])
        fila['epocas'] = int(f['epocas'])
        fila['mejor_epoca'] = int(f['mejor_epoca'])
        fila['robots'] = 1561  # robots de validación (los CSV de errores lo repiten en cada fila)
        # Con el umbral que maximiza el F1 de validación
        fila['p_umbral'], fila['r_umbral'], fila['f1_umbral'] = fila['precision_f1'], fila['exhaustividad_f1'], fila['f1_max']
        fila['fp_umbral'], fila['fn_umbral'] = fila['fp_f1'], fila['fn_f1']
        val.append(fila)
    registro = json.loads((CADENA / 'test_registro.json').read_text(encoding='utf-8'))
    test = []
    for f in leer_csv(CADENA / 'resumen_test.csv'):
        fila = {k: (num(v) if k not in ('experimento', 'modelo') else v) for k, v in f.items()}
        fila['modelo'] = f['modelo']
        fila['lr'] = float(f['lr'])
        fila['robots'] = 1721
        fila['umbral_fijado'] = registro[f['experimento']]['umbral']
        # En test, precision/exhaustividad/fp/fn ya son los del umbral fijado en validación
        fila['p_umbral'], fila['r_umbral'] = fila['precision'], fila['exhaustividad']
        fila['f1_umbral'] = f1_de(fila['precision'], fila['exhaustividad'])
        fila['fp_umbral'], fila['fn_umbral'] = fila['fp'], fila['fn']
        test.append(fila)
    return val, test


def historial(modelo, lr, sufijo=''):
    filas = leer_csv(WEEK2 / 'resultados_train' / (id_exp(modelo, lr) + sufijo) / 'historial.csv')
    return {k: [float(f[k]) for f in filas] for k in ('epoch', 'train_loss', 'valid_loss', 'valid_map', 'valid_map_50', 'lr')}


def cargar_largo():
    """Entrenamientos repetidos con más épocas (acción `largo` de la cadena), si los hay."""
    ruta = CADENA / 'resumen_largo.csv'
    if not ruta.exists():
        return []
    filas = []
    for f in leer_csv(ruta):
        filas.append({'modelo': f['modelo'], 'lr': float(f['lr']), 'epocas': int(f['epocas']), 'mejor_epoca': int(f['mejor_epoca']),
                      'sufijo': f'_ep{f["epocas"]}'})
    return filas



# --------------------------------------------------------------------------- utilidades de figura

def figura(controles, variantes):
    return {'controles': controles, 'variantes': variantes}


def eje(titulo, **extra):
    return {'title': {'text': titulo}, **extra}


def hover_curva(nombre, y_texto):
    return f'<b>{nombre}</b><br>Época %{{x}}<br>{y_texto}: %{{y:.4f}}<extra></extra>'


def curvas(experimentos, clave, titulo_y, rango=None, color_de=None, dash_de=None, nombre_de=None):
    """Una línea por experimento con su mejor época marcada. experimentos: lista de (modelo, lr, mejor_epoca)."""
    trazas = []
    for modelo, lr, mejor in experimentos:
        h = historial(modelo, lr)
        color = (color_de or (lambda m, l: COLORES[m]))(modelo, lr)
        nombre = (nombre_de or (lambda m, l: NOMBRES[m]))(modelo, lr)
        grupo = f'{modelo}{lr}'
        trazas.append({'type': 'scatter', 'mode': 'lines+markers', 'name': nombre, 'legendgroup': grupo, 'x': h['epoch'], 'y': h[clave],
                       'line': {'color': color, 'width': 2, 'dash': (dash_de or (lambda m, l: 'solid'))(modelo, lr)},
                       'marker': {'size': 5, 'color': color}, 'hovertemplate': hover_curva(nombre, titulo_y)})
        trazas.append({'type': 'scatter', 'mode': 'markers', 'name': nombre, 'legendgroup': grupo, 'showlegend': False,
                       'x': [mejor], 'y': [h[clave][mejor - 1]], 'marker': {'symbol': 'diamond', 'size': 13, 'color': color,
                                                                           'line': {'color': '#ffffff', 'width': 1.5}},
                       'hovertemplate': f'<b>{nombre}</b><br>Mejor checkpoint (época {mejor})<br>{titulo_y}: %{{y:.4f}}<extra></extra>'})
    layout = {'xaxis': eje('Época', dtick=1), 'yaxis': eje(titulo_y)}
    if rango:
        layout['yaxis']['range'] = rango
    return {'data': trazas, 'layout': layout}


# --------------------------------------------------------------------------- figuras

METRICAS_CURVA = [('AP@0,5 en validación (zoom)', 'valid_map_50', [0.86, 0.96]),
                  ('AP@0,5 en validación (escala completa)', 'valid_map_50', None),
                  ('AP 0,50:0,95 en validación', 'valid_map', None),
                  ('Pérdida de validación', 'valid_loss', None),
                  ('Pérdida de entrenamiento', 'train_loss', None)]


def fig_arquitecturas(val):
    exp = [(m, 0.001, next(f['mejor_epoca'] for f in val if f['modelo'] == m and f['lr'] == 0.001)) for m in MODELOS]
    variantes = {}
    for i, (etiqueta, clave, rango) in enumerate(METRICAS_CURVA):
        variantes[str(i)] = curvas(exp, clave, etiqueta.split(' (')[0], rango)
    return figura([{'etiqueta': 'Medida', 'opciones': [m[0] for m in METRICAS_CURVA]}], variantes)


def fig_tasa(val):
    variantes = {}
    for i, modelo in enumerate(MODELOS_LR):
        exp = [(modelo, lr, next(f['mejor_epoca'] for f in val if f['modelo'] == modelo and f['lr'] == lr)) for lr in (0.0005, 0.001, 0.002)]
        for j, (etiqueta, clave, rango) in enumerate(METRICAS_CURVA[1:]):
            c = curvas(exp, clave, etiqueta.split(' (')[0], None, color_de=lambda m, lr: COLOR_LR[lr],
                       dash_de=lambda m, lr: DASH_LR[lr], nombre_de=lambda m, lr: f'lr {lr_txt(lr)}')
            variantes[f'{i}|{j}'] = c
    return figura([{'etiqueta': 'Modelo', 'opciones': [NOMBRES[m] for m in MODELOS_LR]},
                   {'etiqueta': 'Medida', 'opciones': [m[0] for m in METRICAS_CURVA[1:]]}], variantes)


def fig_aprendizaje(val):
    ordenadas = [{'modelo': f['modelo'], 'lr': f['lr'], 'mejor_epoca': f['mejor_epoca'], 'sufijo': '', 'etiqueta': nombre_exp(f['modelo'], f['lr'])}
                 for f in sorted(val, key=lambda f: (MODELOS.index(f['modelo']), f['lr']))]
    ordenadas += [{**f, 'etiqueta': f"{nombre_exp(f['modelo'], f['lr'])} · {f['epocas']} épocas"} for f in cargar_largo()]
    variantes = {}
    for i, f in enumerate(ordenadas):
        h = historial(f['modelo'], f['lr'], f['sufijo'])
        mejor = f['mejor_epoca']
        cortes = [int(h['epoch'][k]) for k in range(1, len(h['lr'])) if h['lr'][k] != h['lr'][k - 1]]
        formas = [{'type': 'line', 'xref': 'x', 'yref': 'paper', 'x0': c - 0.5, 'x1': c - 0.5, 'y0': 0, 'y1': 1, 'line': {'color': '#DCE3E9', 'width': 1.2}}
                  for c in cortes]
        formas.append({'type': 'line', 'xref': 'x', 'yref': 'paper', 'x0': mejor, 'x1': mejor, 'y0': 0, 'y1': 1,
                       'line': {'color': '#788797', 'width': 1.5, 'dash': 'dot'}})
        variantes[str(i)] = {
            'data': [{'type': 'scatter', 'mode': 'lines+markers', 'name': 'Pérdida de entrenamiento', 'x': h['epoch'], 'y': h['train_loss'],
                      'line': {'color': GRIS, 'width': 2}, 'marker': {'size': 5}, 'hovertemplate': 'Época %{x}<br>Pérdida de entrenamiento: %{y:.4f}<extra></extra>'},
                     {'type': 'scatter', 'mode': 'lines+markers', 'name': 'Pérdida de validación', 'x': h['epoch'], 'y': h['valid_loss'],
                      'line': {'color': NARANJA, 'width': 2}, 'marker': {'size': 5}, 'hovertemplate': 'Época %{x}<br>Pérdida de validación: %{y:.4f}<extra></extra>'},
                     {'type': 'scatter', 'mode': 'lines+markers', 'name': 'AP@0,5 en validación (eje derecho)', 'x': h['epoch'], 'y': h['valid_map_50'], 'yaxis': 'y2',
                      'line': {'color': AZUL, 'width': 2.5}, 'marker': {'size': 6}, 'hovertemplate': 'Época %{x}<br>AP@0,5: %{y:.4f}<extra></extra>'}],
            'layout': {'xaxis': eje('Época', dtick=1 if len(h['epoch']) <= 15 else 5), 'yaxis': eje('Pérdida'),
                       'yaxis2': eje('AP@0,5 en validación', overlaying='y', side='right', showgrid=False),
                       'shapes': formas,
                       'annotations': [{'x': mejor, 'y': 0.98, 'xref': 'x', 'yref': 'paper', 'text': f'mejor checkpoint (época {mejor})',
                                        'showarrow': False, 'xanchor': 'left', 'yanchor': 'top', 'xshift': 6, 'bgcolor': 'rgba(255,255,255,.85)',
                                        'font': {'size': 11, 'color': '#526576'}}]}}
    final = next(i for i, f in enumerate(ordenadas) if f['modelo'] == 'faster_rcnn_v2' and f['lr'] == 0.001 and not f['sufijo'])
    return figura([{'etiqueta': 'Experimento', 'opciones': [f['etiqueta'] for f in ordenadas], 'predeterminado': final}], variantes)


MEDIDAS_COSTE = [('Minutos de entrenamiento', lambda f: f['minutos_train'], 'min', 1),
                 ('Época del mejor checkpoint', lambda f: f['mejor_epoca'], 'época', 0),
                 ('Minutos hasta el mejor checkpoint (estimado)', lambda f: f['minutos_train'] * f['mejor_epoca'] / f['epocas'], 'min', 1),
                 ('Memoria pico de GPU (MiB)', lambda f: f['mem_pico_mib'], 'MiB', 0),
                 ('Tiempo por imagen en inferencia (ms)', lambda f: f['ms_una_a_una'], 'ms', 1)]


def fig_coste(val):
    variantes = {}
    for i, (etiqueta, fn, unidad, dec) in enumerate(MEDIDAS_COSTE):
        orden = sorted(val, key=lambda f: -fn(f))
        categorias = [nombre_exp(f['modelo'], f['lr']) for f in orden]
        trazas = []
        for modelo in MODELOS:
            filas = [f for f in orden if f['modelo'] == modelo]
            if not filas:
                continue
            trazas.append({'type': 'bar', 'orientation': 'h', 'name': NOMBRES[modelo], 'marker': {'color': COLORES[modelo]},
                           'y': [nombre_exp(f['modelo'], f['lr']) for f in filas], 'x': [round(fn(f), 2) for f in filas],
                           'text': [coma(fn(f), dec) + ' ' + unidad for f in filas], 'textposition': 'outside', 'cliponaxis': False,
                           'customdata': [[f['ap50_todos'], f['epocas'], f['mejor_epoca'], f['minutos_train']] for f in filas],
                           'hovertemplate': '<b>%{y}</b><br>' + etiqueta + ': %{text}<br>AP@0,5 en validación: %{customdata[0]:.4f}'
                                            '<br>Mejor época: %{customdata[2]} de %{customdata[1]}<extra></extra>'})
        variantes[str(i)] = {'data': trazas, 'layout': {'xaxis': eje(etiqueta, range=[0, round(max(fn(f) for f in val) * 1.4, 2)]),
                                                       'yaxis': {'categoryorder': 'array', 'categoryarray': categorias, 'autorange': 'reversed'},
                                                       'height': 640, 'margin': {'l': 230}}}
    return figura([{'etiqueta': 'Medida', 'opciones': [m[0] for m in MEDIDAS_COSTE]}], variantes)


METRICAS_CALIDAD = [('AP@0,5 · validación', 'val', 'ap50_todos'), ('AP@0,5 · test', 'test', 'ap50_todos'),
                    ('AP@0,5 de los difficult · validación', 'val', 'ap50_difficult'), ('AP@0,5 de los difficult · test', 'test', 'ap50_difficult'),
                    ('AP 0,50:0,95 · validación', 'val', 'ap_0.5:0.95'), ('AP 0,50:0,95 · test', 'test', 'ap_0.5:0.95'),
                    ('F1 · validación', 'val', 'f1_umbral'), ('F1 · test', 'test', 'f1_umbral')]


def _rango_ajustado(valores, margen=0.15):
    """Rango que deja fuera los valores muy por debajo de la mediana (p. ej. SSDlite320) y devuelve cuáles son."""
    mediana = statistics.median(valores)
    dentro = [v for v in valores if v >= mediana - margen]
    pad = (max(dentro) - min(dentro)) * 0.12 or 0.01
    return [min(dentro) - pad, max(dentro) + pad], [v for v in valores if v < mediana - margen]


def fig_latencia(val, test):
    variantes = {}
    for i, (etiqueta, conjunto, clave) in enumerate(METRICAS_CALIDAD):
        filas = val if conjunto == 'val' else test
        # La latencia se mide aparte en cada conjunto, así que cada uno usa su propia columna
        valores = [f[clave] for f in filas]
        rango, fuera = _rango_ajustado(valores)
        for j in (0, 1):
            trazas = []
            for modelo in MODELOS:
                fs = [f for f in filas if f['modelo'] == modelo]
                if not fs:
                    continue
                trazas.append({'type': 'scatter', 'mode': 'markers', 'name': NOMBRES[modelo], 'x': [f['ms_una_a_una'] for f in fs],
                               'y': [f[clave] for f in fs],
                               'marker': {'color': COLORES[modelo], 'size': [16 if f['lr'] == 0.001 else 9 for f in fs],
                                          'opacity': [1 if f['lr'] == 0.001 else 0.6 for f in fs], 'line': {'color': '#ffffff', 'width': 1.5}},
                               'customdata': [[lr_txt(f['lr']), f['minutos_train'], f['mejor_epoca']] for f in fs],
                               'hovertemplate': '<b>' + NOMBRES[modelo] + ' · lr %{customdata[0]}</b><br>' + etiqueta
                                                + ': %{y:.4f}<br>Inferencia: %{x:.1f} ms por imagen<br>Entrenamiento: %{customdata[1]:.0f} min<extra></extra>'})
            layout = {'xaxis': eje('Tiempo por imagen (ms, escala logarítmica)', type='log',
                                   tickvals=[4, 10, 20, 50, 100], ticktext=['4', '10', '20', '50', '100']),
                      'yaxis': eje(etiqueta)}
            if j == 0 and fuera:
                layout['yaxis']['range'] = rango
                layout['annotations'] = [{'xref': 'paper', 'yref': 'paper', 'x': 0, 'y': 1, 'xanchor': 'left', 'yanchor': 'top', 'showarrow': False,
                                          'text': ' y '.join(f'{NOMBRES[f["modelo"]]} ({coma(f[clave])})' for f in filas if f[clave] in fuera)
                                                  + (' quedan fuera de escala' if len(fuera) > 1 else ' queda fuera de escala'),
                                          'font': {'size': 11, 'color': '#526576'}}]
            variantes[f'{i}|{j}'] = {'data': trazas, 'layout': layout}
    return figura([{'etiqueta': 'Medida', 'opciones': [m[0] for m in METRICAS_CALIDAD]},
                   {'etiqueta': 'Escala', 'opciones': ['Ajustada', 'Completa']}], variantes)


MEDIDAS_VT = [('AP@0,5 de todos los robots', 'ap50_todos', [0.6, 1.0]), ('AP@0,5 de los robots normales', 'ap50_normales', [0.6, 1.0]),
              ('AP@0,5 de los difficult', 'ap50_difficult', [0.2, 0.75]), ('AP 0,50:0,95', 'ap_0.5:0.95', [0.3, 0.7]),
              ('Precisión (con el umbral fijado en validación)', 'p_umbral', [0.6, 1.0]),
              ('Exhaustividad (con el umbral fijado en validación)', 'r_umbral', [0.3, 1.0]),
              ('F1 (con el umbral fijado en validación)', 'f1_umbral', [0.6, 1.0]),
              ('Falsos positivos por cada 100 robots', 'fp_100', None), ('Robots perdidos por cada 100 robots', 'fn_100', None)]


def _tasas(filas):
    for f in filas:
        f['fp_100'] = f['fp_umbral'] / f['robots'] * 100
        f['fn_100'] = f['fn_umbral'] / f['robots'] * 100
    return filas


def fig_validacion_test(val, test):
    v = {f['modelo']: f for f in _tasas(val) if f['lr'] == 0.001}
    t = {f['modelo']: f for f in _tasas(test) if f['lr'] == 0.001}
    variantes = {}
    for i, (etiqueta, clave, rango) in enumerate(MEDIDAS_VT):
        dec = 2 if clave.endswith('_100') else 4
        trazas = []
        for nombre, datos, color in (('Validación', v, GRIS), ('Test', t, AZUL)):
            trazas.append({'type': 'bar', 'name': nombre, 'marker': {'color': color}, 'x': [NOMBRES[m] for m in MODELOS],
                           'y': [round(datos[m][clave], 5) for m in MODELOS],
                           'text': [coma(datos[m][clave], dec) for m in MODELOS], 'textposition': 'none',
                           'hovertemplate': '<b>%{x}</b><br>' + nombre + ': %{text}<extra></extra>'})
        layout = {'xaxis': {'tickangle': 0}, 'yaxis': eje(etiqueta.split(' (')[0]), 'barmode': 'group'}
        if rango:
            layout['yaxis']['range'] = rango
        variantes[str(i)] = {'data': trazas, 'layout': layout}
    return figura([{'etiqueta': 'Medida', 'opciones': [m[0] for m in MEDIDAS_VT]}], variantes)


def fig_errores(test):
    t = {f['modelo']: f for f in test if f['lr'] == 0.001}
    series = [('Falsos positivos', lambda f: f['fp'], NARANJA), ('Robots normales perdidos', lambda f: f['fn'] - f['fn_difficult'], AZUL),
              ('Robots difficult perdidos', lambda f: f['fn_difficult'], MORADO)]
    trazas = [{'type': 'bar', 'name': n, 'marker': {'color': c}, 'x': [NOMBRES[m] for m in MODELOS], 'y': [int(fn(t[m])) for m in MODELOS],
               'text': [str(int(fn(t[m]))) for m in MODELOS], 'textposition': 'outside', 'cliponaxis': False,
               'hovertemplate': '<b>%{x}</b><br>' + n + ': %{y}<extra></extra>'} for n, fn, c in series]
    return figura([], {'0': {'data': trazas, 'layout': {'xaxis': {'tickangle': 0}, 'yaxis': eje('Errores en test (1721 robots)', rangemode='tozero'),
                                                       'barmode': 'group'}}})


def _detalle(modelo):
    return WEEK2 / 'resultados_test' / f'{id_exp(modelo, 0.001)}_test'


def fig_umbral(test):
    registro = json.loads((CADENA / 'test_registro.json').read_text(encoding='utf-8'))
    modelos = ['faster_rcnn_v2', 'faster_rcnn_v3']
    variantes = {}
    for i, modelo in enumerate(modelos):
        filas = leer_csv(_detalle(modelo) / 'umbral_confianza.csv')
        x = [float(f['umbral']) for f in filas]
        fijado = registro[id_exp(modelo, 0.001)]['umbral']
        f1s = [float(f['f1']) for f in filas]
        mejor = max(range(len(f1s)), key=f1s.__getitem__)
        series = [('Precisión', 'precision', AZUL, 'solid'), ('Exhaustividad', 'recall', NARANJA, 'solid'),
                  ('Exhaustividad de los difficult', 'recall_difficult', MORADO, 'dash'), ('F1', 'f1', '#172B40', 'solid')]
        trazas = [{'type': 'scatter', 'mode': 'lines+markers', 'name': n, 'x': x, 'y': [float(f[c]) for f in filas],
                   'line': {'color': col, 'width': 2.5 if c == 'f1' else 2, 'dash': d}, 'marker': {'size': 4},
                   'hovertemplate': n + ': %{y:.4f}<br>Umbral %{x}<extra></extra>'} for n, c, col, d in series]
        trazas.append({'type': 'scatter', 'mode': 'markers', 'name': 'Mejor F1 en test', 'x': [x[mejor]], 'y': [f1s[mejor]],
                       'marker': {'symbol': 'diamond', 'size': 13, 'color': '#172B40', 'line': {'color': '#ffffff', 'width': 1.5}},
                       'hovertemplate': f'Mejor F1 posible en test: %{{y:.4f}}<br>Umbral %{{x}}<extra></extra>'})
        variantes[str(i)] = {'data': trazas, 'layout': {
            'xaxis': eje('Umbral de confianza', range=[0, 1]), 'yaxis': eje('Valor', range=[0.4, 1.0]),
            'shapes': [{'type': 'line', 'xref': 'x', 'yref': 'paper', 'x0': fijado, 'x1': fijado, 'y0': 0, 'y1': 1,
                        'line': {'color': '#788797', 'width': 1.5, 'dash': 'dot'}}],
            'annotations': [{'x': fijado, 'y': 0.03, 'xref': 'x', 'yref': 'paper', 'xanchor': 'right', 'yanchor': 'bottom', 'showarrow': False,
                             'xshift': -6, 'bgcolor': 'rgba(255,255,255,.85)',
                             'text': f'umbral fijado en validación: {coma(fijado, 2)}', 'font': {'size': 11, 'color': '#526576'}}]}}
    return figura([{'etiqueta': 'Modelo', 'opciones': [NOMBRES[m] for m in modelos]}], variantes)


MEDIDAS_SEC = [('AP@0,5', 'map_50', 4), ('F1', 'f1', 4), ('Falsos positivos', 'fp', 0), ('Robots perdidos', 'fn', 0)]


def fig_secuencias(test):
    modelos = [('faster_rcnn_v2', 'Faster R-CNN v2 (final)', AZUL), ('faster_rcnn_v3', 'Faster R-CNN MobileNet (rápido)', VERDE)]
    datos = {m: [f for f in leer_csv(_detalle(m) / 'errores_por_video.csv') if f['grupo'] != 'Total'] for m, _, _ in modelos}
    variantes = {}
    for i, (etiqueta, clave, dec) in enumerate(MEDIDAS_SEC):
        trazas = []
        for modelo, nombre, color in modelos:
            filas = datos[modelo]
            trazas.append({'type': 'bar', 'name': nombre, 'marker': {'color': color}, 'x': [f['grupo'].replace('PIDS', '') for f in filas],
                           'y': [num(f[clave]) if dec else int(float(f[clave])) for f in filas],
                           'customdata': [[f['imagenes'], f['robots'], f['robots_difficult'], f['fp'], f['fn']] for f in filas],
                           'hovertemplate': '<b>%{x}</b> · ' + nombre + '<br>' + etiqueta + ': %{y' + (':.4f' if dec else '') + '}'
                                            '<br>%{customdata[0]} imágenes, %{customdata[1]} robots (%{customdata[2]} difficult)'
                                            '<br>FP %{customdata[3]} · perdidos %{customdata[4]}<extra></extra>'})
        layout = {'xaxis': {'tickangle': -35}, 'yaxis': eje(etiqueta, rangemode='tozero'), 'barmode': 'group', 'margin': {'b': 130}}
        if clave in ('map_50', 'f1'):
            layout['yaxis']['range'] = [0, 1.02]
        variantes[str(i)] = {'data': trazas, 'layout': layout}
    return figura([{'etiqueta': 'Medida', 'opciones': [m[0] for m in MEDIDAS_SEC]}], variantes)


COLUMNAS_MAPA = [('AP@0,5', 'ap50_todos'), ('AP@0,5 normales', 'ap50_normales'), ('AP@0,5 difficult', 'ap50_difficult'),
                 ('AP 0,50:0,95', 'ap_0.5:0.95'), ('Precisión', 'p_umbral'), ('Exhaustividad', 'r_umbral'), ('F1', 'f1_umbral')]


def fig_mapa(val, test):
    variantes = {}
    for i, filas in enumerate((val, test)):
        orden = sorted(filas, key=lambda f: -f['ap50_todos'])
        z, texto = [], []
        columnas = {k: [f[k] for f in orden] for _, k in COLUMNAS_MAPA}
        for f in orden:
            fila_z, fila_t = [], []
            for _, k in COLUMNAS_MAPA:
                v = columnas[k]
                rango = (max(v) - min(v)) or 1
                fila_z.append(round((f[k] - min(v)) / rango, 4))
                fila_t.append(coma(f[k]))
            z.append(fila_z)
            texto.append(fila_t)
        variantes[str(i)] = {'data': [{'type': 'heatmap', 'x': [c for c, _ in COLUMNAS_MAPA], 'y': [nombre_exp(f['modelo'], f['lr']) for f in orden],
                                       'z': z, 'text': texto, 'texttemplate': '%{text}', 'textfont': {'size': 11},
                                       'colorscale': [[0, '#f3f6f9'], [1, '#2463A6']], 'showscale': False, 'xgap': 2, 'ygap': 2,
                                       'hovertemplate': '<b>%{y}</b><br>%{x}: %{text}<extra></extra>'}],
                             'layout': {'xaxis': {'side': 'top', 'tickangle': 0}, 'yaxis': {'autorange': 'reversed'}, 'height': 60 + 38 * len(orden) + 100,
                                        'margin': {'l': 230, 't': 80}}}
    return figura([{'etiqueta': 'Conjunto', 'opciones': ['Validación (13 entrenamientos)', 'Test (7 modelos, lr 0,001)']}], variantes)


def construir():
    val, test = cargar()
    return {'arquitecturas': fig_arquitecturas(val), 'tasa': fig_tasa(val), 'aprendizaje': fig_aprendizaje(val), 'coste': fig_coste(val),
            'latencia': fig_latencia(val, test), 'validacion_test': fig_validacion_test(val, test), 'errores': fig_errores(test),
            'umbral': fig_umbral(test), 'secuencias': fig_secuencias(test), 'mapa': fig_mapa(val, test)}


def escribir():
    figuras = construir()
    contenido = json.dumps(figuras, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    SALIDA.write_text('window.PIDS_CADENA = ' + contenido + ';\n', encoding='utf-8', newline='\n')
    print(f'{len(figuras)} figuras en {SALIDA} ({SALIDA.stat().st_size // 1024} KiB)')


if __name__ == '__main__':
    escribir()
