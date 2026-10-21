"""Comprueba la portada de Pages, sus recursos y la reconstrucción del destino."""

from html.parser import HTMLParser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import construir_spa


class Enlaces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(valor for nombre, valor in attrs
                         if nombre in ('href', 'src') and valor)


class ConstruirSpaTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        base = Path(self.temporal.name)
        self.eda = base / 'fuente'
        self.interactivos = self.eda / 'interactivos'
        self.interactivos.mkdir(parents=True)
        exportaciones = self.eda / 'para_informe'
        exportaciones.mkdir()
        for formato in ('png', 'svg', 'pdf'):
            (exportaciones / f'figura.{formato}').write_text(f'Figura {formato}', encoding='utf-8')
        (self.eda / 'README.md').write_text('# Metodología', encoding='utf-8')
        self.indice = '''<!doctype html>
<html lang="es"><head><link rel="stylesheet" href="estilos.css">
<script src="explorador.js" defer></script></head><body>
<a href="#distribucion">Saltar a la figura</a>
<section id="distribucion"><h2>Distribución por vídeo</h2>
<iframe src="mapas_calor_por_video.html"></iframe>
<p>Qué concluimos: el 92 % de los centros.</p></section>
<a href="../para_informe/figura.svg" download>SVG</a>
<a href="../para_informe/figura.png" download>PNG</a>
<a href="../para_informe/figura.pdf" download>PDF</a>
<a href="../README.md">Metodología</a></body></html>'''
        (self.interactivos / 'indice.html').write_text(self.indice, encoding='utf-8')
        for nombre in ('estilos.css', 'explorador.js', 'figuras.css', 'figuras.js',
                       'plotly.min.js', 'recuentos_fotogramas.csv', 'recuentos_ventanas.csv'):
            (self.interactivos / nombre).write_text(f'Recurso {nombre}', encoding='utf-8')
        figura = ('<!doctype html><html><head><link rel="stylesheet" href="figuras.css">'
                  '<script src="figuras.js" defer></script></head><body>'
                  '<script src="plotly.min.js"></script></body></html>')
        for nombre in ('mapas_calor_por_video.html', 'mapas_calor_temporales.html',
                       'robots_por_fotograma.html'):
            (self.interactivos / nombre).write_text(figura, encoding='utf-8')
        self.destino = base / 'sitio'
        self.fuente = patch.object(construir_spa, 'EDA', self.eda)
        self.fuente.start()
        self.addCleanup(self.fuente.stop)

    def test_portada_conserva_conclusiones_anclas_y_recursos(self):
        construir_spa.construir(self.destino)
        texto = (self.destino / 'index.html').read_text(encoding='utf-8')
        self.assertIn('Qué concluimos: el 92 % de los centros.', texto)
        self.assertIn('href="#distribucion"', texto)
        self.assertIn('href="eda/interactivos/estilos.css"', texto)
        self.assertIn('src="eda/interactivos/mapas_calor_por_video.html"', texto)
        self.assertIn('href="eda/para_informe/figura.svg"', texto)
        self.assertIn('href="eda/README.md"', texto)
        self.assertTrue((self.destino / '.nojekyll').is_file())
        for pagina in self.destino.rglob('*.html'):
            enlaces = Enlaces()
            enlaces.feed(pagina.read_text(encoding='utf-8'))
            for url in enlaces.urls:
                partes = urlsplit(url)
                if partes.path:
                    with self.subTest(pagina=pagina, url=url):
                        self.assertTrue((pagina.parent / partes.path).is_file())

    def test_conserva_archivos_y_rutas_antiguas_sin_regenerar_datos(self):
        construir_spa.construir(self.destino)
        for fuente in self.interactivos.iterdir():
            self.assertEqual(fuente.read_bytes(),
                             (self.destino / 'eda' / 'interactivos' / fuente.name).read_bytes())
        self.assertEqual((self.interactivos / 'indice.html').read_text(encoding='utf-8'), self.indice)
        self.assertFalse((self.destino / 'datos').exists())

    def test_no_publica_documentacion_interna_ni_caches(self):
        for nombre in ('PRODUCT.md', 'DESIGN.md', 'notas.py', '.env'):
            (self.interactivos / nombre).write_text('interno', encoding='utf-8')
        for nombre in ('.impeccable', '__pycache__'):
            carpeta = self.interactivos / nombre
            carpeta.mkdir()
            (carpeta / 'interno.js').write_text('interno', encoding='utf-8')
        construir_spa.construir(self.destino)
        publico = self.destino / 'eda' / 'interactivos'
        for nombre in ('PRODUCT.md', 'DESIGN.md', 'notas.py', '.env', '.impeccable', '__pycache__'):
            self.assertFalse((publico / nombre).exists())

    def test_reconstruccion_retira_archivos_obsoletos(self):
        construir_spa.construir(self.destino)
        (self.destino / 'obsoleto.js').write_text('anterior', encoding='utf-8')
        construir_spa.construir(self.destino)
        self.assertFalse((self.destino / 'obsoleto.js').exists())
        self.assertTrue((self.destino / 'index.html').is_file())

    def test_no_borra_un_destino_con_archivos_ajenos(self):
        self.destino.mkdir()
        archivo = self.destino / 'trabajo.txt'
        archivo.write_text('conservar', encoding='utf-8')
        with self.assertRaises(ValueError):
            construir_spa.construir(self.destino)
        self.assertEqual(archivo.read_text(encoding='utf-8'), 'conservar')

    def test_fuente_incompleta_conserva_la_salida_anterior(self):
        construir_spa.construir(self.destino)
        portada = (self.destino / 'index.html').read_bytes()
        (self.interactivos / 'plotly.min.js').unlink()
        with self.assertRaises(FileNotFoundError):
            construir_spa.construir(self.destino)
        self.assertEqual((self.destino / 'index.html').read_bytes(), portada)

    def test_no_sustituye_el_repositorio_ni_las_fuentes(self):
        for destino in (construir_spa.RAIZ, construir_spa.RAIZ.parent,
                        self.eda, self.interactivos):
            with self.subTest(destino=destino), self.assertRaises(ValueError):
                construir_spa.construir(destino)

    def test_adapta_subrutas_sin_cambiar_urls_externas_textos_o_scripts(self):
        texto = '''<!doctype html><p>Ejemplo: href="no-cambiar.html"</p>
<!-- <a href="comentario.html"> -->
<script>const ejemplo = 'src="literal.js"';</script>
<a href="https://example.org/info">Externo</a><a href="/absoluta">Raíz</a>
<a href='#figura'>Ancla</a><img src='imagenes/vista.svg?x=1#detalle'/>
<script src="figuras.js" defer></script>'''
        salida = construir_spa.adaptar_indice(texto)
        self.assertIn('href="no-cambiar.html"', salida)
        self.assertIn('href="comentario.html"', salida)
        self.assertIn('src="literal.js"', salida)
        self.assertIn('href="https://example.org/info"', salida)
        self.assertIn('href="/absoluta"', salida)
        self.assertIn("href='#figura'", salida)
        self.assertIn("src='eda/interactivos/imagenes/vista.svg?x=1#detalle'", salida)
        url = 'eda/interactivos/figuras.js'
        self.assertIn(f'src="{url}"', salida)
        self.assertEqual(urljoin('https://equipo.github.io/PIDS-Proyecto2/', url),
                         'https://equipo.github.io/PIDS-Proyecto2/eda/interactivos/figuras.js')


if __name__ == '__main__':
    unittest.main()
