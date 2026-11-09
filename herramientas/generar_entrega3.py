"""Primer borrador de la memoria de la entrega 3: la de la entrega 2 más el Bloque 3.

Copia docs/informes/informe_entrega2.docx (editado a mano en Word, que no se toca) y le añade:

- en la portada, «Fases 1, 2 y 3», «Entrega 3 · Bloques 1, 2 y 3» y la fecha de entrega;
- el texto de docs/informe_bloque3_borrador.md, antes de «Referencias», con los estilos
  de la plantilla (títulos, texto, pies, tablas con cabecera azul y filas alternas, figuras);
- la referencia [21] al estudio del robot camuflado;
- las correcciones de la revisión de la entrega 2 (correcciones_entrega2.py): Bloques 1 y 2
  corregidos, columna del Bloque 3 en el reparto, referencias [22] a [28] y tabla de respuesta.

    python herramientas/generar_entrega3.py                 crea docs/informes/informe_entrega3.docx
    python herramientas/generar_entrega3.py --forzar        lo sobrescribe (se pierden los cambios a mano)

El borrador admite: «# » y «## » (títulos), «# Anexo ...» (lo que sigue va al final de los anexos,
antes de la respuesta a la revisión), párrafos, tablas Markdown seguidas de un pie
«*Tabla ...*», figuras «![Figura ...](ruta|ruta)» con rutas relativas a docs/, **negrita**, __entradilla__
(cursiva subrayada), ^superíndice^ y [PENDIENTE: ...] (resaltado en amarillo). Las líneas que empiezan por «>» se ignoran.
Después hay que abrirlo en Word, actualizar el índice (F9) y revisar la paginación.
"""

import argparse
import os
import re
import sys
from xml.sax.saxutils import escape

import docx
from docx.oxml import parse_xml
from docx.shared import Cm
from docx.text.paragraph import Paragraph

import correcciones_entrega2

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(RAIZ, 'docs')
ENTRADA = os.path.join(DOCS, 'informes', 'informe_entrega2.docx')
BORRADOR = os.path.join(DOCS, 'informe_bloque3_borrador.md')
SALIDA = os.path.join(DOCS, 'informes', 'informe_entrega3.docx')
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

PORTADA = {
    'MEMORIA DEL PROYECTO  FASES 1 Y 2': 'MEMORIA DEL PROYECTO  FASES 1, 2 Y 3',
    'Entrega 2 · Bloques 1 y 2': 'Entrega 3 · Bloques 1, 2 y 3',
    '03/11/2026': '15/11/2026',
}
REFERENCIA = ('[21] Grupo 2. Robot camuflado y robots aliados: ¿a qué dispara el detector? 2026. '
              'https://github.com/javiersaguar/PIDS-Proyecto2/blob/main/docs/senuelo_aliado.md')
ANCHO_TABLA = 9070            # dxa, como las tablas de la memoria


# --- lectura del borrador ------------------------------------------------------------
def leer_bloques(ruta):
    lineas = [l.rstrip('\n') for l in open(ruta, encoding='utf-8')]
    bloques, actual = [], []
    for l in lineas + ['']:
        if l.startswith('>'):
            continue
        if l.strip():
            actual.append(l)
            continue
        if actual:
            bloques.append(actual)
            actual = []
    salida = []
    for b in bloques:
        primera = b[0]
        if primera.startswith('## '):
            salida.append(('h2', primera[3:].strip()))
        elif primera.startswith('# '):
            salida.append(('h1', primera[2:].strip()))
        elif primera.startswith('|'):
            filas = [[c.strip() for c in l.strip().strip('|').split('|')] for l in b]
            filas = [f for f in filas if not all(re.fullmatch(r':?-+:?', c) for c in f)]
            salida.append(('tabla', filas))
        elif primera.startswith('!['):
            m = re.fullmatch(r'!\[(.*)\]\((.*)\)', ' '.join(b))
            salida.append(('figura', m.group(1), [os.path.join(DOCS, r) for r in m.group(2).split('|')]))
        elif primera.startswith('*') and ' '.join(b).endswith('*'):
            salida.append(('pie', ' '.join(b).strip('*')))
        else:
            salida.append(('p', ' '.join(l.strip() for l in b)))
    return salida


# --- XML de la plantilla -------------------------------------------------------------
def runs(texto, tam=None, color=None, negrita=False):
    """Runs de un texto con **negrita**, __cursiva subrayada__ (entradillas), ^superíndice^ y
    [PENDIENTE ...] resaltado; sin `código`."""
    texto = texto.replace('`', '')
    partes = re.split(r'(\*\*.+?\*\*|__.+?__|\^[^^\s]+\^|\[PENDIENTE[^\]]*\])', texto)
    xml = []
    for parte in partes:
        if not parte:
            continue
        b = negrita or parte.startswith('**')
        entradilla = parte.startswith('__') and parte.endswith('__') and len(parte) > 4
        sup = parte.startswith('^') and parte.endswith('^') and len(parte) > 2
        resaltar = parte.startswith('[PENDIENTE')
        if parte.startswith('**') or entradilla:
            parte = parte[2:-2]
        elif sup:
            parte = parte[1:-1]
        rpr = ('<w:b/>' if b else '') + ('<w:i/><w:iCs/>' if entradilla else '')
        rpr += (f'<w:color w:val="{color}"/>' if color else '')
        rpr += (f'<w:sz w:val="{tam}"/>' if tam else '') + ('<w:highlight w:val="yellow"/>' if resaltar else '')
        rpr += ('<w:u w:val="single"/>' if entradilla else '') + ('<w:vertAlign w:val="superscript"/>' if sup else '')
        rpr += '<w:lang w:val="es-ES"/>'
        xml.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(parte)}</w:t></w:r>')
    return ''.join(xml)


def parrafo(texto, estilo=None, extra=''):
    ppr = (f'<w:pStyle w:val="{estilo}"/>' if estilo else '') + extra
    return parse_xml(f'<w:p {W}><w:pPr>{ppr}<w:rPr><w:lang w:val="es-ES"/></w:rPr></w:pPr>{runs(texto)}</w:p>')


def anchos(filas, dxa_por_letra=95):
    """Anchos de columna: cada una cabe su palabra más larga y el resto se reparte según el texto."""
    n = len(filas[0])
    celdas = [[f[i] if i < len(f) else '' for f in filas] for i in range(n)]
    minimos = [max(len(p) for c in col for p in c.split() or ['']) * dxa_por_letra + 200 for col in celdas]
    pesos = [max(6, min(max(len(c) for c in col), 60)) for col in celdas]
    libre = max(0, ANCHO_TABLA - sum(minimos))
    a = [int(m + libre * p / sum(pesos)) for m, p in zip(minimos, pesos)]
    a[-1] += ANCHO_TABLA - sum(a)
    return a


def tabla(filas):
    cols = anchos(filas)
    borde = ''.join(f'<w:{l} w:val="single" w:sz="4" w:space="0" w:color="D9D9D9"/>'
                    for l in ('top', 'left', 'bottom', 'right'))
    margen = ''.join(f'<w:{l} w:w="65" w:type="dxa"/>' for l in ('top', 'left', 'bottom', 'right'))
    xml = [f'<w:tbl {W}><w:tblPr><w:tblW w:w="{ANCHO_TABLA}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" '
           'w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>'
           + ''.join(f'<w:gridCol w:w="{c}"/>' for c in cols) + '</w:tblGrid>']
    for i, fila in enumerate(filas):
        cabecera = i == 0
        relleno = '203B65' if cabecera else ('F1F4F8' if i % 2 else 'FFFFFF')
        trpr = '<w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if cabecera else '') + '</w:trPr>'
        celdas = []
        for c, ancho in enumerate(cols):
            texto = fila[c] if c < len(fila) else ''
            seguir = '<w:keepNext/>' if i < len(filas) - 1 else ''
            celdas.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/><w:tcBorders>{borde}</w:tcBorders>'
                f'<w:shd w:val="clear" w:color="auto" w:fill="{relleno}"/><w:tcMar>{margen}</w:tcMar>'
                f'<w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr>{seguir}'
                '<w:spacing w:before="40" w:after="40" w:line="252" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
                + runs(texto, tam=16, color='FFFFFF' if cabecera else None, negrita=cabecera) + '</w:p></w:tc>')
        xml.append(f'<w:tr>{trpr}{"".join(celdas)}</w:tr>')
    xml.append('</w:tbl>')
    return parse_xml(''.join(xml))


def poner_texto(p, texto):
    """Cambia el texto de un párrafo conservando el formato de su primer run."""
    rs = p.runs
    rs[0].text = texto
    for r in rs[1:]:
        r._r.getparent().remove(r._r)


# --- montaje ---------------------------------------------------------------------------
def generar(salida):
    doc = docx.Document(ENTRADA)
    todos = list(doc.paragraphs) + [p for t in doc.tables for f in t.rows for c in f.cells for p in c.paragraphs]
    for viejo, nuevo in PORTADA.items():
        hechos = [p for p in todos if p.text.strip() == viejo]
        if not hechos:
            raise SystemExit(f'No se encuentra «{viejo}» en {ENTRADA}')
        for p in hechos:
            poner_texto(p, nuevo)

    titulos = [p for p in doc.paragraphs if p.style.name == 'Heading 1']
    referencias = next(p for p in titulos if p.text.strip() == 'Referencias')
    anexos = next(p for p in titulos if p.text.strip() == 'Anexos')
    anexos._p.addprevious(parrafo(REFERENCIA, extra='<w:jc w:val="left"/>'))

    # Los anexos del borrador van detrás del último anexo, antes de los párrafos vacíos que
    # preceden a «Respuesta a la revisión anterior»
    respuesta = next(p for p in titulos if p.text.strip() == 'Respuesta a la revisión anterior')._p
    fin_anexos = respuesta
    while (fin_anexos.getprevious() is not None and fin_anexos.getprevious().tag == respuesta.tag
           and not ''.join(fin_anexos.getprevious().itertext()).strip()):
        fin_anexos = fin_anexos.getprevious()

    primero = True
    ancla = referencias._p
    for bloque in leer_bloques(BORRADOR):
        tipo = bloque[0]
        if tipo == 'h1' and bloque[1].startswith('Anexo '):
            ancla = fin_anexos
            el = parrafo(bloque[1], 'Ttulo2')
        elif tipo == 'h1':
            el = parrafo(bloque[1], 'Ttulo1', '<w:pageBreakBefore/>' if primero else '')
            primero = False
        elif tipo == 'h2':
            el = parrafo(bloque[1], 'Ttulo2')
        elif tipo == 'p':
            el = parrafo(bloque[1])
        elif tipo == 'pie':
            el = parrafo(bloque[1], 'Descripcin', '<w:keepLines/>')
        elif tipo == 'tabla':
            el = tabla(bloque[1])
        elif tipo == 'figura':
            el = parse_xml(f'<w:p {W}><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr></w:p>')
            ancla.addprevious(el)
            p = Paragraph(el, referencias._parent)
            ancho = Cm(15.5) if len(bloque[2]) == 1 else Cm(15.0 / len(bloque[2]))
            for i, ruta in enumerate(bloque[2]):
                if i:
                    p.add_run('   ')
                p.add_run().add_picture(ruta, width=ancho)
            el = parrafo(bloque[1], 'Descripcin', '<w:keepLines/>')
        ancla.addprevious(el)
    correcciones_entrega2.aplicar(doc, sys.modules[__name__])
    doc.save(salida)
    print(f'Creado {salida}')


def main(argv=None):
    p = argparse.ArgumentParser(description='Memoria de la entrega 3: entrega 2 + Bloque 3')
    p.add_argument('--salida', default=SALIDA)
    p.add_argument('--forzar', action='store_true', help='sobrescribir la salida si ya existe')
    a = p.parse_args(argv)
    if os.path.exists(a.salida) and not a.forzar:
        raise SystemExit(f'{a.salida} ya existe y puede tener cambios a mano. Usa --forzar o --salida otra.docx')
    generar(a.salida)


if __name__ == '__main__':
    sys.exit(main())
