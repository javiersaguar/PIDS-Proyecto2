"""Prepara los datos y las miniaturas de la página del Bloque 3.

Uso, desde la raíz del repositorio:

    python web/Bloque3/preparar_datos.py ["ENTREGA 2/WEEK3/evidencias"]

Lee las carpetas de los dos intentos del 12/11 (las evidencias no se versionan) y
escribe `datos.js` y las miniaturas WebP de `imagenes/`. Necesita Pillow.
"""

import csv
import json
import math
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
EVIDENCIAS = RAIZ / 'ENTREGA 2' / 'WEEK3' / 'evidencias'

INTENTOS = [
    dict(clave='oficial', carpeta='20261112_155726', nombre='Demo oficial'),
    dict(clave='profesor', carpeta='20261112_160426', nombre='Intento del profesor'),
]
ANCHO, CALIDAD = 480, 55

# Plano medido en el laboratorio (circuito.py): x hacia delante, y positiva a la derecha.
PUNTOS = [[0, 0], [2.85, 0], [5.04, 0], [5.04, -1], [3.6, -1], [3.6, 0],
          [6.48, 0], [6.48, -0.7], [8.78, -0.7]]
RIVALES = [
    dict(nombre='Rival 1', x=2.85, y=1.2),
    dict(nombre='Robot camuflado', x=2.85, y=-1.2, camuflado=True),
    dict(nombre='Rival 2', x=4.86, y=-2.2, hasta_x=4.0),
    dict(nombre='Rival 3', x=5.73, y=-0.7, escondido=True),
]
TRAMOS = [
    dict(fase='P1-ruta', desde=0, hasta=1, texto='Túnel: 2,85 m a 0,5 m/s'),
    dict(fase='R1-ruta', desde=1, hasta=3, texto='2,19 m a 0,4 m/s y 1 m a la izquierda'),
    dict(fase='R1-marcha', desde=3, hasta=4, texto='1,44 m marcha atrás a 0,1 m/s, disparando al rival 2'),
    dict(fase='R1-vuelta', desde=4, hasta=5, texto='1 m a la derecha'),
    dict(fase='R2-ruta', desde=5, hasta=7, texto='2,88 m a 0,5 m/s y 0,7 m a la izquierda'),
    dict(fase='R2-marcha', desde=7, hasta=8, texto='2,3 m a 0,1 m/s con la torreta hacia atrás, disparando al rival 3'),
]
FIJO = {'inicio': 0, 'P1-parada': 1, 'baile': 8}


def segundos(hora):
    return datetime.strptime(hora.replace('-', ':'), '%H:%M:%S')


def punto_en(desde, hasta, f):
    """Punto a una fracción f de la longitud del tramo de PUNTOS[desde] a PUNTOS[hasta]."""
    trozos = list(zip(PUNTOS[desde:hasta], PUNTOS[desde + 1:hasta + 1]))
    largos = [math.dist(a, b) for a, b in trozos]
    resto = f * sum(largos)
    for (a, b), largo in zip(trozos, largos):
        if resto <= largo or largo == largos[-1]:
            g = min(1, resto / largo) if largo else 0
            return [round(a[0] + (b[0] - a[0]) * g, 3), round(a[1] + (b[1] - a[1]) * g, 3)]
        resto -= largo
    return PUNTOS[hasta]


def miniatura(origen, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(origen) as im:
        im = im.convert('RGB')
        im.thumbnail((ANCHO, ANCHO))
        im.save(destino, 'WEBP', quality=CALIDAD, method=6)


def recorrido(carpeta, clave, inicio):
    """Fotos cada 0,5 s con su fase y una posición interpolada con el plano."""
    fotos = []
    for ruta in sorted((carpeta / 'recorrido').glob('*.jpg')):
        n, fase, hora = re.match(r'(\d+)_(.+)_(\d\d-\d\d-\d\d)\.jpg', ruta.name).groups()
        fotos.append(dict(n=int(n), fase=fase, t=(segundos(hora) - inicio).seconds, ruta=ruta))
    # Los dos tramos de R1-ruta (antes y después del retroceso) se separan.
    visto_marcha = False
    for f in fotos:
        if f['fase'] == 'R1-marcha':
            visto_marcha = True
        elif f['fase'] == 'R1-ruta' and visto_marcha:
            f['fase'] = 'R1-vuelta'
    salida = []
    for fase, grupo in agrupar(fotos):
        tramo = next((t for t in TRAMOS if t['fase'] == fase), None)
        for i, f in enumerate(grupo):
            if tramo:
                pos = punto_en(tramo['desde'], tramo['hasta'], (i + 0.5) / len(grupo))
            else:
                pos = PUNTOS[FIJO.get(fase, 1)]
            nombre = f'{f["n"]:04d}.webp'
            miniatura(f['ruta'], AQUI / 'imagenes' / clave / 'recorrido' / nombre)
            salida.append(dict(t=f['t'], fase=fase, x=pos[0], y=pos[1],
                               img=f'imagenes/{clave}/recorrido/{nombre}'))
    return salida


def agrupar(fotos):
    grupos = []
    for f in fotos:
        if grupos and grupos[-1][0] == f['fase']:
            grupos[-1][1].append(f)
        else:
            grupos.append((f['fase'], [f]))
    return grupos


def detecciones(carpeta, clave, inicio):
    filas = list(csv.DictReader(open(carpeta / 'registro.csv', encoding='utf-8')))
    por_segundo = {}
    for fila in filas:
        por_segundo.setdefault(fila['momento'], []).append(fila)
    salida = []
    for fila in filas:
        mismas = por_segundo[fila['momento']]
        t = (segundos(fila['momento']) - inicio).seconds + mismas.index(fila) / len(mismas)
        nombre = f'{int(fila["n"]):03d}.webp'
        miniatura(carpeta / fila['imagen'], AQUI / 'imagenes' / clave / 'detecciones' / nombre)
        salida.append(dict(
            n=int(fila['n']), t=round(t, 2), parada=fila['parada'], fase=fila['fase'],
            yaw=round(float(fila['yaw']), 1), ms=round(float(fila['ms_inferencia'])),
            conf=[float(c) for c in fila['confianzas'].split()],
            aceptadas=int(fila['n_aceptadas'] or 0), disparos=int(fila['disparos'] or 0),
            img=f'imagenes/{clave}/detecciones/{nombre}'))
    return salida


def main():
    evidencias = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCIAS
    shutil.rmtree(AQUI / 'imagenes', ignore_errors=True)
    datos = dict(puntos=PUNTOS, rivales=RIVALES, tramos=TRAMOS, umbral=0.95,
                 umbral_camuflado=0.7, intentos=[])
    for intento in INTENTOS:
        carpeta = evidencias / intento['carpeta']
        primera = sorted((carpeta / 'recorrido').glob('*.jpg'))[0].name
        inicio = segundos(re.search(r'(\d\d-\d\d-\d\d)\.jpg', primera).group(1))
        datos['intentos'].append(dict(
            clave=intento['clave'], nombre=intento['nombre'],
            hora=inicio.strftime('%H:%M'),
            recorrido=recorrido(carpeta, intento['clave'], inicio),
            detecciones=detecciones(carpeta, intento['clave'], inicio)))
    texto = json.dumps(datos, ensure_ascii=False, separators=(',', ':'))
    (AQUI / 'datos.js').write_text(
        '// Generado por preparar_datos.py a partir de las evidencias del 12/11/2026.\n'
        f'window.DATOS_BLOQUE3 = {texto};\n', encoding='utf-8')
    total = sum(p.stat().st_size for p in (AQUI / 'imagenes').rglob('*.webp'))
    print(f'datos.js y {sum(1 for _ in (AQUI / "imagenes").rglob("*.webp"))} miniaturas '
          f'({total / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
