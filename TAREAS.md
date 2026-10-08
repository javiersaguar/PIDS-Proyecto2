# Tareas

Lista de tareas **ordenadas por prioridad**: cuanto más arriba, antes hay que hacerla. El estado general del proyecto está en [`ESTADO.md`](ESTADO.md).

## Cómo asignarse una tarea

1. Elige una tarea con **Responsable** vacío (`—`). Empieza por las de arriba cuyas dependencias ya estén hechas.
2. Escribe tu nombre en la columna **Responsable** y cambia el **Estado** a `En curso`.
3. Haz commit directamente en `main` con el mensaje `Asigna T0X a <nombre>`. Se puede hacer desde la web de GitHub con el lápiz de editar. Este fichero y `ESTADO.md` son los únicos que se editan directamente en `main`.
4. Cuando la termines, pon el **Estado** a `Hecha` y, si hace falta, actualiza `ESTADO.md`.

En una tarea puede haber más de una persona (`Javier, Mónica`). Antes de editar, haz *pull* o recarga la página para no pisar la asignación de otro.

**Prioridad:**
- **P1:** bloquea al resto. Sin ella no se puede avanzar.
- **P2:** necesaria para la primera entrega.
- **P3:** para después de la primera entrega (Bloque 2).

**Estado:** `Pendiente` · `En curso` · `Hecha`

## Resumen

| ID | Prioridad | Tarea | Depende de | Responsable | Estado |
|---|---|---|---|---|---|
| T01 | P1 | Acordar y documentar los criterios de anotación | — | — | Pendiente |
| T02 | P1 | Ficha de cada vídeo y revisión de la variabilidad | — | — | Pendiente |
| T03 | P1 | Extraer fotogramas en JupyterHub (`INTERVAL = 24`) | — | — | Pendiente |
| T04 | P1 | Anotar el lote A (vídeos 01 y 02, ~158 imágenes) | T01, T03 | — | Pendiente |
| T05 | P1 | Anotar el lote B (vídeos 03 y 04, ~159 imágenes) | T01, T03 | — | Pendiente |
| T06 | P1 | Anotar el lote C (vídeos 05 y 06, ~169 imágenes) | T01, T03 | — | Pendiente |
| T07 | P1 | Anotar el lote D (vídeos 07 y 08, ~180 imágenes) | T01, T03 | — | Pendiente |
| T08 | P1 | Anotar el lote E (vídeos 09 y 10, ~147 imágenes) | T01, T03 | — | Pendiente |
| T09 | P1 | Copia de seguridad del dataset anotado | T04–T08 | — | Pendiente |
| T10 | P2 | Revisión cruzada de las anotaciones | T04–T08 | — | Pendiente |
| T11 | P2 | EDA base con `eda.ipynb` | T10 | — | Pendiente |
| T12 | P2 | Análisis exploratorio adicional | T11 | — | Pendiente |
| T13 | P2 | Depuración del dataset | T10, T11 | — | Pendiente |
| T14 | P2 | Aumento de datos con `data_aug.ipynb` | T13 | — | Pendiente |
| T15 | P2 | Memoria: portada, introducción, recolección y anotación | T01, T02 | — | Pendiente |
| T16 | P2 | Memoria: EDA, depuración y aumento de datos | T12, T13, T14 | — | Pendiente |
| T17 | P2 | Memoria: reparto del trabajo, revisión final y PDF | T15, T16 | — | Pendiente |
| T18 | P3 | Separar los datos en entrenamiento, validación y test | T14 | — | Pendiente |
| T19 | P3 | Primer entrenamiento con `train.ipynb` | T18 | — | Pendiente |
| T20 | P3 | Evaluación con `test.ipynb` (mAP y resultados cualitativos) | T19 | — | Pendiente |

## Detalle

### T01 · Acordar y documentar los criterios de anotación (P1)

Va antes que nada: si cada uno anota a su manera, el modelo aprende cajas inconsistentes. Hay una **propuesta completa** en [`docs/criterios_anotacion.md`](docs/criterios_anotacion.md), con reglas justificadas, ejemplos de nuestros vídeos y una ronda de calibración. Hay que revisarla **entre los cinco**, cerrar las decisiones de su sección 7 y hacer la calibración.
- ¿Se anotan los robots parcialmente ocluidos? ¿A partir de qué porcentaje visible?
- ¿Y los robots muy lejanos, desenfocados o cortados por el borde de la imagen?
- ¿Qué tan ajustada va la caja: al chasis, o incluyendo el cañón y las antenas?
- Una sola clase: `robot`. Formato PascalVOC.

**Hecha cuando:** las decisiones están cerradas, la calibración llega a un IoU medio de 0,80 o más (`herramientas/revisar_anotaciones.py acuerdo`) y el documento ya no pone «propuesta». Estos criterios hay que justificarlos en la memoria.

### T02 · Ficha de cada vídeo y revisión de la variabilidad (P1)

Completar en `ESTADO.md`, para cada vídeo, el escenario y sus condiciones: lugar, interior o exterior, iluminación, oclusiones, número de robots, distancia y movimiento de la cámara. Después, comprobar si el conjunto cubre lo que pide el enunciado. Si falta algo (por ejemplo, ningún vídeo en exterior o sin oclusiones), proponer grabar más **cuanto antes**.

**Hecha cuando:** la tabla está completa y está decidido si hace falta grabar más.

### T03 · Extraer fotogramas en JupyterHub (P1)

Subir los vídeos a `data_train/` en JupyterHub. Los zips se descomprimen con `unzip` desde el terminal, porque el panel no admite carpetas. Después, ejecutar `video2frames.ipynb` con `INTERVAL = 24`, que da ~813 imágenes (ver `ESTADO.md`).

**Hecha cuando:** existen `data_train/ROBOMASTER_VIDEO_XX/images` y `labels` para los 10 vídeos, y el zip con las imágenes está compartido con el grupo para anotar.

### T04–T08 · Anotar los lotes A–E (P1)

Cada lote son dos vídeos, más o menos un quinto del trabajo de anotación: lo ideal es que cada integrante coja uno. Se anota con `labelImg` siguiendo los criterios de T01:
- *View* → *Single Class Mode*
- Formato **PascalVOC**
- Clase `robot`
- *Open Dir* sobre `images` y *Change Save Dir* sobre `labels`

**Hecha cuando:** `python herramientas/revisar_anotaciones.py validar ../data_train` no da errores en el lote y el lote está de vuelta en JupyterHub.

### T09 · Copia de seguridad del dataset anotado (P1)

Comprimir `data_train/` en JupyterHub (`zip -r`), descargarlo y guardarlo en la nube compartida del grupo. Los `.xml` de las etiquetas pesan poco: versionarlos también en el repo (`ENTREGA 1/WEEK1/labels/`). Las imágenes no se suben al repo (ver `AGENTS.md`).

**Hecha cuando:** hay una copia fuera de JupyterHub y las etiquetas están en `main`.

### T10 · Revisión cruzada de las anotaciones (P2)

Cada integrante revisa un lote que no ha anotado (A→B→C→D→E→A) y busca cajas mal ajustadas, robots sin anotar o criterios aplicados de forma distinta. Los errores los corrige quien anotó el lote.

**Hecha cuando:** los cinco lotes están revisados y corregidos.

### T11 · EDA base con `eda.ipynb` (P2)

Ejecutar el notebook sobre nuestros datos. Salen imágenes y cajas por secuencia, la distribución del área de las cajas y la distribución RGB. Hay que guardar las figuras para la memoria e interpretarlas, no solo pegarlas.

**Hecha cuando:** el notebook está ejecutado con nuestros datos en `ENTREGA 1/WEEK1/` y las figuras están exportadas.

### T12 · Análisis exploratorio adicional (P2)

El enunciado exige **al menos un análisis propio**, explicando qué pregunta responde y qué ha revelado. Algunas ideas:
- Mapa de calor de la posición de los centros de las cajas.
- Número de robots por imagen y proporción de imágenes sin robots.
- Relación de aspecto de las cajas.
- Nitidez de cada imagen (varianza del Laplaciano) para detectar fotogramas movidos.
- Similitud entre fotogramas consecutivos para detectar casi-duplicados.

**Hecha cuando:** hay al menos uno, con su figura e interpretación.

### T13 · Depuración del dataset (P2)

Buscar y corregir o eliminar:
- Etiquetas incorrectas.
- Cajas de robots que no se ven.
- Imágenes casi idénticas.
- Fotogramas muy movidos o poco representativos.

Cuidado con no quitar todos los casos difíciles: el modelo fallaría en la realidad. Hay que documentar el **criterio** y cuántas imágenes se tocan. Si no hay nada que depurar, se explica cómo se ha comprobado.

**Hecha cuando:** el dataset limpio está en JupyterHub, la copia de T09 está actualizada y el criterio está escrito.

### T14 · Aumento de datos con `data_aug.ipynb` (P2)

Revisar las transformaciones del notebook y decidir cuáles se quedan y cuáles no. Por ejemplo, el volteo horizontal tiene sentido; el vertical no, porque el robot nunca va boca abajo. Hay que **añadir al menos una nueva** y justificar tanto las que se mantienen como las que se descartan. El aumento se aplica **solo sobre los datos originales**, nunca sobre los ya aumentados.

**Hecha cuando:** existen las carpetas `-aug`, la lista de transformaciones está justificada y hay figuras de ejemplo.

### T15 · Memoria: portada, introducción, recolección y anotación (P2)

Sobre la plantilla `PIDS-template.docx`. La introducción presenta el problema. La recolección incluye la tabla de vídeos de `ESTADO.md` y la variabilidad (T02); la anotación, los criterios de T01. Se puede empezar en paralelo a la anotación.

### T16 · Memoria: EDA, depuración y aumento de datos (P2)

Recoge T11–T14 y pone el foco en la **justificación** de cada decisión y en la interpretación crítica de los resultados, que es lo que más se valora.

### T17 · Memoria: reparto del trabajo, revisión final y PDF (P2)

- Añadir el apartado de reparto del trabajo, tomando los responsables de esta tabla.
- Revisar la extensión: máximo **10 páginas de cuerpo**, sin contar portada, índice, reparto, referencias ni anexos.
- Exportar un único `PIDS_grupoX_entrega1.pdf`.

**Hecha cuando:** el PDF está entregado.

### T18–T20 · Bloque 2 (P3)

Para después de la primera entrega:
- **T18:** separar `data_train`, `data_val` y `data_test` por secuencias, para que no se filtren fotogramas casi iguales entre conjuntos.
- **T19:** primer entrenamiento con `train.ipynb` (`faster_rcnn_v1`) en el entorno GPU de JupyterHub.
- **T20:** evaluar con `test.ipynb` (mAP y resultados cualitativos).
