"""Comprueba las anotaciones PascalVOC del dataset según docs/criterios_anotacion.md.

Uso:
    python revisar_anotaciones.py validar <carpeta_data_train>
    python revisar_anotaciones.py acuerdo <carpeta_persona_1> <carpeta_persona_2> [...]

`validar` recorre cada secuencia (<carpeta>/<secuencia>/{images,labels}) y avisa de
imágenes sin .xml, nombres de clase distintos de `robot`, cajas degeneradas, fuera de
la imagen o más pequeñas que el mínimo acordado.

`acuerdo` compara las anotaciones que varias personas han hecho de las MISMAS imágenes
(ronda de calibración): cada carpeta contiene los .xml de una persona. Empareja las
cajas por IoU y resume, por pareja, el IoU medio y los robots que solo anotó uno.

Solo usa la biblioteca estándar de Python.
"""

import os
import sys
import itertools
import xml.etree.ElementTree as ET

CLASE = 'robot'
LADO_MINIMO = 10        # px: por debajo no se anota (regla R6)
LADO_DIFICIL = 30       # px: por debajo se marca difficult (regla R6)
IOU_EMPAREJAR = 0.5     # IoU mínimo para considerar que dos cajas son el mismo robot
IOU_OBJETIVO = 0.8     # Acuerdo mínimo de cada pareja en la calibración
MIN_IMAGENES_CALIBRACION = 20
EXTENSIONES = ('.jpg', '.jpeg', '.png')


def leer_xml(ruta):
    """Devuelve (ancho, alto, lista de objetos) de un .xml PascalVOC."""
    raiz = ET.parse(ruta).getroot()
    tam = raiz.find('size')
    ancho = int(tam.find('width').text) if tam is not None else None
    alto = int(tam.find('height').text) if tam is not None else None
    if not ancho or not alto or ancho < 0 or alto < 0:
        raise ValueError('faltan dimensiones válidas de imagen')
    objetos = []
    for obj in raiz.iter('object'):
        caja = obj.find('bndbox')
        dificil = obj.find('difficult')
        objetos.append({
            'nombre': (obj.find('name').text or '').strip() if obj.find('name') is not None else '',
            'caja': [int(float(caja.find(c).text)) for c in ('xmin', 'ymin', 'xmax', 'ymax')],
            'dificil': dificil is not None and dificil.text.strip() == '1',
        })
    return ancho, alto, objetos


def listar(carpeta, extensiones):
    if not os.path.isdir(carpeta):
        return {}
    return {os.path.splitext(f)[0]: f for f in sorted(os.listdir(carpeta))
            if not f.startswith('.') and f.lower().endswith(extensiones)}


def validar(carpeta_datos):
    if not os.path.isdir(carpeta_datos):
        print(f'ERROR: no existe la carpeta {carpeta_datos}')
        return 1
    errores, avisos = [], []
    total = {'imagenes': 0, 'xml': 0, 'vacias': 0, 'robots': 0, 'dificiles': 0, 'pequenos': 0}
    secuencias = [s for s in sorted(os.listdir(carpeta_datos))
                  if os.path.isdir(os.path.join(carpeta_datos, s)) and not s.startswith('.')]
    print(f'{"secuencia":<28}{"imágenes":>9}{"xml":>6}{"vacías":>8}{"robots":>8}{"difficult":>10}')
    for seq in secuencias:
        imagenes = listar(os.path.join(carpeta_datos, seq, 'images'), EXTENSIONES)
        etiquetas = listar(os.path.join(carpeta_datos, seq, 'labels'), ('.xml',))
        if not imagenes and not etiquetas:
            continue
        cuenta = {'vacias': 0, 'robots': 0, 'dificiles': 0}
        for nombre in sorted(set(imagenes) - set(etiquetas)):
            errores.append(f'{seq}/{imagenes[nombre]}: imagen sin .xml (si no tiene robots, guárdala igualmente con Ctrl+S)')
        for nombre in sorted(set(etiquetas) - set(imagenes)):
            errores.append(f'{seq}/labels/{etiquetas[nombre]}: .xml sin imagen')
        for nombre, fichero in etiquetas.items():
            ruta = f'{seq}/labels/{fichero}'
            try:
                ancho, alto, objetos = leer_xml(os.path.join(carpeta_datos, seq, 'labels', fichero))
            except (ET.ParseError, AttributeError, ValueError, OverflowError) as e:
                errores.append(f'{ruta}: no se puede leer ({e})')
                continue
            if not objetos:
                cuenta['vacias'] += 1
            for i, o in enumerate(objetos, 1):
                x1, y1, x2, y2 = o['caja']
                w, h = x2 - x1, y2 - y1
                cuenta['robots'] += 1
                cuenta['dificiles'] += o['dificil']
                if o['nombre'] != CLASE:
                    errores.append(f'{ruta} caja {i}: clase "{o["nombre"]}" (debe ser "{CLASE}")')
                if w <= 0 or h <= 0:
                    errores.append(f'{ruta} caja {i}: caja degenerada {o["caja"]} (rompe el entrenamiento)')
                    continue
                if ancho and alto and (x1 < 0 or y1 < 0 or x2 > ancho or y2 > alto):
                    errores.append(f'{ruta} caja {i}: se sale de la imagen {ancho}x{alto}: {o["caja"]}')
                if min(w, h) < LADO_MINIMO:
                    errores.append(f'{ruta} caja {i}: {w}x{h} px, menor que el mínimo de {LADO_MINIMO} px (R6)')
                    total['pequenos'] += 1
                elif w < LADO_DIFICIL and not o['dificil']:
                    avisos.append(f'{ruta} caja {i}: {w} px de ancho sin marcar difficult (R6)')
            for a, b in itertools.combinations(range(len(objetos)), 2):
                if iou(objetos[a]['caja'], objetos[b]['caja']) > 0.9:
                    avisos.append(f'{ruta}: cajas {a + 1} y {b + 1} casi idénticas (¿duplicada?)')
        print(f'{seq:<28}{len(imagenes):>9}{len(etiquetas):>6}{cuenta["vacias"]:>8}{cuenta["robots"]:>8}{cuenta["dificiles"]:>10}')
        total['imagenes'] += len(imagenes)
        total['xml'] += len(etiquetas)
        for k in ('vacias', 'robots', 'dificiles'):
            total[k] += cuenta[k]
    print(f'{"TOTAL":<28}{total["imagenes"]:>9}{total["xml"]:>6}{total["vacias"]:>8}{total["robots"]:>8}{total["dificiles"]:>10}')
    if not total['imagenes']:
        errores.append('no se han encontrado imágenes; pasa una carpeta con secuencias images/labels (por ejemplo, un lote)')
    if total['xml']:
        print(f'\nImágenes sin robots: {100 * total["vacias"] / total["xml"]:.1f} % (orientativo: 5-10 %)')
    for titulo, lista in (('ERRORES', errores), ('AVISOS', avisos)):
        if lista:
            print(f'\n{titulo} ({len(lista)}):')
            for linea in lista:
                print(f'  - {linea}')
    print('\nSin errores.' if not errores else f'\n{len(errores)} errores que hay que corregir.')
    return 1 if errores else 0


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def emparejar(cajas_a, cajas_b):
    """Emparejamiento voraz por IoU descendente. Devuelve (IoUs emparejados, solo_a, solo_b)."""
    pares = sorted(((iou(a, b), i, j) for i, a in enumerate(cajas_a) for j, b in enumerate(cajas_b)), reverse=True)
    usados_a, usados_b, ious = set(), set(), []
    for valor, i, j in pares:
        if valor < IOU_EMPAREJAR:
            break
        if i not in usados_a and j not in usados_b:
            usados_a.add(i)
            usados_b.add(j)
            ious.append(valor)
    return ious, len(cajas_a) - len(usados_a), len(cajas_b) - len(usados_b)


def acuerdo(carpetas):
    if len(carpetas) < 2 or len(set(os.path.abspath(c) for c in carpetas)) != len(carpetas):
        print('ERROR: indica al menos dos carpetas distintas de anotadores.')
        return 1
    anotaciones = {}
    for c in carpetas:
        if not os.path.isdir(c):
            print(f'ERROR: no existe la carpeta {c}')
            return 1
        archivos = listar(c, ('.xml',))
        if not archivos:
            print(f'ERROR: {c} no tiene anotaciones; la calibración está pendiente.')
            return 1
        try:
            leidos = {n: leer_xml(os.path.join(c, f)) for n, f in archivos.items()}
        except (ET.ParseError, AttributeError, ValueError, OverflowError) as e:
            print(f'ERROR: XML inválido en {c}: {e}')
            return 1
        for n, (ancho, alto, objetos) in leidos.items():
            for o in objetos:
                x1, y1, x2, y2 = o['caja']
                if (o['nombre'] != CLASE or min(x2 - x1, y2 - y1) < LADO_MINIMO
                        or x1 < 0 or y1 < 0 or x2 > ancho or y2 > alto):
                    print(f'ERROR: clase o caja inválida en {c}/{archivos[n]}')
                    return 1
        anotaciones[c] = {n: [o['caja'] for o in datos[2]] for n, datos in leidos.items()}
    comunes = set.intersection(*(set(v) for v in anotaciones.values()))
    union = set.union(*(set(v) for v in anotaciones.values()))
    if comunes != union or len(comunes) < MIN_IMAGENES_CALIBRACION:
        print(f'ERROR: todos deben anotar las mismas {MIN_IMAGENES_CALIBRACION} imágenes como mínimo '
              f'(comunes: {len(comunes)}, presentes en alguna carpeta: {len(union)}).')
        return 1
    print(f'Imágenes comunes a todos: {len(comunes)}\n')
    print(f'{"pareja":<40}{"IoU medio":>10}{"emparejados":>12}{"solo 1º":>9}{"solo 2º":>9}')
    detalle = []
    todos = []
    cumple = True
    for a, b in itertools.combinations(carpetas, 2):
        ious, solo_a, solo_b = [], 0, 0
        for img in sorted(comunes):
            i, sa, sb = emparejar(anotaciones[a][img], anotaciones[b][img])
            ious += i
            solo_a += sa
            solo_b += sb
            if sa or sb or (i and min(i) < 0.7):
                detalle.append(f'{img}: {os.path.basename(a)} vs {os.path.basename(b)} -> '
                               f'solo 1º={sa}, solo 2º={sb}, IoU mínimo={min(i) if i else 0:.2f}')
        todos += ious
        medio = sum(ious) / len(ious) if ious else 0
        cumple = cumple and bool(ious) and medio >= IOU_OBJETIVO and solo_a == 0 and solo_b == 0
        nombre = f'{os.path.basename(os.path.normpath(a))} vs {os.path.basename(os.path.normpath(b))}'
        print(f'{nombre:<40}{medio:>10.3f}{len(ious):>12}{solo_a:>9}{solo_b:>9}')
    if todos:
        print(f'\nIoU medio global: {sum(todos) / len(todos):.3f} (objetivo: >= 0,80)')
    if detalle:
        print('\nImágenes a comentar en grupo:')
        for linea in detalle:
            print(f'  - {linea}')
    print('\nCalibración superada.' if cumple else '\nCalibración pendiente: revisar parejas con IoU < 0,80 o robots sin pareja.')
    return 0 if cumple else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) >= 3 and sys.argv[1] == 'validar':
        sys.exit(validar(sys.argv[2]))
    if len(sys.argv) >= 4 and sys.argv[1] == 'acuerdo':
        sys.exit(acuerdo(sys.argv[2:]))
    print(__doc__)
    sys.exit(2)
