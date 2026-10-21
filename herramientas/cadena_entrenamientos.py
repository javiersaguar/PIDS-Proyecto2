#!/usr/bin/env python3
"""Encadena entrenamientos y evaluaciones en validación, uno tras otro, en el JupyterHub.

Desde la raíz del repositorio:

    python herramientas/cadena_entrenamientos.py preflight   # prueba cada modelo en pequeño y decide el lote
    python herramientas/cadena_entrenamientos.py cadena      # fase 1 y fase 2 (llama antes al preflight si falta)
    python herramientas/cadena_entrenamientos.py estado      # qué se ha hecho y qué falta
    python herramientas/cadena_entrenamientos.py empaquetar  # resultados en un zip, sin los pesos

Pensado para lanzarse con nohup. Se puede relanzar: salta lo que ya tiene su evaluación y
reanuda el entrenamiento que quedó a medias.

- Fase 1: los siete modelos del script original con el perfil de aumento `robusto_v1` y lr 0,001.
- Fase 2: los TOP_FASE2 mejores por AP@0,5 en validación, con lr 0,0005 y 0,002.

Cada experimento ejecuta train.ipynb y test.ipynb (conjunto `val`) con la configuración en
PIDS_CONFIG. El test no se toca. Solo usa la biblioteca estándar.
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEEK1 = RAIZ / 'ENTREGA 1' / 'WEEK1'
WEEK2 = RAIZ / 'ENTREGA 1' / 'WEEK2'
CADENA = WEEK2 / 'cadena'

PERFIL = 'robusto_v1'
# De menor a mayor coste: los resultados llegan antes y un fallo se ve pronto
MODELOS = ['ssd_v2', 'ssd_v1', 'faster_rcnn_v3', 'faster_rcnn_v1', 'retinanet_v1', 'faster_rcnn_v2', 'retinanet_v2']
LR_BASE = 0.001
LR_FASE2 = (0.0005, 0.002)
TOP_FASE2 = 3
EPOCAS, EPOCAS_LR_BAJO = 12, 15           # el mejor AP@0,5 de los entrenamientos anteriores cae entre la época 2 y la 29
IMAGENES = {'train': 3184, 'val': 672, 'test': 718}   # esperadas en datasets_experimentos/<perfil>
CANDIDATOS_LOTE = ((8, 1), (4, 2), (2, 4))            # (lote, acumulación): lote efectivo 8
PASOS_PRUEBA, IMAGENES_PRUEBA = 20, 48


# ------------------------------------------------------------------ nombres y tablas
def lr_txt(lr: float) -> str:
    """0,001 -> 'lr001'; 0,0005 -> 'lr0005'."""
    return 'lr' + format(lr, 'g').split('.')[1]


def sufijo(lr: float) -> str:
    return f'{PERFIL}_{lr_txt(lr)}'


def nombre(modelo: str, lr: float) -> str:
    return f'{modelo}_aug_{sufijo(lr)}'


def epocas(lr: float) -> int:
    return EPOCAS_LR_BAJO if lr < LR_BASE else EPOCAS


def ahora() -> str:
    return datetime.now().isoformat(timespec='seconds')


def leer_json(ruta: Path, defecto=None):
    try:
        return json.loads(Path(ruta).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def escribir_json(ruta: Path, datos) -> None:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(datos, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


def leer_csv(ruta: Path) -> list:
    try:
        with open(ruta, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def resultado_val(exp: str):
    """resumen.json de la evaluación en validación de un experimento, o None."""
    return leer_json(WEEK2 / 'resultados_test' / f'{exp}_val' / 'resumen.json')


def ap50(resumen: dict, grupo: str = 'todos') -> float:
    return next((float(f['map_50']) for f in resumen['map'] if f['grupo'] == grupo), float('nan'))


def elegir_mejores(candidatos: dict, n: int) -> list:
    """candidatos: {modelo: resumen de la evaluación}. Mayor AP@0,5; a igualdad, mejor en difficult."""
    return sorted(candidatos, key=lambda m: (-ap50(candidatos[m]), -ap50(candidatos[m], 'difficult')))[:n]


def parchear_perfil(nb: dict, perfil: str) -> dict:
    """Copia de data_aug.ipynb con otro PERFIL_AUMENTO, sin tocar el original."""
    celdas = [c for c in nb['cells'] if c['cell_type'] == 'code' and "PERFIL_AUMENTO = 'base'" in ''.join(c['source'])]
    if len(celdas) != 1:
        raise ValueError(f'Se esperaba una celda con PERFIL_AUMENTO, hay {len(celdas)}')
    fuente = ''.join(celdas[0]['source'])
    if fuente.count("PERFIL_AUMENTO = 'base'") != 1:
        raise ValueError('PERFIL_AUMENTO = \'base\' no aparece exactamente una vez')
    fuente = fuente.replace("PERFIL_AUMENTO = 'base'", f"PERFIL_AUMENTO = '{perfil}'")
    lineas = fuente.split('\n')
    celdas[0]['source'] = [l + '\n' for l in lineas[:-1]] + ([lineas[-1]] if lineas[-1] else [])
    return nb


# ------------------------------------------------------------------ ejecución de notebooks
def ejecutar(notebook: Path, salida: str, cfg, log: Path) -> int:
    """nbconvert --execute con PIDS_CONFIG; devuelve el código de salida."""
    (CADENA / 'ejecutados').mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    orden = [sys.executable, '-m', 'nbconvert', '--to', 'notebook', '--execute', str(notebook),
             '--output', salida, '--output-dir', str(CADENA / 'ejecutados'), '--ExecutePreprocessor.timeout=-1']
    if os.environ.get('PIDS_KERNEL'):                       # opcional: nombre del kernel de Jupyter
        orden.append(f"--ExecutePreprocessor.kernel_name={os.environ['PIDS_KERNEL']}")
    entorno = dict(os.environ, NO_ALBUMENTATIONS_UPDATE='1')
    entorno.pop('PIDS_CONFIG', None)
    if cfg is not None:
        entorno['PIDS_CONFIG'] = json.dumps(cfg)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(f'\n=== {ahora()} {notebook.name} -> {salida}\n')
        f.flush()
        return subprocess.run(orden, cwd=str(notebook.parent), env=entorno, stdout=f, stderr=subprocess.STDOUT).returncode


def sin_memoria(log: Path) -> bool:
    try:
        cola = Path(log).read_text(encoding='utf-8', errors='replace')[-30000:].lower()
    except OSError:
        return False
    return 'outofmemoryerror' in cola or 'out of memory' in cola


def limpiar(exp: str) -> None:
    """Borra modelos y resultados de un experimento de prueba. Solo los de preflight."""
    assert exp.endswith('_preflight'), exp
    for ruta in (RAIZ / 'models' / exp, WEEK2 / 'resultados_train' / exp, WEEK2 / 'resultados_test' / f'{exp}_val'):
        shutil.rmtree(ruta, ignore_errors=True)


def borrar_entrenamiento(exp: str) -> None:
    """Para repetir un entrenamiento que falló desde cero (no se puede reanudar con otro lote)."""
    for ruta in (RAIZ / 'models' / exp, WEEK2 / 'resultados_train' / exp, WEEK2 / 'resultados_test' / f'{exp}_val'):
        shutil.rmtree(ruta, ignore_errors=True)


# ------------------------------------------------------------------ datos del perfil
def contar_jpg(carpeta: Path) -> int:
    return sum(1 for _ in carpeta.rglob('*.jpg')) if carpeta.is_dir() else 0


def datos_listos() -> bool:
    destino = RAIZ / 'datasets_experimentos' / PERFIL
    return all(contar_jpg(destino / f'data_{k}') == n for k, n in IMAGENES.items())


def generar_datos() -> None:
    """Ejecuta data_aug.ipynb con el perfil. Unos 15 minutos."""
    if datos_listos():
        print(f'[{ahora()}] datos de {PERFIL} ya listos', flush=True)
        return
    destino = RAIZ / 'datasets_experimentos' / PERFIL
    # Una generación a medias se rehace, pero solo se borra lo que creó data_aug.ipynb (lleva su marca)
    for carpeta in [destino / f'data_{k}' for k in IMAGENES]:
        if carpeta.exists():
            if not (carpeta / '.generado_por_data_aug.json').is_file():
                raise RuntimeError(f'{carpeta} existe y no la creó data_aug.ipynb: no se borra')
            shutil.rmtree(carpeta)
    nb = parchear_perfil(json.load(open(WEEK1 / 'data_aug.ipynb', encoding='utf-8')), PERFIL)
    temporal = WEEK1 / f'_data_aug_{PERFIL}.ipynb'
    temporal.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'[{ahora()}] generando datos de {PERFIL}...', flush=True)
    try:
        rc = ejecutar(temporal, f'data_aug_{PERFIL}', None, CADENA / 'logs' / f'datos_{PERFIL}.log')
    finally:
        temporal.unlink(missing_ok=True)
    if rc != 0 or not datos_listos():
        cuentas = {k: contar_jpg(destino / f'data_{k}') for k in IMAGENES}
        raise RuntimeError(f'La generación de datos falló (código {rc}); imágenes {cuentas}, esperadas {IMAGENES}')
    print(f'[{ahora()}] datos listos', flush=True)


# ------------------------------------------------------------------ preflight
def configuracion(modelo: str, lr: float, lote: int, acum: int, **extra) -> dict:
    cfg = dict(model_name=modelo, usar_aumento=True, perfil_aumento=PERFIL, lr=lr, num_epochs=epocas(lr),
               batch_size=lote, acumulacion_gradiente=acum, sufijo_experimento=sufijo(lr), reanudar=True)
    cfg.update(extra)
    return cfg


def preflight() -> dict:
    """Entrena 20 pasos y evalúa 48 imágenes con cada modelo; elige el lote y estima el tiempo."""
    generar_datos()
    plan = {}
    for modelo in MODELOS:
        info = {'viable': False}
        exp = f'{modelo}_aug_preflight'
        log = CADENA / 'logs' / f'preflight_{modelo}.log'
        for lote, acum in CANDIDATOS_LOTE:
            limpiar(exp)
            cfg = configuracion(modelo, LR_BASE, lote, acum, num_epochs=1, sufijo_experimento='preflight',
                                reanudar=False, max_iter_por_epoca=PASOS_PRUEBA, max_imagenes_valid=IMAGENES_PRUEBA)
            print(f'[{ahora()}] preflight {modelo}: lote {lote} x {acum}', flush=True)
            rc = ejecutar(WEEK2 / 'train.ipynb', f'{exp}_train', cfg, log)
            if rc != 0:
                info['error'] = f'train.ipynb terminó con código {rc}'
                if sin_memoria(log):
                    info['error'] += ' (sin memoria)'
                    continue
                break
            h = leer_json(WEEK2 / 'resultados_train' / exp / 'historial.json', {})
            try:
                micro, t_train, t_valid = h['microbatches'][0], h['tiempo_train_s'][0], h['tiempo_valid_s'][0]
            except (KeyError, IndexError):
                info['error'] = 'el historial no tiene tiempos'
                break
            s_img = t_train / (micro * lote)
            s_valid = t_valid / h['imagenes_valid']
            rc = ejecutar(WEEK2 / 'test.ipynb', f'{exp}_test', dict(cfg, conjunto='val', max_imagenes=IMAGENES_PRUEBA), log)
            if rc != 0:
                info['error'] = f'test.ipynb terminó con código {rc}'
                break
            r = resultado_val(exp) or {}
            minutos_epoca = (s_img * IMAGENES['train'] + s_valid * IMAGENES['val']) / 60
            info = {'viable': True, 'batch_size': lote, 'acumulacion_gradiente': acum,
                    's_por_imagen_train': round(s_img, 4), 's_por_imagen_valid': round(s_valid, 4),
                    'min_por_epoca': round(minutos_epoca, 1), 'mem_pico_mib': h.get('mem_pico_mib'),
                    'ms_por_imagen_una_a_una': r.get('ms_por_imagen_una_a_una')}
            break
        plan[modelo] = info
        limpiar(exp)
        escribir_json(CADENA / 'plan.json', plan)
        print(f'[{ahora()}] {modelo}: {info}', flush=True)
    horas = sum(plan[m]['min_por_epoca'] * EPOCAS for m in plan if plan[m].get('viable')) / 60
    print(f'Estimación de la fase 1: {horas:.1f} h de entrenamiento más la evaluación de cada modelo', flush=True)
    return plan


# ------------------------------------------------------------------ experimentos
def guardar_estado(estado: dict) -> None:
    estado['actualizado'] = ahora()
    escribir_json(CADENA / 'estado.json', estado)


def experimento(modelo: str, lr: float, plan: dict, estado: dict, fase: int) -> None:
    exp = nombre(modelo, lr)
    if resultado_val(exp):
        print(f'[{ahora()}] {exp}: ya evaluado, se salta', flush=True)
        return
    elem = estado['experimentos'].setdefault(exp, {'modelo': modelo, 'lr': lr, 'fase': fase})
    elem.update(estado='entrenando', inicio=ahora())
    guardar_estado(estado)
    inicio = time.time()
    lote, acum = plan[modelo]['batch_size'], plan[modelo]['acumulacion_gradiente']
    log = CADENA / 'logs' / f'{exp}.log'
    for intento in range(2):
        cfg = configuracion(modelo, lr, lote, acum)
        print(f'[{ahora()}] {exp}: entrenando ({epocas(lr)} épocas, lote {lote} x {acum})', flush=True)
        rc = ejecutar(WEEK2 / 'train.ipynb', f'{exp}_train', cfg, log)
        if rc == 0:
            break
        if sin_memoria(log) and intento == 0 and acum < 4:
            lote, acum = lote // 2, acum * 2          # se repite desde cero con un lote más pequeño
            borrar_entrenamiento(exp)
            elem['reintento'] = f'sin memoria; lote {lote} x {acum}'
            continue
        elem.update(estado='fallo', error=f'train.ipynb código {rc}', fin=ahora())
        guardar_estado(estado)
        print(f'[{ahora()}] {exp}: FALLÓ el entrenamiento (código {rc})', flush=True)
        return
    elem.update(estado='evaluando', batch_size=lote, acumulacion_gradiente=acum)
    guardar_estado(estado)
    rc = ejecutar(WEEK2 / 'test.ipynb', f'{exp}_test', dict(cfg, conjunto='val'), log)
    resumen = resultado_val(exp)
    if rc != 0 or not resumen:
        elem.update(estado='fallo', error=f'test.ipynb código {rc}', fin=ahora())
    else:
        elem.update(estado='hecho', fin=ahora(), minutos=round((time.time() - inicio) / 60, 1),
                    ap50_todos=ap50(resumen), ap50_difficult=ap50(resumen, 'difficult'))
    guardar_estado(estado)
    escribir_resumen_csv(estado)
    print(f'[{ahora()}] {exp}: {elem["estado"]} {elem.get("ap50_todos", "")}', flush=True)


def escribir_resumen_csv(estado: dict) -> None:
    columnas = ['experimento', 'modelo', 'lr', 'fase', 'epocas', 'lote', 'acumulacion', 'mejor_epoca',
                'ap50_todos', 'ap50_normales', 'ap50_difficult', 'ap_0.5:0.95', 'fp', 'fn', 'fn_difficult',
                'precision', 'exhaustividad', 'ms_una_a_una', 'minutos_train', 'mem_pico_mib']
    filas = []
    for exp, e in estado['experimentos'].items():
        r = resultado_val(exp)
        t = leer_json(WEEK2 / 'resultados_train' / exp / 'resumen.json', {})
        if not r:
            continue
        total = next((f for f in r['por_video'] if f['grupo'] == 'Total'), {})
        todos = next((f for f in r['map'] if f['grupo'] == 'todos'), {})
        filas.append({
            'experimento': exp, 'modelo': e['modelo'], 'lr': e['lr'], 'fase': e['fase'], 'epocas': t.get('num_epochs'),
            'lote': t.get('batch_size'), 'acumulacion': t.get('acumulacion_gradiente'), 'mejor_epoca': t.get('mejor_epoca'),
            'ap50_todos': ap50(r), 'ap50_normales': ap50(r, 'normales'), 'ap50_difficult': ap50(r, 'difficult'),
            'ap_0.5:0.95': todos.get('map'), 'fp': total.get('fp'), 'fn': total.get('fn'),
            'fn_difficult': total.get('fn_difficult'), 'precision': total.get('precision'),
            'exhaustividad': total.get('recall'), 'ms_una_a_una': r.get('ms_por_imagen_una_a_una'),
            'minutos_train': t.get('tiempo_train_min'), 'mem_pico_mib': t.get('mem_pico_mib')})
    with open(CADENA / 'resumen.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)


def cadena() -> None:
    CADENA.mkdir(parents=True, exist_ok=True)
    plan = leer_json(CADENA / 'plan.json') or preflight()
    viables = [m for m in MODELOS if plan.get(m, {}).get('viable')]
    estado = leer_json(CADENA / 'estado.json') or {'inicio': ahora(), 'perfil': PERFIL, 'experimentos': {}}
    estado['no_viables'] = {m: plan[m].get('error') for m in MODELOS if m in plan and not plan[m].get('viable')}
    guardar_estado(estado)
    print(f'[{ahora()}] modelos viables: {viables}; no viables: {estado["no_viables"]}', flush=True)

    for modelo in viables:                                        # fase 1
        experimento(modelo, LR_BASE, plan, estado, fase=1)

    candidatos = {m: r for m in viables if (r := resultado_val(nombre(m, LR_BASE)))}
    mejores = elegir_mejores(candidatos, TOP_FASE2)
    estado['fase2'] = {'elegidos': mejores, 'ap50': {m: ap50(candidatos[m]) for m in mejores}}
    guardar_estado(estado)
    print(f'[{ahora()}] fase 2 con {mejores}', flush=True)
    for modelo in mejores:                                        # fase 2
        for lr in LR_FASE2:
            experimento(modelo, lr, plan, estado, fase=2)

    estado['fin'] = ahora()
    guardar_estado(estado)
    escribir_resumen_csv(estado)
    empaquetar()
    print(f'[{ahora()}] cadena terminada', flush=True)


# ------------------------------------------------------------------ consulta y empaquetado
def estado_actual() -> None:
    estado = leer_json(CADENA / 'estado.json')
    plan = leer_json(CADENA / 'plan.json') or {}
    if plan:
        print('PLAN (preflight):')
        for m, p in plan.items():
            if p.get('viable'):
                print(f"  {m:16s} lote {p['batch_size']}x{p['acumulacion_gradiente']}  {p['min_por_epoca']:5.1f} min/época  "
                      f"{p.get('mem_pico_mib')} MiB  {p.get('ms_por_imagen_una_a_una')} ms/imagen")
            else:
                print(f"  {m:16s} NO VIABLE: {p.get('error')}")
    if not estado:
        print('Aún no hay estado: la cadena no ha empezado.')
        return
    print(f"\nInicio {estado.get('inicio')} · actualizado {estado.get('actualizado')} · fin {estado.get('fin', '—')}")
    if 'fase2' in estado:
        print('Fase 2 con:', estado['fase2']['elegidos'])
    for exp, e in estado['experimentos'].items():
        h = leer_csv(WEEK2 / 'resultados_train' / exp / 'historial.csv')
        prog = f"época {len(h)}/{epocas(e['lr'])}" if h else ''
        mejor = max((float(f['valid_map_50']) for f in h), default=float('nan'))
        extra = f"AP@0,5 val {e['ap50_todos']:.4f} (difficult {e['ap50_difficult']:.4f}) {e.get('minutos')} min" if e.get('ap50_todos') else ''
        print(f"  {exp:48s} {e['estado']:10s} {prog:12s} mejor AP@0,5 {mejor:.4f}  {extra}  {e.get('error', '')}")


def empaquetar() -> Path:
    """Zip con los resultados (CSV, JSON, figuras) y el estado, sin los pesos de los modelos."""
    estado = leer_json(CADENA / 'estado.json') or {'experimentos': {}}
    destino = CADENA / 'resultados_cadena.zip'
    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as z:
        for exp in estado['experimentos']:
            for carpeta in (WEEK2 / 'resultados_train' / exp, WEEK2 / 'resultados_test' / f'{exp}_val'):
                for f in carpeta.rglob('*') if carpeta.is_dir() else []:
                    if f.is_file():
                        z.write(f, f.relative_to(WEEK2).as_posix())
        for f in ('estado.json', 'plan.json', 'resumen.csv'):
            if (CADENA / f).is_file():
                z.write(CADENA / f, f'cadena/{f}')
    print('Zip en', destino, f'({destino.stat().st_size / 1e6:.1f} MB)')
    return destino


if __name__ == '__main__':
    accion = sys.argv[1] if len(sys.argv) > 1 else 'estado'
    {'preflight': preflight, 'cadena': cadena, 'estado': estado_actual, 'empaquetar': empaquetar}[accion]()
