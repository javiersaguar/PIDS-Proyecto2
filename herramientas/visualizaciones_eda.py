"""Figuras espaciales y temporales a partir de las tablas del EDA (T12)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots


AZUL, NARANJA, TINTA = '#2463A6', '#C65D23', '#172B40'
ESCALA = [[0, '#F4F7FA'], [.12, '#D9E6F2'], [.4, '#86B1D5'], [.7, '#397CB6'], [1, '#123D67']]
REJILLA = (16, 9)
VENTANA_S = 5


def preparar_datos(imgs, cajas, fps):
    """Calcula frecuencias por 100 imágenes; difficult es un subconjunto de todos."""
    if imgs.duplicated(['secuencia', 'frame']).any():
        raise ValueError('Hay imágenes repetidas en secuencia/frame.')
    centros = cajas[['cx', 'cy']].to_numpy()
    if not np.isfinite(centros).all() or not ((centros >= 0) & (centros <= 1)).all():
        raise ValueError('Los centros deben ser finitos y estar normalizados a [0, 1].')
    imagenes = imgs.copy().sort_values(['secuencia', 'frame'])
    imagenes['segundo'] = imagenes.frame / fps
    imagenes['ventana'] = (imagenes.segundo // VENTANA_S).astype(int)
    objetos = cajas.copy()
    objetos['ventana'] = ((objetos.frame / fps) // VENTANA_S).astype(int)
    secuencias = sorted(imagenes.secuencia.unique())
    grupos = ['todos', 'difficult']
    x = np.linspace(0, 1, REJILLA[0] + 1)
    y = np.linspace(0, 1, REJILLA[1] + 1)

    def registro(sec, ventana=None):
        i = imagenes[imagenes.secuencia == sec]
        c = objetos[objetos.secuencia == sec]
        if ventana is not None:
            i, c = i[i.ventana == ventana], c[c.ventana == ventana]
        mapas, cuentas = [], []
        for grupo in grupos:
            g = c if grupo == 'todos' else c[c.difficult == 1]
            h = np.histogram2d(g.cx, g.cy, bins=[x, y])[0].T
            mapas.append(h * 100 / len(i) if len(i) else np.zeros_like(h))
            cuentas.append(len(g))
        return dict(secuencia=sec, ventana=ventana, imagenes=len(i), cuentas=cuentas, mapas=mapas)

    globales = [registro(s) for s in secuencias]
    ventanas = [registro(s, int(v)) for s in secuencias
                for v in sorted(imagenes.loc[imagenes.secuencia == s, 'ventana'].unique())]
    return dict(imagenes=imagenes, cajas=objetos, secuencias=secuencias,
                globales=globales, ventanas=ventanas, x=x, y=y, fps=fps)


def estilo_interactivo(fig, titulo, subtitulo, alto=650):
    fig.update_layout(
        template='plotly_white', height=alto, autosize=True,
        font=dict(family='Arial, sans-serif', size=13, color=TINTA),
        title=dict(text=f'{titulo}<br><sup>{subtitulo}</sup>', x=.055, y=.98),
        margin=dict(l=65, r=70, t=105, b=135), paper_bgcolor='white',
        hoverlabel=dict(bgcolor='white', font_size=13),
    )


def controles(fig, pasos, duracion=450, prefijo=''):
    fig.update_layout(
        updatemenus=[dict(type='buttons', direction='left', x=0, y=-.12,
                         showactive=False, buttons=[
            dict(label='▶ Reproducir', method='animate', args=[None, dict(
                frame=dict(duration=duracion, redraw=True), transition=dict(duration=0), fromcurrent=True)]),
            dict(label='Ⅱ Pausa', method='animate', args=[[None], dict(
                mode='immediate', frame=dict(duration=0, redraw=True), transition=dict(duration=0))]),
        ])],
        sliders=[dict(active=0, x=0, y=-.03, len=1, pad=dict(t=28, b=10),
                      currentvalue=dict(prefix=prefijo, font=dict(size=12)), steps=pasos)],
    )


def paso(nombre, etiqueta):
    return dict(label=etiqueta, method='animate', args=[[nombre], dict(
        mode='immediate', frame=dict(duration=0, redraw=True), transition=dict(duration=0))])


def mapas_interactivos(datos, temporal=False):
    registros = datos['ventanas'] if temporal else datos['globales']
    maximo = max(float(m.max()) for r in registros for m in r['mapas']) or 1
    centros_x = (datos['x'][:-1] + datos['x'][1:]) / 2
    centros_y = (datos['y'][:-1] + datos['y'][1:]) / 2
    fig = make_subplots(rows=1, cols=2, subplot_titles=['Todos los robots', 'Solo difficult'], horizontal_spacing=.09)

    def trazas(r):
        return [go.Heatmap(x=centros_x.tolist(), y=centros_y.tolist(),
                          z=np.round(m, 3).tolist(), coloraxis='coloraxis',
                          hovertemplate='x/ancho: %{x:.2f}<br>y/alto: %{y:.2f}<br>Centros/100 imágenes: %{z:.2f}<extra></extra>')
                for m in r['mapas']]

    def etiqueta(r):
        tramo = f" · {r['ventana'] * VENTANA_S}–{(r['ventana'] + 1) * VENTANA_S} s" if temporal else ''
        return f"{r['secuencia']}{tramo} · {r['imagenes']} imágenes · {r['cuentas'][0]} robots · {r['cuentas'][1]} difficult"

    for col, t in enumerate(trazas(registros[0]), 1):
        fig.add_trace(t, row=1, col=col)
    frames, pasos = [], []
    encabezado = 'Centros de robots por ventanas de 5 segundos' if temporal else 'Distribución espacial por vídeo'
    for indice, r in enumerate(registros):
        nombre = str(indice)
        frames.append(go.Frame(name=nombre, data=trazas(r), traces=[0, 1],
                               layout=go.Layout(title=dict(text=f'{encabezado}<br><sup>{etiqueta(r)}</sup>'))))
        rotulo = f"{r['secuencia']} · {r['ventana'] * VENTANA_S} s" if temporal else r['secuencia']
        pasos.append(paso(nombre, rotulo))
    fig.frames = frames
    estilo_interactivo(fig, encabezado, etiqueta(registros[0]), alto=650)
    for col in (1, 2):
        fig.update_xaxes(range=[0, 1], title_text='x / ancho', showgrid=False, row=1, col=col)
        fig.update_yaxes(range=[1, 0], title_text='y / alto', showgrid=False,
                         scaleanchor='x' if col == 1 else 'x2', scaleratio=9/16,
                         constrain='domain', row=1, col=col)
    fig.update_layout(coloraxis=dict(colorscale=ESCALA, cmin=0, cmax=maximo,
                                    colorbar=dict(title='Centros por<br>100 imágenes', thickness=14)))
    controles(fig, pasos, duracion=550 if temporal else 900, prefijo='Intervalo: ' if temporal else 'Vídeo: ')
    if temporal:
        # Saltar al inicio de un vídeo conserva el mismo control temporal y la escala global.
        saltos = [dict(label=s, method='animate', args=[[str(next(i for i, r in enumerate(registros)
                    if r['secuencia'] == s))], dict(mode='immediate', frame=dict(duration=0, redraw=True),
                                                  transition=dict(duration=0))]) for s in datos['secuencias']]
        menus = list(fig.layout.updatemenus)
        menus.append(dict(type='dropdown', x=1, xanchor='right', y=1.16,
                          buttons=[dict(label='Saltar a vídeo…', method='skip')] + saltos,
                          showactive=False))
        fig.update_layout(updatemenus=menus)
    return fig


def recuentos_interactivos(datos):
    """Diez curvas sincronizadas por número de fotograma anotado, sin inventar muestras."""
    secuencias = datos['secuencias']
    imagenes = datos['imagenes']
    tablas = [imagenes[imagenes.secuencia == s] for s in secuencias]
    titulos = [f"{s} · media {g.robots.mean():.2f} robots/imagen" for s, g in zip(secuencias, tablas)]
    fig = make_subplots(rows=5, cols=2, subplot_titles=titulos, vertical_spacing=.075, horizontal_spacing=.09)
    frames_muestra = sorted(imagenes.frame.unique())
    limite_x = float(imagenes.segundo.max()) + 1
    limite_y = max(1, int(imagenes.robots.max())) + .35

    def curva(g, frame):
        d = g[g.frame <= frame]
        return go.Scatter(x=d.segundo.round(3).tolist(), y=d.robots.tolist(), mode='lines+markers',
                          line=dict(color=AZUL, width=2), marker=dict(size=4),
                          customdata=d[['frame', 'difficult']].values.tolist(),
                          hovertemplate='Fotograma %{customdata[0]} · %{x:.2f} s<br>Robots: %{y}<br>Difficult: %{customdata[1]}<extra></extra>',
                          showlegend=False)

    for indice, g in enumerate(tablas):
        row, col = indice // 2 + 1, indice % 2 + 1
        fig.add_trace(curva(g, frames_muestra[0]), row=row, col=col)
        fig.add_hline(y=float(g.robots.mean()), line_dash='dot', line_color='#A6B4C2', row=row, col=col)
        fig.update_xaxes(range=[0, limite_x], title_text='Tiempo (s)' if row == 5 else None, row=row, col=col)
        fig.update_yaxes(range=[0, limite_y], dtick=1, title_text='Robots', row=row, col=col)
    encabezado = 'Robots por fotograma · los diez vídeos'
    def titulo(frame):
        return f'{encabezado}<br><sup>Fotograma {frame} · {frame / datos["fps"]:.2f} s · línea punteada: media de cada vídeo</sup>'
    fig.frames = [go.Frame(name=str(f), data=[curva(g, f) for g in tablas], traces=list(range(len(tablas))),
                           layout=go.Layout(title=dict(text=titulo(f)))) for f in frames_muestra]
    estilo_interactivo(fig, encabezado, 'Fotogramas anotados cada 24 frames; los negativos cuentan como cero.', alto=1050)
    fig.update_layout(title=dict(text=titulo(frames_muestra[0])))
    controles(fig, [paso(str(f), str(f)) for f in frames_muestra], duracion=130, prefijo='Fotograma: ')
    return fig


def estilo_eje(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(colors='#53677A', labelsize=9)
    ax.grid(False)


def figuras_documento(datos):
    """Versiones estáticas completas para Word/PDF; no son capturas de pantalla."""
    figuras = {}
    maximo = max(float(m.max()) for r in datos['globales'] for m in r['mapas']) or 1
    for grupo, nombre in enumerate(('todos', 'difficult')):
        fig, ejes = plt.subplots(2, 5, figsize=(16, 6.3), layout='constrained')
        for ax, r in zip(ejes.flat, datos['globales']):
            im = ax.pcolormesh(datos['x'], datos['y'], r['mapas'][grupo],
                               cmap='Blues', vmin=0, vmax=maximo, shading='flat')
            ax.set(xlim=(0, 1), ylim=(1, 0), aspect=9/16)
            ax.set_title(f"{r['secuencia']}  ·  {r['cuentas'][grupo]} cajas / {r['imagenes']} imágenes", fontsize=10, pad=9)
            ax.set(xlabel='x / ancho', ylabel='y / alto', xticks=[0, .5, 1], yticks=[0, .5, 1])
            estilo_eje(ax)
        titulo = 'Todos los robots' if nombre == 'todos' else 'Solo robots difficult'
        fig.suptitle(f'Distribución de centros por vídeo · {titulo}', fontsize=17, color=TINTA, fontweight='bold')
        barra = fig.colorbar(im, ax=ejes, shrink=.75, label='Centros por 100 imágenes · escala común en ambos grupos')
        barra.solids.set_rasterized(False)
        figuras[f'mapa_calor_por_video_{nombre}'] = fig

    fig, ejes = plt.subplots(5, 2, figsize=(12, 12), sharex=True, sharey=True, layout='constrained')
    for ax, sec in zip(ejes.flat, datos['secuencias']):
        g = datos['imagenes'][datos['imagenes'].secuencia == sec]
        ax.plot(g.segundo, g.robots, color=AZUL, linewidth=1.4, marker='o', markersize=2)
        ax.axhline(g.robots.mean(), color='#8496A8', linestyle=':', linewidth=1.2)
        ax.set_title(f'{sec} · media {g.robots.mean():.2f} · {len(g)} imágenes', loc='left', fontsize=11)
        ax.set(xlim=(0, datos['imagenes'].segundo.max() + 1), ylim=(-.1, datos['imagenes'].robots.max()+.35),
               yticks=range(int(datos['imagenes'].robots.max())+1), ylabel='Robots')
        estilo_eje(ax)
        ax.yaxis.grid(True, color='#E5EBF0', linewidth=.6)
    for ax in ejes[-1]:
        ax.set_xlabel('Tiempo desde el inicio del vídeo (s)')
    fig.suptitle('Robots por fotograma · diez vídeos\nLínea punteada: media, incluidos los fotogramas sin robots',
                 fontsize=16, fontweight='bold', color=TINTA)
    figuras['robots_por_fotograma_videos'] = fig

    # Una hoja de intervalos por vídeo conserva todo el contenido temporal en el PDF.
    for sec in datos['secuencias']:
        registros = [r for r in datos['ventanas'] if r['secuencia'] == sec]
        nfilas = int(np.ceil(len(registros) / 3))
        fig, ejes = plt.subplots(nfilas, 6, figsize=(16, nfilas*2.1), layout='constrained', squeeze=False)
        max_temporal = max(float(m.max()) for r in datos['ventanas'] for m in r['mapas']) or 1
        for k, r in enumerate(registros):
            for grupo in (0, 1):
                ax = ejes[k // 3, (k % 3)*2+grupo]
                im = ax.pcolormesh(datos['x'], datos['y'], r['mapas'][grupo],
                                   cmap='Blues', vmin=0, vmax=max_temporal, shading='flat')
                ax.set(xlim=(0, 1), ylim=(1, 0), aspect=9/16)
                etiqueta = 'Todos' if grupo == 0 else 'Difficult'
                ax.set_title(f"{r['ventana']*5}–{(r['ventana']+1)*5} s · {etiqueta}\n{r['cuentas'][grupo]} cajas / {r['imagenes']} imágenes", fontsize=8)
                ax.set(xticks=[0, .5, 1], yticks=[0, .5, 1])
                estilo_eje(ax)
        for k in range(len(registros)*2, nfilas*6):
            ejes.flat[k].axis('off')
        fig.suptitle(f'{sec} · evolución espacial en ventanas de 5 segundos', fontsize=16, color=TINTA, fontweight='bold')
        barra = fig.colorbar(im, ax=ejes, shrink=.8, label='Centros por 100 imágenes · escala temporal común')
        barra.solids.set_rasterized(False)
        figuras[f'mapas_temporales_{sec}'] = fig
    return figuras


def exportar_documento(figuras, destino, formatos=('png', 'svg', 'pdf'), dpi=300):
    """PNG a 300 ppp para Word; SVG/PDF vectoriales para edición y publicación."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.titleweight': 'medium',
                         'axes.edgecolor': '#CDD6DF', 'axes.labelcolor': TINTA,
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white'}):
        for nombre, fig in figuras.items():
            for extension in formatos:
                fig.savefig(destino / f'{nombre}.{extension}', dpi=dpi, bbox_inches='tight')


def exportar_interactivos(datos, destino):
    """HTML autónomos con una copia local compartida de Plotly; no requieren conexión."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / 'plotly.min.js').write_text(get_plotlyjs(), encoding='utf-8')
    figuras = {
        'mapas_calor_por_video': mapas_interactivos(datos),
        'mapas_calor_temporales': mapas_interactivos(datos, temporal=True),
        'robots_por_fotograma': recuentos_interactivos(datos),
    }
    for nombre, fig in figuras.items():
        fig.write_html(destino / f'{nombre}.html', include_plotlyjs='plotly.min.js',
                       auto_play=False, config=dict(displaylogo=False, responsive=True,
                       toImageButtonOptions=dict(format='svg', filename=nombre)))
    filas = []
    for r in datos['ventanas']:
        filas.append(dict(video=r['secuencia'], inicio_s=r['ventana']*VENTANA_S,
                          fin_s=(r['ventana']+1)*VENTANA_S, imagenes=r['imagenes'],
                          robots=r['cuentas'][0], difficult=r['cuentas'][1]))
    pd.DataFrame(filas).to_csv(destino / 'recuentos_ventanas.csv', index=False)
    datos['imagenes'][['secuencia', 'frame', 'segundo', 'robots', 'difficult']].to_csv(
        destino / 'recuentos_fotogramas.csv', index=False)
    crear_indice(destino)
    return figuras


def crear_indice(destino):
    """Página de entrada local para las tres figuras y sus exportaciones."""
    destino = Path(destino)
    tarjetas = [
        ('01', 'Distribución por vídeo', 'Todos los robots y difficult, con una escala común.',
         'mapas_calor_por_video', 'mapa_calor_por_video_todos'),
        ('02', 'Evolución espacial', 'Ventanas de 5 segundos, con recuentos visibles y salto por vídeo.',
         'mapas_calor_temporales', 'mapas_temporales_V01'),
        ('03', 'Robots por fotograma', 'Diez vídeos sincronizados. Cada curva termina con su última muestra.',
         'robots_por_fotograma', 'robots_por_fotograma_videos'),
    ]
    cuerpo = ''.join(f'''<article><span class="numero">{n}</span><h2>{titulo}</h2><p>{texto}</p>
        <a href="{html}.html"><img src="../para_informe/{imagen}.png" alt="{titulo}"></a>
        <a class="boton" href="{html}.html">Abrir figura interactiva →</a>
        <p class="formatos">Exportar: <a href="../para_informe/{imagen}.png">PNG 300 ppp</a> ·
        <a href="../para_informe/{imagen}.svg">SVG</a> · <a href="../para_informe/{imagen}.pdf">PDF</a></p></article>'''
        for n, titulo, texto, html, imagen in tarjetas)
    (destino / 'indice.html').write_text('''<!doctype html><html lang="es"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1"><title>EDA · Espacio y tiempo</title>
    <style>*{box-sizing:border-box}body{margin:0;background:#f4f7fa;color:#172b40;font:16px/1.6 Arial,sans-serif}
    main{max-width:1280px;margin:auto;padding:56px 30px}header{max-width:850px;margin-bottom:38px}
    .etiqueta,.numero{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#2463a6;font-weight:700}
    h1{font-size:42px;line-height:1.15;margin:14px 0 20px;letter-spacing:-1px}header p{color:#53677a}
    .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}article{padding:25px;background:white;border:1px solid #dce4ec;border-radius:12px}
    h2{font-size:22px;line-height:1.25;margin:12px 0}article p{color:#53677a;font-size:14px}img{width:100%;height:225px;object-fit:contain;border:1px solid #edf1f5;margin:12px 0 20px}
    a{color:#2463a6}.boton{font-size:14px;font-weight:700}.formatos{font-size:12px}aside{margin-top:32px;border-left:3px solid #2463a6;padding:10px 20px;background:#e9f0f7;font-size:14px}
    @media(max-width:900px){.grid{grid-template-columns:1fr}h1{font-size:32px}img{height:260px}}</style>
    <main><header><div class="etiqueta">PIDS · Entrega 1 · Análisis exploratorio</div><h1>Dónde aparecen los robots<br>y cómo cambia cada vídeo</h1>
    <p>Comparación espacial y temporal de las anotaciones originales. Reproduce, pausa o desplaza el control para explorar las muestras.</p></header>
    <section class="grid">''' + cuerpo + '''</section><aside><strong>Cómo leer las figuras.</strong>
    Los mapas muestran centros por 100 imágenes, con la misma escala en todos y difficult. Los recuentos incluyen las imágenes sin robots.
    Se observan los fotogramas anotados cada 24 frames; no se infieren muestras intermedias.
    <br>Para Word/PDF: usa los archivos de <code>para_informe/</code>. Para abrir sin conexión: conserva esta carpeta con <code>plotly.min.js</code>.
    <br><a href="recuentos_fotogramas.csv">Datos por fotograma</a> · <a href="recuentos_ventanas.csv">Datos por ventana</a> ·
    <a href="../README.md">Metodología y pies de figura</a></aside></main></html>''', encoding='utf-8')
