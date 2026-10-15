# Experimento de resolución 1024

Propuesta de Alejandro, autorizada por Javier tras cerrar el análisis de lr001.
Arrancado el **15/10/2026 a las 23:44 Europe/Madrid**, después de subir los informes.

| Parámetro | Valor |
|---|---|
| Experimento | `faster_rcnn_v1_aug_lr001_res1024` |
| Inicialización | COCO, entrenamiento nuevo; no continúa desde lr001 |
| Modelo | Faster R-CNN ResNet-50 FPN |
| Resolución interna | `min_size=1024`, `max_size=1820`, tanto al entrenar como al evaluar |
| Datos | Los mismos 3184 de entrenamiento con aumento base; 672 de validación |
| Tasa / épocas / semilla | 0,001 / 30 / 0 |
| Memoria | Microbatch 4, acumulación 2, lote efectivo 8 |
| Optimizador y scheduler | SGD y ReduceLROnPlateau, como lr001 |
| Criterio del mejor | Mayor AP@0,5 de validación |
| Código de arranque | Commit `dc8dc20` |
| PID inicial | `10327` |

La acumulación pondera por el número de imágenes del microbatch y trata la cola
incompleta. Dos pruebas verifican el resultado de las actualizaciones en un modelo
cuadrático sencillo. No implica identidad numérica con un forward de ocho imágenes:
pueden cambiar el muestreo de propuestas y los redondeos. Esta adaptación de memoria
se debe mencionar al comparar con lr001, cuyo lote físico era ocho.

## Comprobación y arranque

`herramientas/comprobar_res1024.py` ejecutó dos microbatches con gradientes, un paso
del optimizador en memoria y una inferencia. No guardó pesos ni un checkpoint.
Resultado `ok`: 8482 MiB máximos reservados frente a 11906,1 MiB utilizables por
PyTorch. Comprobó el tamaño interno real del modelo.

Tras lanzar la cadena se verificó el PID activo, sin archivo de salida, GPU al
100 % y 9693 MiB usados de 12288 MiB físicos, incluida la memoria ajena al proceso.
El notebook registró su configuración en la carpeta propia del nuevo experimento.
Estos son datos de arranque, no resultados de precisión ni de una época completa.

Se ejecutan en segundo plano `train_res1024.ipynb` y después
`test_val_res1024.ipynb`. Esta última comprueba que la resolución del checkpoint
coincide con la del constructor. La resolución no se recupera de `state_dict`.

No se incluyen los perfiles nuevos de lluvia, sombras, oclusión texturada o refuerzo
difficult; tampoco MultiStepLR ni otra arquitectura. Se estudia resolución con la
adaptación necesaria del microbatch. Se mantienen los conjuntos y se reserva test.

## Seguimiento en el laboratorio

En `~/PIDS-Proyecto2/ENTREGA 1/WEEK2`:

```bash
cat train_res1024.pid
cat train_res1024.exit
tail -n 5 resultados_train/faster_rcnn_v1_aug_lr001_res1024/historial.csv
```

`train_res1024.exit` solo aparece cuando termina la cadena; 0 indica éxito.
El log de nbconvert no muestra las épocas en tiempo real: quedan en `historial.csv`.
Mientras no termine la primera época aún no habrá historial. Los notebooks ejecutados
se conservan en el laboratorio y los pesos permanecen ignorados en Git.

Al terminar se comparará con el mejor lr001: AP50 0,9433, AP 0,50:0,95 0,6302,
AP50 difficult 0,6462, AP small 0,1182, FP 190 y FN 83, junto con curvas, secuencias,
latencia y memoria. El seguimiento horario avisa solo de finalización, fallo o
intervención necesaria.
