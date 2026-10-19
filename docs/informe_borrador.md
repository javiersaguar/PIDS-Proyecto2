# Borrador de la memoria

> **Borrador de trabajo.** Recoge el contenido de la memoria con las cifras reales del
> repositorio. La plantilla oficial ya está disponible y se incluyen versiones
> completas y por fase en `docs/informes/`. Lo marcado como
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

### 4.3 Posición y recuentos por vídeo y a lo largo del tiempo

El mapa agregado se amplía con mapas por vídeo y con **132 intervalos disjuntos de
5 segundos**, comparando todos los robots con los `difficult`. Una cuadrícula de
16 × 9 recoge los centros normalizados. La frecuencia se expresa en **centros por
100 imágenes**, contando los negativos; ambos grupos comparten escala de color.
Los intervalos finales pueden contener menos imágenes y muestran su recuento.
Así se distingue la frecuencia espacial del número de imágenes de cada grabación.
La paleta cálida usa una intensidad no lineal (gamma 0,4) para hacer visibles las
frecuencias bajas; cero permanece blanco y se conservan las unidades, los máximos
y la escala común entre vídeos y grupos.

Las curvas de recuento muestran los diez vídeos a la vez y avanzan por cada
fotograma anotado. La media global es **1,76 robots por imagen**: V05 presenta la
mayor (**2,27**) y V06 la menor (**1,26**), con 22 negativas entre 93 imágenes.
Las medias incluyen los negativos y las curvas terminan con cada vídeo. Se usan
los 808 originales y 375 `difficult`, antes de depurar. Como el muestreo es cada
24 frames (~0,79 s), no se infiere la presencia de robots entre muestras ni se
identifican robots individuales a lo largo del vídeo.

Los HTML sirven como material complementario. Para el documento se exportan los
mapas globales, las curvas completas y una hoja de intervalos por vídeo a PNG
(300 ppp), SVG y PDF en `resultados_eda/para_informe/`. La normalización común
permite describir diferencias entre grabaciones; no demuestra que la distribución
se mantenga en escenarios nuevos.

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

### 6.4 Ampliaciones preparadas, pendientes de entrenamiento

Se han implementado perfiles separados para explorar sombras locales y lluvia
suave en los dos vídeos exteriores (V04 y V09), obstáculos con textura en lugar de
barras lisas, y oscuridad o movimiento adicionales en una de las copias de imágenes
con `difficult`. Se conservan los originales y tres copias por imagen. En las nuevas
oclusiones se limita la unión de máscaras al 25 % del área de cada caja; esta medida
no equivale al porcentaje visible del cuerpo del robot.

El perfil combinado `robusto_v1` se ha comprobado en memoria sobre las 2388 copias:
conserva 4167 de las 4197 cajas de entrada (pérdida del 0,715 %, igual al aumento
base), con cajas válidas y 24 copias reproducidas exactamente. Se produjeron 109
sombras, 62 lluvias, 347 oclusiones texturadas y 128 refuerzos de copias con
`difficult`. Los destinos están separados del dataset actual.

**Todavía no se ha medido su efecto en mAP.** Estos datos verifican la generación,
no una mejora del detector. Los perfiles individuales permiten estudiar cada
cambio con el resto de parámetros fijo. La lluvia sintética requeriría además
imágenes reales de lluvia para evaluar robustez en esa condición. No se ha evaluado
test ni alterado los datos del experimento lr001, ya finalizado.

Código y lámina de ejemplos PNG/PDF:
`ENTREGA 1/WEEK1/resultados_aug/experimentos/README.md`.

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
  aprendizaje no llegó a bajar. La mejora tardía es pequeña; la curva por sí sola
  no permite predecir cuánto aportarían más épocas.
- **No se aprecia un deterioro sostenido de validación** en estos dos experimentos con lr=0,0001. La pérdida de validación se mantiene
  estable (0,243 sin aumento, 0,235 con aumento) mientras la de entrenamiento sigue
  bajando.

Figuras: `resultados_train/faster_rcnn_v1_aug/historial.png` y
`resultados_train/faster_rcnn_v1_sin_aug/historial.png` recuperadas del laboratorio y versionadas junto con los CSV.

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
  Se ha confirmado al menos un caso de anotación incompleta; véase la sección 8.6.
  No se puede atribuir el conjunto de los FP a etiquetas ausentes sin revisarlos uno a uno.
- **`PIDS2025_GR01_0010` tiene el peor mAP 0,50:0,95 (0,40)** a pesar de un mAP@0,5 de
  0,905: encuentra los robots pero no ajusta las cajas como las de ese grupo. Hay que
  comprobar si es por cómo anotaron (antenas, robots cortados).

### 8.4 Umbral y velocidad

- **Umbral del modelo original:** el mayor F1 de la rejilla ensayada aparece en
  **0,95**, extremo superior de esa rejilla (0,75 sin aumento). No es una localización
  exacta del óptimo. Con lr=0,001 la mejor muestra está en 0,85; hay que volver a
  decidir el umbral para el modelo definitivo y el coste de los errores en la demo.
- **Velocidad:** unos **73 ms por imagen** en la RTX 3060, unas 14 imágenes por
  segundo.

Figuras en `resultados_test/faster_rcnn_v1_aug_val/`:
- `map_por_grupo.png`;
- `umbral_confianza.png`;
- `ejemplos_peores.jpg`;
- `ejemplos_al_azar.jpg`.

Figuras recuperadas del laboratorio y versionadas junto con los CSV.

### 8.5 Experimento de tasa de aprendizaje 0,001

`faster_rcnn_v1_aug_lr001` finalizó el 15/10/2026 a las 22:13 Europe/Madrid,
incluida su evaluación automática en validación (salida 0). Se mantuvieron COCO,
SGD, 30 épocas, lote 8, semilla 0 y el mismo aumento base. Las ampliaciones de
sombras, lluvia y oclusión texturada no participan en este resultado.

**Curvas y mejor época.** El mejor AP@0,5 del historial aparece en la época **5**:
0,943169, frente a 0,942506 en la época 29 con lr=0,0001 (+0,066 puntos
porcentuales). El AP 0,50:0,95 de esas épocas es 0,629899 frente a 0,607000.
La pérdida de validación alcanza su mínimo en la época 4 (0,221198) y luego sube,
mientras la de entrenamiento sigue bajando hasta 0,065661. En la época 30 el
AP@0,5 ha caído a 0,933178 y la pérdida de validación es 0,241296. Hay indicios
de sobreajuste después del óptimo temprano; añadir épocas no resuelve esa caída.
`ReduceLROnPlateau` sí actuó: las tasas usadas fueron 0,001 en épocas 1–10,
0,0001 en 11–16, 0,00001 en 17–22, 0,000001 en 23–28 y 0,0000001 en 29–30.
Las bajadas no recuperaron el mejor resultado. Debe usarse `model_best.pt`, no
el checkpoint final. La época 5 habría necesitado aproximadamente 54 minutos
al ritmo observado, pero se completaron las 30 épocas en unas 5 h 19 min.

**Evaluación de los mejores checkpoints con el mismo notebook de validación:**

| Métrica | lr=0,0001 | lr=0,001 | Cambio |
|---|---:|---:|---:|
| AP@0,5, todos | 0,9416 | 0,9433 | +0,17 pp |
| AP 0,50:0,95, todos | 0,6081 | 0,6302 | +2,21 pp |
| AP@0,75, todos | 0,7146 | 0,7460 | +3,14 pp |
| AP@0,5, normales | 0,9664 | 0,9740 | +0,76 pp |
| AP@0,5, difficult | 0,6341 | 0,6462 | +1,21 pp |
| AP de objetos pequeños | 0,1074 | 0,1182 | +1,08 pp |
| TP / FN con confianza ≥0,5 e IoU ≥0,5 | 1478 / 83 | 1478 / 83 | Sin cambio |
| FN normales / difficult | 20 / 63 | 18 / 65 | 2 normales menos; 2 difficult más |
| FP frente a las etiquetas | 210 | 190 | −20 |
| Precisión / F1 al umbral 0,5 | 0,8756 / 0,9098 | 0,8861 / 0,9155 | +1,05 / +0,57 pp |

Las cifras del historial y de la evaluación final son salidas de procedimientos
distintos y se presentan por separado. La mejora principal está en el ajuste de
las cajas y en reducir detecciones contadas como FP, no en detectar más robots
al umbral 0,5. Aunque sube el AP de difficult al recorrer las confianzas, su
exhaustividad con confianza 0,5 baja de 0,7529 a 0,7451. No es una mejora uniforme.

**Por secuencia.** El AP@0,5 sube en 7 de las 11 secuencias y baja en 4. Destaca
`PIDS2025_GR01_0010`: 0,9049 → 0,9404 (+3,55 pp) y FN 4 → 1. En cambio,
`PIDS2025_GR04_0011` pasa de 29 a 33 FN, y sus difficult perdidos de 25 a 28;
`PIDS2025_GR01_0002` baja en AP@0,5 de difficult de 0,8640 a 0,7540.
`PIDS2024_GR04_0003` sigue perdiendo sus 6 difficult. La tabla completa está en
`comparaciones/lr001/secuencias_comparadas.csv`.

**Umbral y coste.** El mayor F1 de las muestras 0,05, 0,10, …, 0,95 está ahora en
0,85; es una propuesta para volver a revisar con el modelo definitivo. La latencia
medida es 72,7 ms por imagen en lote y 75,1 ms una a una en la RTX 3060. No incluye
captura, red ni actuación del robot y no equivale al rendimiento completo de la demo.

**Decisión provisional.** Se toma lr=0,001 como referencia del siguiente experimento
por el AP agregado, el mejor ajuste de cajas y los FP menores, conservando el
checkpoint de la época 5. Una única semilla y +0,17 pp en AP@0,5 no prueban una
mejora estable. La resolución propuesta por Alejandro es el siguiente cambio
prioritario para estudiar objetos pequeños. Se mantiene el aumento base y no se
mezclan a la vez arquitectura, resolución y nuevas degradaciones.

Figuras: `comparaciones/lr001/curvas_comparadas.png`, `lr_comparado.png` y
`secuencias_comparadas.png`; métricas y ejemplos originales en
`resultados_test/faster_rcnn_v1_aug_lr001_val/`.

### 8.6 Limitación confirmada de las etiquetas de validación

`PIDS2024_GR02_0001/frame_0444.jpg` muestra **cuatro robots visibles**, pero su XML
contiene **una sola caja**. Por tanto, detectar correctamente alguno de los otros
robots puede contarse como falso positivo. Esto limita la interpretación de
precisión, FP, F1 y AP frente a esas etiquetas: los 190 FP de lr001 y los 324 de
res1024 no equivalen necesariamente al mismo número de errores visuales del detector. No se ha cuantificado cuántos casos presentan
este problema ni se han corregido las etiquetas, para conservar la comparación.
No se ha usado test para tomar estas decisiones.

### 8.7 Experimento de resolución 1024/1820

Validación de los checkpoints seleccionados por AP50. Misma semilla 0, COCO,
lr inicial 0,001, SGD, ReduceLROnPlateau y aumento base. No se usa test.
La resolución cambia de 800/1333 a 1024/1820. Para memoria, el lote físico 8
se sustituye por microbatch 4 y acumulación 2 (efectivo 8); no son numéricamente
idénticos. Ejecución terminada el 16/10/2026 hacia las 08:45 Europe/Madrid, salida 0.

| Métrica | lr001 800 | lr001 1024 | Cambio |
|---|---:|---:|---:|
| AP50 | 0,9433 | 0,9465 | +0,32 pp |
| AP 0,50:0,95 | 0,6302 | 0,6047 | −2,55 pp |
| AP75 | 0,7460 | 0,6990 | −4,70 pp |
| AP50 difficult | 0,6462 | 0,6282 | −1,80 pp |
| AP small | 0,1182 | 0,1886 | +7,04 pp |
| AP large | 0,6919 | 0,6459 | −4,60 pp |
| TP / FN a confianza 0,5 e IoU 0,5 | 1478 / 83 | 1493 / 68 | 15 FN menos |
| FN difficult | 65 | 56 | 9 menos |
| FP frente a etiquetas | 190 | 324 | 134 más |
| Precisión / F1 a confianza 0,5 | 0,8861 / 0,9155 | 0,8217 / 0,8840 | Empeoran |
| Recall difficult a confianza 0,5 | 0,7451 | 0,7804 | +3,53 pp |
| Inferencia individual, ms/imagen | 75,1 | 121,6 | +61,9 % |

**Decisión provisional:** conservar lr001 a resolución original como referencia
por equilibrio entre AP, FP y coste. La resolución beneficia pequeños y recall al
umbral fijo, pero no mejora de forma uniforme. Una semilla no prueba estabilidad.

**Selección del checkpoint:** res1024 alcanza su mejor AP50 del historial en la
época 2 (0,946440), frente a la 5 de lr001 (0,943169). Su máximo AP 0,50:0,95 está
en la época 5 (0,632233), mientras la época 2 da 0,605390. Se mantiene el criterio
AP50 definido antes del entrenamiento. No se ha reevaluado otro checkpoint ni se
afirma que toda ejecución de mayor resolución empeore el ajuste de cajas.
El historial y la evaluación final proceden de procedimientos distintos.

**Curvas:** pérdida de validación mínima en época 3 (0,215909), final 0,232343;
AP50 final 0,933510. Indicios de sobreajuste y posterior estancamiento. Las tasas
usadas son 0,001 en 1–9, 0,0001 en 10–15, 1e−5 en 16–21, 1e−6 en 22–27 y 1e−7
en 28–30. Las bajadas no recuperan el máximo AP50. No se recomienda prolongarlo.

**Secuencias:** AP50 sube en 4, baja en 6 y empata en una. GR03_0011 de 2025 gana
4,16 pp y reduce FN 28→22. GR04_0011 de 2025 reduce FN 33→25 pero sube FP 28→58.
GR01_0002 de 2025 pierde 1,20 pp. GR04_0003 de 2024 sigue perdiendo sus 6 difficult.

**Límites:** `PIDS2024_GR02_0001/frame_0444.jpg` contiene cuatro robots visibles,
pero su XML solo una caja. Algunas detecciones correctas cuentan como FP; no se
ha cuantificado la extensión ni se atribuyen todos los 324 FP a etiquetas omitidas.
GR02_0001 pasa de 49 a 71 FP frente a esas etiquetas. No se corrigen los conjuntos.
La latencia en lote (72,7→120,5 ms/imagen) usa lotes distintos, 8→4; se prefiere
la comparación individual. El pico de 8482 MiB fue del preflight, no del entrenamiento
completo. El mejor F1 muestreado pasa de confianza 0,85 a 0,95 (extremo de la rejilla).


La muestra de `res1024` en `PIDS2025_GR03_0011/frame_0600` incluye una caja
roja sobre una pierna y varias cajas solapadas en torno a un objetivo. Las omisiones
confirmadas en otras etiquetas no explican todos los errores.

Figuras y datos auditables en `ENTREGA 1/WEEK2/comparaciones/res1024/`.

### 8.8 Siguientes pasos

1. Mantener provisionalmente lr001 a resolución original como referencia por equilibrio
   entre ajuste de cajas, FP y latencia. Conservar res1024 como alternativa para pequeños.
2. Revisar visualmente los errores, distinguiendo omisiones de etiquetas y errores reales.
3. Si hay margen, comparar una ampliación dirigida a `difficult` con el resto fijo o una
   segunda arquitectura. Las nuevas sombras, lluvia y oclusiones no se han entrenado.
4. Elegir modelo y umbral antes de evaluar test una sola vez. No se ha usado test.

## 9. Conclusiones

Conclusiones provisionales de las fases 1 y 2; falta comparación de arquitecturas,
evaluación final de test y revisión del grupo.

- **Datos:** 796 originales depurados y 1399 cajas; con aumento base, 3184 imágenes
  y 5566 cajas. El IoU medio entre anotadores es 0,81, sin implicar un techo del AP.
- **Aumento base:** AP50 de 0,9228 a 0,9416; AP50 difficult de 0,5518 a 0,6341.
  La comparación también cambia el número de actualizaciones a igual número de épocas.
- **Tasa:** lr001 alcanza su mejor AP50 en época 5 y mejora el ajuste de cajas;
  evaluación final AP50 0,9433, AP 0,50:0,95 0,6302 y 190 FP frente a etiquetas.
- **Resolución:** AP50 0,9465 y AP small 0,1886, con 15 FN menos, pero 134 FP más,
  AP 0,50:0,95 0,6047 y latencia individual 121,6 ms frente a 75,1 ms. No mejora
  uniformemente: se mantiene lr001 800 como referencia y se explicita la selección por AP50.
- **Límites:** una semilla, adaptación del microbatch y etiquetas incompletas de
  validación. Las ampliaciones del aumento están preparadas, sin resultados entrenados.

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
