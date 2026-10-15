# Propuestas de mejora del entrenamiento (T19, T20)

Propuesta de Alejandro Cuevas, 15/10/2026, a partir de los resultados en validación de
`faster_rcnn_v1` con y sin aumento (`ENTREGA 1/WEEK2/resultados_train/` y
`resultados_test/`). Para discutir en grupo antes de lanzar nada.

## Valoración de los resultados actuales

**Son buenos.** El modelo se entrena solo con nuestros diez vídeos y se valida con
secuencias de otros grupos, escenarios y cámaras, y aun así llega a un mAP@0,5 de
**0,942**. Generaliza.

- **Robots normales: casi en el techo** (0,966). Ahí queda poco que ganar.
- **Sin sobreajuste:** la pérdida de validación se mantiene estable en torno a 0,235.
- **El aumento funciona donde se pensó:** +8,2 puntos en los `difficult`.

El margen está en tres puntos concretos:

| Punto débil | Dato (modelo con aumento) |
|---|---|
| Robots `difficult` | mAP@0,5 de 0,634; se pierden 63 de 255 (25 %) |
| Robots pequeños | `map_small` de **0,107**, la cifra más baja de todas |
| Detecciones falsas | 210, con precisión de 0,876; el mejor F1 exige confianza 0,95 |

**Límite que no depende del modelo:** entre nosotros mismos el IoU medio es de 0,81
(T01), y las cajas de validación las anotaron otros grupos con otro criterio (antenas,
robots cortados). El mAP 0,50:0,95 y el mAP@0,75 tienen por eso un techo bajo; no
conviene perseguirlos.

## Propuestas, por orden de prioridad

Un experimento cada vez, con su propio `sufijo_experimento`, comparado en validación
igual que hasta ahora.

### 1. Tasa de aprendizaje y programador

- **Problema:** 0,0001 es baja para afinar un Faster R-CNN; el tutorial de torchvision
  usa 0,005 con SGD. Además, `ReduceLROnPlateau` mira la pérdida de validación, que con
  aumento bajaba un poco cada pocas épocas, así que **la tasa nunca llegó a bajar** en
  las 30 épocas.
- **En curso:** el experimento `faster_rcnn_v1_aug_lr001` de Javier (PR #14).
- **Si mejora:** probar una bajada programada en vez de depender de la meseta, por
  ejemplo `MultiStepLR` con ×0,1 en las épocas 20 y 26.

### 2. Resolución de entrada (la que más puede ayudar a pequeños y `difficult`)

- **Problema:** Faster R-CNN escala la imagen con `min_size=800` y `max_size=1333`
  por defecto. Un fotograma de 1280×720 se queda en unos 1333×750: apenas crece, y un
  robot de 25 px sigue midiendo unos 26 px. Eso explica en parte el `map_small` de
  0,107.
- **Cambio:** pasar `min_size=1024, max_size=1820` al crear el modelo en
  `torchvision_model` (los constructores de `torchvision.models.detection` los
  aceptan como argumentos). Escala la imagen ×1,42.
- **Coste:** cada época tarda más (ahora ~11 min con aumento) y la inferencia también
  (ahora ~73 ms por imagen). Medirlo, porque importa para la demo en el robot.

### 3. Revisar los falsos positivos antes de corregirlos

- `PIDS2024_GR02_0001` acumula 50 con solo 135 robots, y cuatro secuencias suman 152
  de los 210.
- **Mirar `ejemplos_peores.jpg`:**
  - si son **robots que el otro grupo no anotó**, no es un fallo del modelo; se explica
    en la memoria y no se toca nada;
  - si son **cajas dobles, reflejos u otros objetos**, sí hay que actuar (por ejemplo,
    más negativas en el entrenamiento o un NMS más estricto).
- Es barato y da material para la memoria.

### 4. Cambiar a `faster_rcnn_v2`

- Ya está en el diccionario de `train.ipynb`: es cambiar `model_name`.
- Mejores pesos de COCO: 46,7 de mAP frente a 37,0 de `faster_rcnn_v1`.
- **Coste:** más lento. Comparar el tiempo por imagen con el de la *demo* en mente.

### 5. Aumento más agresivo para los `difficult`

Los `difficult` de validación se marcaron por estar **muy movidos, tapados o cortados
más de la mitad, o muy oscuros** (`DATOS_ASIGNATURA/README.md`). Propuesta en
`data_aug.ipynb`:

- más desenfoque de movimiento;
- más oclusión sintética;
- algunas copias muy oscuras.

## Lo que no haría

- **Más épocas:** con aumento, el mAP@0,5 pasa de 0,937 en la época 10 a 0,942 en la
  29. La curva está plana.
- **Muchos experimentos sobre validación:** cada uno que se elige mirándola la va
  desgastando. Mejor dos o tres bien elegidos.
- **Mirar test más de una vez:** solo al final, con el modelo definitivo.
- **Tocar los *anchors*:** el EDA no muestra formas de caja raras.

## Propuesta de plan

1. Esperar al resultado de `lr001` y decidir la tasa.
2. Con esa tasa, un experimento de resolución (`sufijo_experimento = 'res1024'`).
3. En paralelo, revisar a ojo los falsos positivos de las cuatro secuencias.
4. Si queda tiempo de laboratorio, `faster_rcnn_v2` o el aumento para los `difficult`.
5. Con el modelo definitivo, evaluar en test una sola vez y fijar el umbral de la
   *demo* (en torno a 0,9–0,95).
