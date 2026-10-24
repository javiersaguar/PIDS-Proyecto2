# Cadena de entrenamientos (21/10/2026)

Compara los siete detectores del script original de la asignatura, con los datos del perfil
de aumento `robusto_v1` y variando la tasa de aprendizaje (lr). Se lanza una vez en el
JupyterHub y los experimentos se ejecutan uno tras otro, sin intervención.

Todo se evalúa en **validación**; el test no se toca hasta elegir el modelo definitivo.

## Qué se entrena

| Fase | Modelos | lr | Épocas |
|---|---|---|---|
| 1 | `ssd_v2`, `ssd_v1`, `faster_rcnn_v3`, `faster_rcnn_v1`, `retinanet_v1`, `faster_rcnn_v2`, `retinanet_v2` | 0,001 | 12 |
| 2 | Los 3 mejores de la fase 1 por AP@0,5 en validación | 0,0005 y 0,002 | 15 con 0,0005; 12 con 0,002 |

- **Datos:** `datasets_experimentos/robusto_v1/`. Los 796 originales depurados y 2.388 copias
  aumentadas con las cuatro ampliaciones juntas (sombras, oclusión con textura, refuerzo de
  `difficult` y lluvia); ver [`experimentos/README.md`](../ENTREGA%201/WEEK1/resultados_aug/experimentos/README.md).
  Validación (672 imágenes) y test (718) son los conjuntos de la asignatura, sin aumentar.
- **Épocas:** 12 porque en los entrenamientos anteriores el mejor AP@0,5 cae entre la época
  2 y la 29, y con lr 0,001 sobreajusta a partir de la 5. Con 0,0005 hace falta algo más.
- **Orden:** de menor a mayor coste, para que los resultados lleguen antes y un fallo se
  vea pronto.
- **Elección del mejor:** mayor AP@0,5 en validación con todos los robots; a igualdad,
  mejor AP@0,5 en `difficult`.
- **Comparación limpia:** `faster_rcnn_v1` con lr 0,001 repite el experimento
  `faster_rcnn_v1_aug_lr001` cambiando solo el aumento de base a `robusto_v1`.
- **Lote:** el efectivo es siempre 8. Si un modelo no cabe en la GPU con lote 8, el
  `preflight` lo parte en microlotes con acumulación de gradientes (4×2 o 2×4).

## Cómo se ejecuta

En `~/pids_main` (copia limpia de este repositorio en el laboratorio):

```bash
cd ~/pids_main
python herramientas/cadena_entrenamientos.py preflight                  # ~45 min: prueba cada modelo en pequeño
nohup python herramientas/cadena_entrenamientos.py cadena > "ENTREGA 1/WEEK2/cadena/cadena.log" 2>&1 &
python herramientas/cadena_entrenamientos.py estado                     # progreso, cuando quieras
python herramientas/cadena_entrenamientos.py empaquetar                 # zip de resultados, sin pesos
```

- **`preflight`:** genera los datos del perfil si faltan (~15 min), y con cada modelo entrena
  20 pasos y evalúa 48 imágenes. Comprueba que entrena, evalúa y cabe en memoria, elige el
  lote y estima el tiempo por época. Lo guarda en `cadena/plan.json`.
- **`cadena`:** ejecuta la fase 1, elige los mejores y ejecuta la fase 2. Si un experimento
  falla, sigue con el siguiente. Si se queda sin memoria, lo repite una vez con un lote más
  pequeño.
- **Se puede relanzar:** salta lo que ya tiene su evaluación y reanuda el entrenamiento que
  quedó a medias desde `model_last.pt`.

### Opciones

```bash
python herramientas/cadena_entrenamientos.py cadena --modelos retinanet_v2,faster_rcnn_v2   # solo esos, en ese orden
python herramientas/cadena_entrenamientos.py cadena --sin-fase2                             # no varía el lr
python herramientas/cadena_entrenamientos.py cadena --simular                               # muestra el plan sin ejecutar nada
```

### En un ordenador local con GPU (Windows)

Se hizo el 21/10/2026 como copia de seguridad cuando el laboratorio dejó de responder.

1. Clonar la rama en una carpeta nueva, para no mezclar los resultados con el repositorio de trabajo.
2. Crear un entorno que reutilice `torch`: `python -m venv --system-site-packages .venv-cadena`, e instalar
   `albumentations==1.4.18 albucore==0.0.17 torchmetrics==1.9.0 pycocotools==2.0.11`.
3. Registrar su kernel: `.venv-cadena\Scripts\python.exe -m ipykernel install --sys-prefix --name pids-cadena`.
   Con `PIDS_KERNEL=pids-cadena` la cadena ejecuta los notebooks con ese kernel.
4. Lanzar con `cadena_entrenamientos.py cadena`. El `preflight` se hace solo al empezar y elige
   el lote según la memoria de **esa** GPU (con 8 GB, `faster_rcnn_v1` y `retinanet_v2` no caben con lote 8).

El script impide que Windows se suspenda mientras corre, pero no si se cierra la tapa del portátil.
Usa `python -m nbconvert` y no `jupyter nbconvert`, porque el control de aplicaciones de Windows
bloquea el ejecutable `jupyter.exe` de un entorno nuevo.

Si se ejecuta la misma cadena en dos máquinas, los modelos se repiten: conviene repartirlos con `--modelos`.
Las versiones de `torch` y `torchvision` también difieren (laboratorio: 2.4.1 y 0.19.1), así que los
resultados de las dos máquinas se pueden comparar, pero no son bit a bit iguales.

## Qué deja

| Dónde | Qué |
|---|---|
| `ENTREGA 1/WEEK2/resultados_train/<experimento>/` | `historial.csv` y `.json` (con tiempos y memoria), `resumen.json`, curvas |
| `ENTREGA 1/WEEK2/resultados_test/<experimento>_val/` | `map.csv`, `errores_por_video.csv`, `umbral_confianza.csv`, figuras |
| `ENTREGA 1/WEEK2/cadena/resumen.csv` | Una fila por experimento: AP@0,5 por grupo, errores, tiempo por imagen y de entrenamiento |
| `ENTREGA 1/WEEK2/cadena/estado.json` y `plan.json` | Estado de cada experimento y plan del `preflight` |
| `ENTREGA 1/WEEK2/cadena/logs/` y `ejecutados/` | Un log y un notebook ejecutado por experimento |
| `models/<experimento>/` | Pesos (`model_best.pt`, `model_last.pt`); no se versionan |

El nombre de cada experimento es `<modelo>_aug_robusto_v1_lr<tasa>`, por ejemplo
`retinanet_v1_aug_robusto_v1_lr001`.

## Cómo está hecho

- `train.ipynb` y `test.ipynb` leen la variable de entorno `PIDS_CONFIG` (JSON) con el modelo,
  el lr, las épocas, el lote, el perfil y el sufijo. **Sin esa variable valen los de siempre**,
  así que siguen funcionando a mano.
- `herramientas/entrenamiento.py` ya daba la acumulación de gradientes; `train.ipynb` la usa
  ahora para todos los modelos y mide el tiempo de entrenamiento y de validación por época.
- Con `PIDS_CONFIG`, el entrenamiento **se detiene si no hay GPU** en vez de seguir en CPU.
- `data_aug.ipynb` no se modifica: la cadena ejecuta una copia temporal con `PERFIL_AUMENTO`
  cambiado.
- Pruebas de las partes que no usan la GPU: `python -m unittest herramientas/tests/test_cadena_entrenamientos.py`.

## Cosas a tener en cuenta al interpretar los resultados

- **`ssd_v1` y `ssd_v2` reducen la imagen a 300×300 y 320×320** (así los define torchvision),
  por lo que los robots lejanos quedan muy pequeños. Son modelos rápidos y es esperable que
  pierdan precisión en los `difficult`.
- **Las cabezas de clasificación se sustituyen** por otras nuevas (código original de la
  asignatura), también en RetinaNet y SSD, que las reinicializa por completo.
- **La validación ya no actualiza las estadísticas de BatchNorm.** Solo afecta a `ssd_v2` y
  `faster_rcnn_v2`, los únicos con BatchNorm entrenable (en el resto está congelado o no hay).
  Antes, la pasada de pérdida de validación las actualizaba con las imágenes de validación.
- **`ssd_v2` con pesos de COCO tiene una arquitectura distinta de la que torchvision crea sin
  ellos** (cola de MobileNetV3 reducida: 480 canales en vez de 960). Para cargar un modelo
  entrenado, `torchvision_model` fuerza `weights_backbone=None` en ese caso. Lo descubrió el
  `preflight`.
- **Una sola semilla** (0). Diferencias de menos de 0,5 puntos de AP@0,5 no son concluyentes.
- **Las etiquetas de otros grupos** pueden no seguir nuestros criterios (antenas, robots
  cortados), y algunas tienen robots sin anotar: parte de los falsos positivos puede ser eso.
