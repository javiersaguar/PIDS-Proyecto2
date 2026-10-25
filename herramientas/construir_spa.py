"""Empaqueta las SPAs de los bloques 1 y 2 para GitHub Pages.

Uso: python3 herramientas/construir_spa.py [destino]

El destino por defecto es _site. Debe estar vacío o contener una construcción
previa de este script. Solo se usa la biblioteca estándar de Python.

La portada conserva el contenido de indice.html y adapta sus enlaces. El Bloque 2
se publica bajo bloque2/. Ambas páginas incluyen un selector de bloque.
Los originales del EDA se publican bajo eda/ para mantener sus rutas y descargas.
No se regeneran las figuras ni se requieren resultados de entrenamiento.
"""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import urlsplit, urlunsplit


RAIZ = Path(__file__).resolve().parent.parent
EDA = RAIZ / 'ENTREGA 1' / 'WEEK1' / 'resultados_eda'
BLOQUE2 = RAIZ / 'web' / 'Bloque2'
ESTILOS_NAVEGACION = RAIZ / 'web' / 'navegacion_bloques.css'
RUTA_INTERACTIVOS = 'eda/interactivos'
EXTENSIONES_PUBLICAS = {'.html', '.css', '.js', '.csv', '.png', '.pdf', '.jpg', '.jpeg',
                        '.svg', '.ico', '.woff', '.woff2'}
ATRIBUTO_URL = re.compile(r'''(\b(?:href|src)\s*=\s*)(["'])(.*?)\2''', re.IGNORECASE)


def adaptar_indice(texto: str) -> str:
    """Cambia solo enlaces de apertura; conserva textos, anclas y código."""
    class Enlaces(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.cambios = []
            self.lineas = [0]
            for linea in texto.splitlines(keepends=True):
                self.lineas.append(self.lineas[-1] + len(linea))

        def handle_starttag(self, tag, attrs):
            original = self.get_starttag_text()

            def adaptar(coincidencia):
                atributo, comilla, url = coincidencia.groups()
                partes = urlsplit(url)
                if partes.scheme or partes.netloc or not partes.path or url.startswith('/'):
                    return coincidencia.group(0)
                ruta = posixpath.normpath(posixpath.join(RUTA_INTERACTIVOS, partes.path))
                nueva = urlunsplit(('', '', ruta, partes.query, partes.fragment))
                return f'{atributo}{comilla}{nueva}{comilla}'

            nuevo = ATRIBUTO_URL.sub(adaptar, original)
            if nuevo != original:
                fila, columna = self.getpos()
                inicio = self.lineas[fila - 1] + columna
                self.cambios.append((inicio, inicio + len(original), nuevo))

        handle_startendtag = handle_starttag

    enlaces = Enlaces()
    enlaces.feed(texto)
    for inicio, fin, nuevo in reversed(enlaces.cambios):
        texto = texto[:inicio] + nuevo + texto[fin:]
    return texto


def ignorar_privados(carpeta, nombres):
    """Publica recursos web y omite documentación interna, cachés y metadatos."""
    return [nombre for nombre in nombres
            if nombre.startswith('.') or nombre == '__pycache__'
            or (not (Path(carpeta) / nombre).is_dir()
                and Path(nombre).suffix.lower() not in EXTENSIONES_PUBLICAS)]


def agregar_navegacion(texto: str, bloque: int) -> str:
    """Añade el selector a las copias publicadas, con rutas relativas a Pages."""
    cabecera = '<header class="page-header">'
    if texto.count(cabecera) != 1 or texto.count('</head>') != 1:
        raise ValueError(f'La página del Bloque {bloque} no tiene la cabecera esperada.')
    prefijo = '' if bloque == 1 else '../'
    enlaces = []
    for numero, ruta in ((1, 'index.html'), (2, 'bloque2/index.html')):
        activo = ' aria-current="page"' if numero == bloque else ''
        enlaces.append(f'<a href="{prefijo}{ruta}"{activo}>Bloque {numero}</a>')
    navegacion = ('\n      <nav class="navegacion-bloques" aria-label="Bloques del proyecto">'
                  + ''.join(enlaces) + '</nav>')
    texto = texto.replace(cabecera, cabecera + navegacion, 1)
    return texto.replace('</head>',
                         f'  <link rel="stylesheet" href="{prefijo}navegacion_bloques.css">\n</head>', 1)


def construir(destino: Path) -> None:
    destino = destino.resolve()
    if destino == RAIZ or destino in RAIZ.parents or any(
            destino == fuente or destino in fuente.parents or fuente in destino.parents
            for fuente in (EDA.resolve(), BLOQUE2.resolve())):
        raise ValueError('El destino no puede sustituir al repositorio ni a las fuentes de los bloques.')

    interactivos = EDA / 'interactivos'
    necesarios = ['indice.html', 'estilos.css', 'explorador.js', 'figuras.css',
                  'figuras.js', 'plotly.min.js', 'mapas_calor_por_video.html',
                  'mapas_calor_temporales.html', 'robots_por_fotograma.html',
                  'recuentos_fotogramas.csv', 'recuentos_ventanas.csv']
    necesarios_bloque2 = ['index.html', 'estilos.css', 'graficas.js', 'datos.js', 'plotly.min.js']
    for ruta in [*(interactivos / nombre for nombre in necesarios), EDA / 'README.md',
                 *(BLOQUE2 / nombre for nombre in necesarios_bloque2), ESTILOS_NAVEGACION]:
        if not ruta.is_file():
            raise FileNotFoundError(f'Falta un recurso necesario: {ruta}')
    if not (EDA / 'para_informe').is_dir():
        raise FileNotFoundError(f'Falta la carpeta de exportaciones: {EDA / "para_informe"}')

    # Valida ambas páginas antes de reemplazar una salida anterior.
    indice = (interactivos / 'indice.html').read_text(encoding='utf-8')
    portada = agregar_navegacion(adaptar_indice(indice), 1)
    segundo_bloque = agregar_navegacion((BLOQUE2 / 'index.html').read_text(encoding='utf-8'), 2)

    # Solo se reemplaza una salida identificable de este constructor.
    if destino.exists():
        if not destino.is_dir():
            raise ValueError('El destino debe ser una carpeta.')
        if any(destino.iterdir()):
            if not all((destino / ruta).is_file() for ruta in
                       ('.nojekyll', 'index.html', 'eda/interactivos/indice.html')):
                raise ValueError('El destino contiene archivos ajenos a esta construcción. Usa una carpeta vacía.')
            shutil.rmtree(destino)

    publico = destino / 'eda'
    publico.mkdir(parents=True, exist_ok=True)
    shutil.copytree(interactivos, publico / 'interactivos', ignore=ignorar_privados)
    shutil.copytree(EDA / 'para_informe', publico / 'para_informe', ignore=ignorar_privados)
    shutil.copy2(EDA / 'README.md', publico / 'README.md')
    shutil.copytree(BLOQUE2, destino / 'bloque2', ignore=ignorar_privados)
    shutil.copy2(ESTILOS_NAVEGACION, destino / 'navegacion_bloques.css')
    (destino / 'index.html').write_text(portada, encoding='utf-8')
    (destino / 'bloque2' / 'index.html').write_text(segundo_bloque, encoding='utf-8')
    (destino / '.nojekyll').touch()
    print(f'SPAs en {destino}: Bloque 1 (3 figuras) y Bloque 2 (4 figuras), con selector común')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Publica los bloques 1 y 2 con un selector en GitHub Pages.')
    parser.add_argument('destino', nargs='?', default='_site', type=Path)
    argumentos = parser.parse_args()
    try:
        construir(argumentos.destino)
    except (OSError, ValueError) as error:
        parser.exit(1, f'No se pudo construir la SPA: {error}\n')
