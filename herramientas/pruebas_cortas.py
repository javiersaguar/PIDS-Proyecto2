#!/usr/bin/env python3
"""Pruebas cortas del Bloque 2 (solo validacion): arquitecturas sin aumento, lote y tasa de aprendizaje.

    python herramientas/pruebas_cortas.py lanzar    # ejecuta lo que falte, una prueba tras otra
    python herramientas/pruebas_cortas.py estado    # tabla con lo hecho hasta ahora
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cadena_entrenamientos as c

SALIDA = c.CADENA / 'pruebas_cortas.json'
EPOCAS_ARQ, EPOCAS_AJUSTE = 6, 3


def cfg(modelo, suf, epocas, lr=0.001, lote=8, acum=1):
    return dict(model_name=modelo, usar_aumento=False, perfil_aumento=c.PERFIL, lr=lr, num_epochs=epocas,
                batch_size=lote, acumulacion_gradiente=acum, sufijo_experimento=suf, reanudar=True)


def plan():
    p = [('arquitectura', cfg('faster_rcnn_v1', 'corto', EPOCAS_ARQ))]
    for b in (16, 32, 1, 2):
        p.append(('lote', cfg('faster_rcnn_v1', f'corto_bs{b}', EPOCAS_AJUSTE, lote=b)))
    for lr in (1e-5, 1e-2, 1e-1):
        p.append(('lr', cfg('faster_rcnn_v1', 'corto_lr' + format(lr, 'g').replace('.', 'p'), EPOCAS_AJUSTE, lr=lr)))
    for m, lote, acum in [('ssd_v2', 8, 1), ('ssd_v1', 8, 1), ('faster_rcnn_v3', 8, 1), ('retinanet_v1', 8, 1),
                          ('retinanet_v2', 8, 1), ('faster_rcnn_v2', 4, 2)]:
        p.append(('arquitectura', cfg(m, 'corto', EPOCAS_ARQ, lote=lote, acum=acum)))
    return p


def nombre(k):
    return f"{k['model_name']}_sin_aug_{k['sufijo_experimento']}"


def historial(exp):
    return c.leer_json(c.WEEK2 / 'resultados_train' / exp / 'historial.json', {})


def error_del_log(log):
    try:
        texto = Path(log).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''
    m = re.findall(r'^\w*(?:Error|Exception)[^\n]*', texto, flags=re.M)
    return m[-1][:400] if m else texto[-300:]


def lanzar():
    c.comprobar_gpu()
    estado = c.leer_json(SALIDA, {})
    for tipo, k in plan():
        exp = nombre(k)
        if (c.WEEK2 / 'resultados_train' / exp / 'resumen.json').is_file():
            print(f'[{c.ahora()}] {exp}: ya hecho', flush=True)
            continue
        if estado.get(exp, {}).get('fallo'):
            print(f'[{c.ahora()}] {exp}: ya fallo ({estado[exp]["fallo"][:60]})', flush=True)
            continue
        log = c.CADENA / 'logs' / f'{exp}.log'
        log.unlink(missing_ok=True)
        print(f'[{c.ahora()}] {exp}: empieza', flush=True)
        t0 = time.time()
        rc = c.ejecutar(c.WEEK2 / 'train.ipynb', f'{exp}_train', k, log)
        e = dict(tipo=tipo, config=k, minutos=round((time.time() - t0) / 60, 1), codigo=rc)
        if rc != 0:
            e['fallo'] = ('sin memoria: ' if c.sin_memoria(log) else '') + error_del_log(log)
        estado[exp] = e
        c.escribir_json(SALIDA, estado)
        print(f'[{c.ahora()}] {exp}: codigo {rc} en {e["minutos"]} min', flush=True)
    print('Terminado', flush=True)


def estado():
    est = c.leer_json(SALIDA, {})
    for tipo, k in plan():
        exp = nombre(k)
        h = historial(exp)
        ap = [round(x, 4) for x in h.get('valid_map_50', [])]
        fin = (c.WEEK2 / 'resultados_train' / exp / 'resumen.json').is_file()
        print(f"{tipo[:4]} {exp:42s} {'OK ' if fin else '...'} ap50={ap} mejor={h.get('best_epoch')} "
              f"mem={h.get('mem_pico_mib')} {est.get(exp, {}).get('fallo', '')[:90]}")


if __name__ == '__main__':
    {'lanzar': lanzar, 'estado': estado}[sys.argv[1]]()
