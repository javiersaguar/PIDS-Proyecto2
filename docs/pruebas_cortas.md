# Pruebas cortas: orden de los experimentos, lote y tasa de aprendizaje (01/11/2026)

El enunciado del Bloque 2 pide tres cosas que la cadena de entrenamientos no había medido:
comparar las arquitecturas **sin aumento** (y añadirlo al final), probar **lotes muy bajos y muy
altos** y probar una tasa de aprendizaje **muy alta**. Se hicieron como pruebas breves en el
JupyterHub (RTX 3060, 12 GB) con `herramientas/pruebas_cortas.py`.

```bash
python herramientas/pruebas_cortas.py lanzar    # ejecuta lo que falte, una prueba tras otra
python herramientas/pruebas_cortas.py estado    # tabla con lo hecho
```

Todo se evalúa en **validación** (672 imágenes); el test no se toca. Se entrena solo con las 796
imágenes originales (`usar_aumento = False`, 100 actualizaciones por época con lote 8), semilla 0 y
SGD con momentum 0,9 y weight decay 0,0005. Cada resultado sale de **una sola ejecución**.
Los historiales por época se quedaron en el laboratorio (`resultados_train/<modelo>_sin_aug_corto*`,
no versionados); las cifras de abajo son las que recoge el Anexo D de la memoria.

## Arquitecturas sin aumento (lr 0,001, 6 épocas)

| Modelo | Mejor época | AP@0,5 sin aumento | AP 0,50:0,95 | AP@0,5 con aumento (12 épocas) | Min de entrenamiento |
|---|---:|---:|---:|---:|---:|
| Faster R-CNN v2 | 6 | 0,9382 | 0,6118 | 0,9513 | 18,8 |
| Faster R-CNN v1 | 5 | 0,9347 | 0,5813 | 0,9426 | 13,2 |
| RetinaNet v2 | 6 | 0,9188 | 0,5814 | 0,9447 | 12,6 |
| Faster R-CNN MobileNet | 5 | 0,9174 | 0,5768 | 0,9281 | 2,5 |
| RetinaNet v1 | 6 | 0,8828 | 0,5727 | 0,9396 | 12,2 |
| SSD300 VGG16 | 6 | 0,7754 | 0,4667 | 0,9008 | 2,3 |
| SSDlite320 | 3 | 0,5975 | 0,3268 | 0,6823 | 0,8 |

Faster R-CNN v2 sigue siendo el mejor y SSD300 y SSDlite320 los peores. RetinaNet y SSD300 mejoran
hasta la última época y con ocho veces menos actualizaciones que los entrenamientos con aumento (600
frente a 4776): su posición no es comparable con la de la tabla con aumento. Esta comparación no aísla
el efecto del aumento.

## Lote (Faster R-CNN v1, lr 0,001, 3 épocas)

| Lote | Pasos por época | AP@0,5 en las épocas 1 / 2 / 3 | Mejor (época) | AP 0,50:0,95 | Memoria pico | Min |
|---:|---:|---|---|---:|---:|---:|
| 1 | 796 | 0,9329 / 0,9332 / 0,9280 | 0,9332 (2) | 0,6084 | 1,3 GiB | 7,2 |
| 2 | 398 | 0,9341 / 0,9358 / 0,9285 | 0,9358 (2) | 0,5851 | 2,3 GiB | 6,7 |
| 8 | 100 | 0,9128 / 0,9287 / 0,9326 | 0,9326 (3) | 0,5886 | 8,0 GiB | 6,6 |
| 16 | — | CUDA out of memory | — | — | — | — |
| 32 | — | CUDA out of memory | — | — | — | — |

El lote 8 son las tres primeras épocas de la prueba de seis. Con 16 y 32 la GPU (11,6 GiB útiles) se
queda sin memoria: al fallar tenía asignados 10,48 y 9,47 GiB y pedía 1008 MiB más.

## Tasa de aprendizaje (Faster R-CNN v1, lote 8, 3 épocas)

| Tasa | AP@0,5 en las épocas 1 / 2 / 3 | Mejor (época) | Pérdida de entrenamiento (época 3) | Resultado |
|---|---|---|---:|---|
| 1e−5 | 0,0034 / 0,0089 / 0,0261 | 0,0261 (3) | 0,461 | Aprende demasiado despacio |
| 0,001 | 0,9128 / 0,9287 / 0,9326 | 0,9326 (3) | 0,145 | Referencia |
| 0,01 | 0,9337 / 0,9353 / 0,9308 | 0,9353 (2) | 0,107 | Llega antes al máximo y baja después |
| 0,1 | 0,0000 / 0,0000 / 0,0000 | 0,0000 (1) | NaN | Diverge desde la primera época |
