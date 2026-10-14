# Borrador de la memoria

> **Borrador de trabajo.** Recoge el contenido de la memoria con las cifras reales del
> repositorio, para pasarlo a la plantilla oficial cuando la tengamos. Lo marcado como
> **[PENDIENTE]** falta por hacer o por confirmar.
>
> La primera entrega pide la portada y el **Bloque 1 completo**, con un máximo de 10
> páginas de cuerpo. Las secciones 7 y 8 (Bloque 2) se dejan preparadas para la
> segunda entrega y se pueden recortar o resumir en esta.

**Portada:** PIDS 2026 · Grupo **[PENDIENTE: número]** · Javier Saguar, Alejandro
Cuevas, Mónica Fernández, Pedro José Orrego y Daniel Naval · Primera entrega · Fichero
`PIDS_grupoX_entrega1.pdf`.

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

Figuras: `cajas_antes_despues.png` y `ejemplos_aumento.jpg`.

---

## 7. Entrenamiento (Bloque 2, avance)

Faster R-CNN ResNet-50 FPN (`faster_rcnn_v1`), preentrenado en COCO, 30 épocas, lote
de 8, SGD con tasa de aprendizaje 0,0001. Se entrenó en la RTX 3060 del laboratorio, a
unos 11 minutos por época. El mejor modelo se elige por mAP@0,5 en validación.

- **Época 1:** mAP@0,5 de 0,866.
- **Época 12:** 0,938.
- **Mejor, época 29:** **0,942**.

A partir de la época 12 apenas mejora y **no hay sobreajuste**: la pérdida de
validación se mantiene en torno a 0,233 mientras la de entrenamiento sigue bajando.
La tasa de aprendizaje no llegó a bajar en ningún momento.

Figura: `resultados_train/faster_rcnn_v1_aug/historial.png`.

**[PENDIENTE]** Entrenamiento sin aumento, para comparar (lanzado el 14/10).

## 8. Evaluación (Bloque 2, avance)

Evaluación en **validación** con el mejor modelo, en tres grupos:

| Robots | Cuántos | mAP@0,5 | mAP 0,50:0,95 | Exhaustividad (AR@100) |
|---|---:|---:|---:|---:|
| Todos | 1561 | 0,942 | 0,608 | 0,68 |
| Normales | 1306 | **0,966** | 0,641 | 0,72 |
| `difficult` | 255 | **0,634** | 0,344 | 0,49 |

**Interpretación:**
- El detector funciona muy bien con los robots claros.
- **El punto débil son los `difficult`** (movidos, lejanos, tapados o cortados): 33
  puntos menos de mAP@0,5. La mejora pasa por más ejemplos difíciles o un aumento más
  agresivo de movimiento y oclusión, no por más épocas.
- El mAP 0,50:0,95 es más bajo que el mAP@0,5 porque el modelo localiza bien los
  robots pero ajusta peor las cajas. En parte es esperable: las cajas de validación
  las anotaron otros grupos con otro criterio, por ejemplo para las antenas.

**[PENDIENTE]**
- Desglose por secuencia y umbral de confianza para la demo.
- Comparación con y sin aumento.
- Evaluación final en test, **una sola vez**.

## 9. Conclusiones

**[PENDIENTE]** Redactarlas al final. Puntos previstos:
- Dataset de 796 imágenes y 1399 robots, anotado con criterios comunes y medidos
  (IoU de 0,81).
- Las decisiones del aumento salen del EDA y se comprueban con datos.
- El modelo generaliza a escenas de otros grupos (mAP@0,5 de 0,94) y falla sobre todo
  en los robots difíciles.

## 10. Reparto del trabajo

**[PENDIENTE]** Repasarlo con el grupo. Según los commits y las PR:

| Integrante | Trabajo |
|---|---|
| Javier Saguar | Repositorio y organización; criterios y guía de anotación; extracción de fotogramas; lote A; revisión de los lotes B, D y E; depuración; aumento de datos y reparto; `difficult` de los conjuntos de la asignatura; evaluación por grupos |
| Alejandro Cuevas | Lote B; revisión del lote C; EDA completo; adaptación de `train.ipynb` y `test.ipynb` |
| Mónica Fernández | Lote C; calibración |
| Pedro José Orrego | Lote D; calibración; propuesta de selección de figuras del EDA |
| Daniel Naval | Lote E; calibración |

## Anexos posibles

- Tabla completa de fichas de los vídeos (`docs/fichas_videos.md`).
- Criterios de anotación completos.
- Lista de imágenes excluidas en la depuración.
- Figuras del EDA que no caben en el cuerpo.
