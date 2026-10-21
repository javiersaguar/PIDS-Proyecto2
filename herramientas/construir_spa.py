"""Empaqueta la SPA de resultados_eda/interactivos para GitHub Pages.

Uso: python3 herramientas/construir_spa.py [destino]

El destino por defecto es _site. Debe estar vacío o contener una construcción
previa de este script. Solo se usa la biblioteca estándar de Python.

La portada conserva el contenido de indice.html y adapta sus enlaces. Los
originales se publican bajo eda/ para mantener sus rutas y descargas existentes.
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


def construir(destino: Path) -> None:
    destino = destino.resolve()
    if destino == RAIZ or destino in RAIZ.parents or destino == EDA or EDA in destino.parents:
        raise ValueError('El destino no puede sustituir al repositorio ni a los resultados del EDA.')

    interactivos = EDA / 'interactivos'
    necesarios = ['indice.html', 'estilos.css', 'explorador.js', 'figuras.css',
                  'figuras.js', 'plotly.min.js', 'mapas_calor_por_video.html',
                  'mapas_calor_temporales.html', 'robots_por_fotograma.html',
                  'recuentos_fotogramas.csv', 'recuentos_ventanas.csv']
    for ruta in [*(interactivos / nombre for nombre in necesarios), EDA / 'README.md']:
        if not ruta.is_file():
            raise FileNotFoundError(f'Falta un recurso necesario: {ruta}')
    if not (EDA / 'para_informe').is_dir():
        raise FileNotFoundError(f'Falta la carpeta de exportaciones: {EDA / "para_informe"}')

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
    indice = (interactivos / 'indice.html').read_text(encoding='utf-8')
    (destino / 'index.html').write_text(adaptar_indice(indice), encoding='utf-8')
    (destino / '.nojekyll').touch()
    print(f'SPA en {destino}: 3 figuras, conclusiones y exportaciones del EDA')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Construye la SPA del EDA para GitHub Pages.')
    parser.add_argument('destino', nargs='?', default='_site', type=Path)
    argumentos = parser.parse_args()
    try:
        construir(argumentos.destino)
    except (OSError, ValueError) as error:
        parser.exit(1, f'No se pudo construir la SPA: {error}\n')
