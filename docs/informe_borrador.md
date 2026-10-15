# Borrador de la memoria

> **Borrador de trabajo.** Recoge el contenido de la memoria con las cifras reales del
> repositorio, para pasarlo a la plantilla oficial cuando la tengamos. Lo marcado como
> **[PENDIENTE]** falta por hacer o por confirmar.
>
> La primera entrega pide la portada y el **Bloque 1 completo**, con un máximo de 10
> páginas de cuerpo. Las secciones 7 y 8 (Bloque 2) se dejan preparadas para la
> segunda entrega y se pueden recortar o resumir en esta.

**Portada:** PIDS 2026 · Grupo **2** (por el usuario `pids2` de JupyterHub; **[PENDIENTE: confirmar]**) · Javier Saguar, Alejandro
Cuevas, Mónica Fernández, Pedro José Orrego y Daniel Naval · Primera entrega · Fichero
`PIDS_grupo2_entrega1.pdf`.

---

## 1. Introducción

El objetivo del proyecto es que un RoboMaster EP detecte robots rivales con una red
neuronal y actúe en consecuencia: apuntar el gimbal y disparar. Se divide en tres
bloques: datos (Bloque 1), entrenamiento del detector (Bloque 2) e integración en el
robot (Bloque 3).

Esta entrega cubre el Bloque 1: cómo se han grabado, anotado, analizado, depurado y
aumentado los datos. Las decisiones se han tomado pensando en lo que verá el robot en
la demo: robots en movimiento, a distintas distancias y detrás de obstáculos.

## 2. Recolección de datos

Se grabaron **10 vídeos** con la cámara del propio robot, en modo *Solo*, en seis
escenarios distintos.

| Vídeo | Escenario | Duración (s) | Fotogramas |
|---|---|---:|---:|
| V01 | Vestíbulo, suelo de granito pulido | 65,4 | 1982 |
| V02 | Aula con sillas | 59,9 | 1815 |
| V03 | Aula de paredes blancas | 60,2 | 1823 |
| V04 | Exterior | 66,1 | 2003 |
| V05 | Pasillo largo | 59,6 | 1807 |
| V06 | Vestíbulo, suelo de color | 74,1 | 2244 |
| V07 | Vestíbulo, suelo de granito pulido | 61,2 | 1855 |
| V08 | Vestíbulo, suelo de color | 81,2 | 2460 |
| V09 | Exterior | 56,2 | 1704 |
| V10 | Aula con sillas | 59,9 | 1815 |
| **Total** | | **643,8 (10 min 44 s)** | **19 508** |

Todos los vídeos son de 1280×720 a 30 fps.

**Variabilidad cubierta** (`docs/fichas_videos.md`):
- interior y exterior;
- luz natural, artificial y mixta, con contraluces y reflejos;
- oclusiones por sillas, piernas y otros robots;
- de 1 a 3 robots a la vez, desde muy lejanos hasta en primer plano;
- cámara en movimiento, con desenfoque y giros.

**Limitaciones:**
- Los dos exteriores son del mismo sitio.
- No hay secuencias del circuito real con obstáculos fijos ni con muy poca luz.

**Extracción de fotogramas:** un fotograma de cada 24 (`INTERVAL = 24`, unos 0,8 s),
para no guardar imágenes casi iguales y llegar a las ~800 que pide el enunciado. Salen
**808 imágenes**.

## 3. Anotación

**Herramienta y formato:** labelImg, formato PascalVOC, una sola clase (`robot`).

### 3.1 Criterios

Antes de anotar se acordaron los criterios, justificados en
`docs/criterios_anotacion.md`. Los principales:

| Regla | Criterio | Por qué |
|---|---|---|
| Qué se anota | Cualquier RoboMaster rival | Una sola clase, como pide el enunciado |
| Qué no | El cañón propio, los reflejos en el suelo y los robots en pantallas | El cañón aparece en todas las imágenes: anotarlo enseñaría a detectarse a sí mismo |
| Ajuste de la caja | Chasis, ruedas, gimbal y cañón, **sin antenas** | Las antenas solo se ven de cerca: con ellas el tamaño de la caja dependería de la distancia y su centro se desplazaría hacia arriba |
| Tapados y cortados | Se anotan si se reconocen y se ve al menos un 30 %. La caja cubre solo lo visible | El mismo 30 % que usa el aumento de datos (`min_visibility`) |
| `difficult` | Menos de 30 px de ancho, menos de la mitad visible o muy movido | Permite medir el modelo por separado en los casos difíciles |
| Imágenes sin robots | Se guardan con su `.xml` vacío | Si no tienen `.xml`, el entrenamiento las ignora y se pierden como ejemplos negativos |
| Duda | «¿Si viera solo este fotograma, diría que hay un robot?» | La red ve las imágenes de una en una, sin el vídeo |

### 3.2 Consistencia entre anotadores

- **Calibración:** los cinco anotamos por separado las mismas 20 imágenes, elegidas
  por ser difíciles. El IoU medio entre parejas fue de **0,81**.
- **Dónde discrepamos más:** en el **borde superior** (7 px de mediana, frente a 4–5 px
  en los demás bordes), es decir, en el gimbal y las antenas.
- **Revisión cruzada:** cada lote lo revisó otra persona. Se ajustaron cajas, se
  añadieron robots sin caja y se marcaron los `difficult` con el mismo criterio
  (detalle en las PR #3, #7 y #8).

Figura: `resultados_eda/acuerdo_anotadores.png`.

**[PENDIENTE]** Comentar la ronda de discusión del grupo sobre el borde superior (T01).

## 4. Análisis exploratorio de datos (EDA)

Notebook: `eda.ipynb`. Figuras y tablas en `resultados_eda/`.

### 4.1 Inventario

**808 imágenes y 1420 robots**: 1,76 robots por imagen, un 26 % `difficult` y 41
imágenes sin robots (5 %).

| Vídeo | Imágenes | Robots | `difficult` | Sin robots |
|---|---:|---:|---:|---:|
| V01 | 82 | 151 | 43 | 2 |
| V02 | 75 | 129 | 43 | 7 |
| V03 | 75 | 149 | 45 | 5 |
| V04 | 83 | 121 | 17 | 1 |
| V05 | 75 | 170 | 18 | 1 |
| V06 | 93 | 117 | 40 | 22 |
| V07 | 77 | 139 | 39 | 0 |
| V08 | 102 | 196 | 65 | 0 |
| V09 | 71 | 116 | 18 | 0 |
| V10 | 75 | 132 | 47 | 3 |

Figuras: `ejemplos_secuencias.jpg` e `imagenes_y_cajas_por_secuencia.png`.

### 4.2 Análisis y lo que se decidió con cada uno

| Análisis | Qué se vio | Decisión |
|---|---|---|
| Tamaño de las cajas | Ninguna caja de menos de 30 px de ancho | Las anclas por defecto de Faster R-CNN sirven; se aumenta con alejamiento para tener robots más pequeños |
| Forma y anclas | Cajas casi cuadradas (aspecto mediano 1,11); las anclas cubren el 99,6 % con IoU ≥ 0,5 | Se mantienen las anclas. El aumento **no puede deformar** los robots |
| Posición de los centros | Franja horizontal a media altura y simétrica | Volteo horizontal sí, vertical no |
| Solapamiento entre robots | Ninguna pareja solapa más de 0,26 | El NMS por defecto (0,5) no borra robots reales |
| Color e iluminación | Los exteriores tienen un tono azulado | Cambios de color suaves en el aumento |
| Parecido entre imágenes | La imagen más parecida a cada una es de su mismo vídeo en el 74 % de los casos | No mezclar fotogramas de un mismo vídeo entre entrenamiento y evaluación |
| Nitidez | 52 imágenes poco nítidas | Revisarlas en la depuración |
| Casi duplicadas | 11 imágenes casi iguales a la anterior | Revisarlas en la depuración |

Figuras: `mapa_calor_centros.png`, `forma_cajas.png` y `linea_temporal.png`.

## 5. Depuración del dataset

Criterios en `docs/depuracion.md`. Se revisaron **a ojo, con sus cajas, 69 imágenes**:
las 52 poco nítidas, las 11 casi duplicadas y 6 casos dudosos de la anotación.

| Criterio | Decisión | Imágenes |
|---|---|---:|
| D1 · Robot visible que no se puede anotar (solo una estela) y sin caja | Se excluye: es una etiqueta contradictoria | 1 |
| D2 · Casi duplicada de la anterior, con los robots parados | Se excluye y se conserva la primera del tramo | 11 |
| D3 · Movida, con sus robots anotados como `difficult` | Se conserva: el robot se moverá en la demo | 41 |
| D4 · Sin robots: suelo, piernas, nuestro propio robot | Se conserva: son negativos difíciles | — |
| D5 · Robot cortado con menos del 30 % visible y sin caja | Se conserva: sigue la regla de anotación | 2 |

**Quedan 796 imágenes.** No se borra ningún original: la exclusión se aplica al
generar los conjuntos (`docs/depuracion_excluir.csv`). Quedan cuatro por debajo de las
~800 del objetivo, porque se ha preferido un dataset sin etiquetas contradictorias.

## 6. Aumento de datos

Notebook: `data_aug.ipynb`. Figuras y tablas en `resultados_aug/`.

### 6.1 Reparto de los conjuntos

La asignatura proporcionó conjuntos de **validación (672 imágenes) y test (718)**
anotados por grupos de otros años. Por eso:

- **se entrena con nuestros diez vídeos** (796 imágenes);
- **se valida y se mide con los conjuntos de la asignatura**.

Así no puede haber fuga entre conjuntos y se mide en escenas que el modelo no ha
visto. Esas imágenes no traían ningún `difficult`: se marcaron 525 con nuestro
criterio, sin tocar sus cajas (`DATOS_ASIGNATURA/README.md`).

### 6.2 Transformaciones

Cada transformación se analizó por separado (`catalogo_transformaciones.jpg`).

| Se usan | Se descartan |
|---|---|
| Volteo horizontal | Volteo vertical y giros de 90° (el suelo nunca está arriba) |
| Escala de 0,6 a 1,25 sin deformar, desplazamiento y giro de ±6° | Recorte 640×480 con redimensión del notebook original (ensancha los robots un 33 %) |
| Brillo, contraste y gamma | Desenfoque uniforme (no se parece al de movimiento real) |
| Tono, saturación y desplazamiento RGB suaves | Intercambio de canales (colores imposibles) |
| Desenfoque de movimiento | Perspectiva (en albumentations 1.4.18 desplaza mal las cajas; detectado con una prueba automática) |
| Compresión JPEG, ruido y menor resolución | Relleno por reflejo al girar (duplica robots sin caja) |
| **Oclusión sintética propia:** barras como patas de silla que no tapan más del 35 % de un robot | |

### 6.3 Resultado

**Tres copias por imagen: 3184 imágenes y 5566 robots para entrenar.**

| | Imágenes | Robots | Robots perdidos | Aspecto mediano |
|---|---:|---:|---:|---:|
| Entrenamiento original | 796 | 1399 | — | 1,11 |
| Copias aumentadas | 2388 | 4167 | 0,7 % | 1,10 |
| Aumentador del notebook original (simulado) | 2388 | 3606 | 14,1 % | 1,18 |

El aumento propuesto conserva la forma, la posición y la proporción de `difficult`, y
añade robots más pequeños. El del notebook original habría perdido el 14 % de los
robots y los habría deformado.

**Efecto medido:** entrenando el mismo modelo con y sin estas copias, el aumento sube
el mAP@0,5 en validación de 0,923 a 0,942, y en los robots `difficult` de 0,552 a
0,634 (sección 8.2).

Figuras: `cajas_antes_despues.png` y `ejemplos_aumento.jpg`.

---

## 7. Entrenamiento (Bloque 2, avance)

Faster R-CNN ResNet-50 FPN (`faster_rcnn_v1`), preentrenado en COCO, 30 épocas, lote
de 8, tasa de aprendizaje inicial 0,0001 y semilla 0. El mejor modelo se elige por
mAP@0,5 en validación. Se entrenó en la RTX 3060 del laboratorio con dos experimentos
que solo cambian los datos de entrenamiento:

| Experimento | Imágenes de entrenamiento | Tiempo por época | mAP@0,5 en la época 1 | Mejor época | Mejor mAP@0,5 | mAP 0,50:0,95 en esa época |
|---|---:|---:|---:|---:|---:|---:|
| Sin aumento | 796 | ~4 min | 0,544 | 20 | 0,923 | 0,581 |
| **Con aumento** | 3184 | ~11 min | 0,866 | 29 | **0,942** | **0,607** |

- **Con aumento aprende antes y llega más alto.** En la época 2 ya está en 0,918, casi
  lo mismo que el mejor resultado sin aumento.
- **Sin aumento se estanca** desde la época 16, en torno a 0,92. El programador de la
  tasa de aprendizaje la bajó a 0,00001 en la época 24 y no mejoró.
- **Con aumento siguió mejorando poco a poco** hasta la época 29, y la tasa de
  aprendizaje no llegó a bajar. Por la curva, más épocas darían como mucho unas
  décimas.
- **No hay sobreajuste** en ninguno de los dos. La pérdida de validación se mantiene
  estable (0,243 sin aumento, 0,235 con aumento) mientras la de entrenamiento sigue
  bajando.

Figuras: `resultados_train/faster_rcnn_v1_aug/historial.png` y
`resultados_train/faster_rcnn_v1_sin_aug/historial.png` **[PENDIENTE: bajarlas del
laboratorio; en el repositorio solo están los `historial.csv`]**.

## 8. Evaluación (Bloque 2, avance)

Se evalúa en **validación** el mejor modelo de cada experimento con `test.ipynb`. Hay
tres grupos de robots:
- **todos**;
- **solo los normales**: los `difficult` se ignoran, ni cuentan como perdidos ni
  penalizan si se detectan;
- **solo los `difficult`**: se ignoran los normales.

El test se reserva para el modelo definitivo y se usa **una sola vez**.

### 8.1 Por grupos (modelo con aumento)

| Robots | Cuántos | mAP@0,5 | mAP@0,75 | mAP 0,50:0,95 | Exhaustividad (AR@100) |
|---|---:|---:|---:|---:|---:|
| Todos | 1561 | 0,942 | 0,715 | 0,608 | 0,68 |
| Normales | 1306 | **0,966** | 0,763 | 0,641 | 0,72 |
| `difficult` | 255 | **0,634** | 0,359 | 0,344 | 0,49 |

- **Con los robots claros el detector funciona muy bien.**
- **El punto débil son los `difficult`** (movidos, lejanos, tapados o cortados): 33
  puntos menos de mAP@0,5.
- El mAP 0,50:0,95 es bastante más bajo que el mAP@0,5: el modelo encuentra los robots,
  pero las cajas no se ajustan tanto. En parte es esperable, porque las cajas de
  validación las anotaron otros grupos con otro criterio, por ejemplo para las antenas.

### 8.2 Con aumento frente a sin aumento

**mAP@0,5 por grupo:**

| Robots | Sin aumento | Con aumento | Diferencia |
|---|---:|---:|---:|
| Todos | 0,923 | 0,942 | +1,9 |
| Normales | 0,960 | 0,966 | +0,6 |
| `difficult` | 0,552 | **0,634** | **+8,2** |
| Todos, mAP@0,75 | 0,658 | 0,715 | +5,7 |
| Todos, mAP 0,50:0,95 | 0,581 | 0,608 | +2,7 |

**Recuento con confianza ≥ 0,5 e IoU ≥ 0,5:**

| | Sin aumento | Con aumento |
|---|---:|---:|
| Robots detectados (TP) | 1446 | 1478 |
| Robots perdidos (FN) | 115 | **83** |
| — normales perdidos | 33 | 20 |
| — `difficult` perdidos | 82 | 63 |
| Detecciones falsas (FP) | 221 | 210 |
| Precisión | 0,867 | 0,876 |
| Exhaustividad | 0,926 | 0,947 |
| Exhaustividad en `difficult` | 0,678 | **0,753** |
| F1 | 0,896 | 0,910 |

**Conclusión:** el aumento ayuda sobre todo donde pensábamos al diseñarlo.
- Apenas cambia los robots claros.
- Sube 8 puntos en los `difficult`, que son los robots movidos, pequeños y tapados que
  imitan el desenfoque de movimiento, la escala y la oclusión sintética.
- Pierde un 28 % menos de robots (83 frente a 115).
- Ajusta mejor las cajas (+5,7 en mAP@0,75).
- No añade detecciones falsas.

**Se toma como modelo base el entrenado con aumento.**

### 8.3 Por secuencia

| Secuencia | Imágenes | Robots (`difficult`) | mAP@0,5 sin aum. | mAP@0,5 con aum. | Perdidos con aum. (`difficult`) | FP con aum. |
|---|---:|---:|---:|---:|---:|---:|
| PIDS2023_GR04_0008 | 125 | 240 (7) | 0,984 | 0,988 | 2 (2) | 14 |
| PIDS2024_GR02_0001 | 72 | 135 (7) | 0,929 | 0,939 | 1 (0) | **50** |
| PIDS2024_GR02_0007 | 35 | 106 (9) | 0,988 | 0,988 | 1 (0) | 8 |
| PIDS2024_GR02_0008 | 28 | 48 (3) | 0,987 | 0,986 | 0 | 14 |
| PIDS2024_GR04_0002 | 14 | 25 (3) | 0,974 | 0,982 | 0 | 2 |
| PIDS2024_GR04_0003 | 10 | 25 (6) | 0,762 | **0,813** | 6 (6) | 5 |
| PIDS2025_GR01_0002 | 76 | 170 (14) | 0,957 | 0,972 | 2 (0) | 39 |
| PIDS2025_GR01_0010 | 45 | 81 (13) | 0,862 | 0,905 | 4 (3) | 28 |
| PIDS2025_GR03_0007 | 87 | 217 (49) | 0,941 | 0,966 | 8 (7) | 8 |
| PIDS2025_GR03_0011 | 52 | 170 (44) | 0,822 | **0,847** | **30 (20)** | 7 |
| PIDS2025_GR04_0011 | 128 | 344 (100) | 0,908 | 0,928 | **29 (25)** | 35 |
| **Total** | 672 | 1561 (255) | 0,923 | 0,942 | 83 (63) | 210 |

- **El aumento mejora 9 de las 11 secuencias** y empata en las otras dos (±0,001).
- **Los robots perdidos se concentran en dos secuencias.** `GR03_0011` y `GR04_0011`
  suman 59 de los 83. Son también las que tienen más `difficult`: 144 de los 255.
- **En `PIDS2024_GR04_0003` no detecta ninguno de sus 6 `difficult`.** Es una secuencia
  corta, de 10 imágenes.
- **Las detecciones falsas se concentran en cuatro secuencias:** `GR02_0001`,
  `GR01_0002`, `GR04_0011` y `GR01_0010` suman 152 de las 210.
  **[PENDIENTE]** Mirar en `ejemplos_peores.jpg` si son errores del modelo, cajas
  dobles o robots que el otro grupo no anotó.
- **`PIDS2025_GR01_0010` tiene el peor mAP 0,50:0,95 (0,40)** a pesar de un mAP@0,5 de
  0,905: encuentra los robots pero no ajusta las cajas como las de ese grupo. Hay que
  comprobar si es por cómo anotaron (antenas, robots cortados).

### 8.4 Umbral y velocidad

- **Umbral:** el F1 máximo del modelo con aumento se alcanza con una confianza de
  **0,95** (0,75 sin aumento). Para la *demo*, donde un falso positivo hace disparar,
  conviene un umbral alto, en torno a 0,9–0,95.
- **Velocidad:** unos **73 ms por imagen** en la RTX 3060, unas 14 imágenes por
  segundo.

Figuras en `resultados_test/faster_rcnn_v1_aug_val/`:
- `map_por_grupo.png`;
- `umbral_confianza.png`;
- `ejemplos_peores.jpg`;
- `ejemplos_al_azar.jpg`.

**[PENDIENTE]** Bajarlas del laboratorio; en el repositorio solo están los CSV.

### 8.5 Siguientes pasos

1. **Una mejora dirigida a los `difficult`**, con un único experimento comparado en
   validación igual que aquí. Opciones:
   - un desenfoque de movimiento y una oclusión más agresivos en el aumento;
   - dar más peso a las imágenes con robots difíciles.
2. **Revisar las detecciones falsas** de las cuatro secuencias señaladas.
3. **Evaluar en test una sola vez**, con el modelo definitivo, y fijar el umbral de la
   *demo*.

## 9. Conclusiones

**[PENDIENTE]** Redactarlas al final. Puntos previstos:
- **Dataset:** 796 imágenes y 1399 robots, anotados con criterios comunes y medidos
  (IoU de 0,81 entre anotadores).
- **Aumento de datos:** las decisiones salen del EDA y se han comprobado con datos. Sin
  perder robots ni deformarlos, sube el mAP@0,5 de 0,923 a 0,942, y en los robots
  difíciles de 0,552 a 0,634.
- **Generalización:** el modelo funciona en escenas de otros grupos y años. Tiene un
  mAP@0,5 de 0,942 y de 0,966 en los robots claros.
- **Punto débil:** los robots difíciles, con un mAP@0,5 de 0,634 y una cuarta parte
  sin detectar. La mejora va por ahí, no por entrenar más épocas.

## 10. Reparto del trabajo

**[PENDIENTE]** Repasarlo con el grupo. Según los commits y las PR:

| Integrante | Trabajo |
|---|---|
| Javier Saguar | Repositorio y organización; criterios y guía de anotación; extracción de fotogramas; lote A; revisión de los lotes B, D y E; depuración; aumento de datos y reparto; `difficult` de los conjuntos de la asignatura; evaluación por grupos; entrenamientos y evaluaciones en el laboratorio |
| Alejandro Cuevas | Lote B; revisión del lote C; EDA completo; adaptación de `train.ipynb` y `test.ipynb` |
| Mónica Fernández | Lote C; calibración |
| Pedro José Orrego | Lote D; calibración; propuesta de selección de figuras del EDA |
| Daniel Naval | Lote E; calibración |

## Anexos posibles

- Tabla completa de fichas de los vídeos (`docs/fichas_videos.md`).
- Criterios de anotación completos.
- Lista de imágenes excluidas en la depuración.
- Figuras del EDA que no caben en el cuerpo.
