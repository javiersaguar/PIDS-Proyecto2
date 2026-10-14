# Tareas

Lista de tareas **ordenadas por prioridad**: cuanto más arriba, antes hay que hacerla. El estado general del proyecto está en [`ESTADO.md`](ESTADO.md).

## Cómo asignarse una tarea

1. Elige una tarea con **Responsable** vacío (`—`). Empieza por las de arriba cuyas dependencias ya estén hechas.
2. Escribe tu nombre en la columna **Responsable** y cambia el **Estado** a `En curso`.
3. Haz el cambio en tu rama personal, con el mensaje `Asigna T0X a <nombre>`, y abre o actualiza su PR hacia `main`. Este fichero y `ESTADO.md` también pasan por PR y revisión; no se editan directamente en `main` (ver `AGENTS.md`).
4. Cuando la termines, pon el **Estado** a `Hecha` y, si hace falta, actualiza `ESTADO.md`.

En una tarea puede haber más de una persona (`Javier, Mónica`). Antes de editar, haz *pull* o recarga la página para no pisar la asignación de otro.

No hace falta una Issue por cada tarea de esta tabla. Abrirla cuando haya un error,
bloqueo, decisión que discutir o trabajo que abarque varias PRs o personas; enlazarla
desde la tarea y las PRs relacionadas para conservar el seguimiento.

**Prioridad:**
- **P1:** bloquea al resto. Sin ella no se puede avanzar.
- **P2:** necesaria para la primera entrega.
- **P3:** para después de la primera entrega (Bloque 2).

**Estado:** `Pendiente` · `En curso` · `Hecha`

Actualización del 09/10/2026 en `javier-saguar`, por petición de Javier. T01 y T03
tienen preparación completa, pero conservan el estado `En curso` por sus pasos
externos pendientes (calibración del grupo e importación en JupyterHub). Los lotes
se asignan para planificar; la anotación todavía no ha empezado.

Actualización del 14/10/2026 en `javier-saguar`. **Todo lo previo al entrenamiento
está hecho**, salvo lo que necesita al grupo o al laboratorio:

- Hechas: anotación y revisión cruzada de los cinco lotes (T04–T08, T10), copia de
  seguridad en `main` (T09), depuración con 12 imágenes excluidas y 796 restantes
  (T13) y aumento regenerado con ella (T14).
- Falta el grupo: cerrar los criterios (T01).
- Reparto (T18): se entrena con nuestros diez vídeos y se valida y mide con los
  conjuntos de otros grupos que da la asignatura.
- Bloque 3: el material de la semana 3 está en `ENTREGA 2/WEEK3/`, con lo que hay que
  hacer en su `README.md`.
- Falta el laboratorio: llevar los datos a JupyterHub y lanzar el entrenamiento (T03,
  T19), siguiendo [`docs/jupyterhub.md`](docs/jupyterhub.md). Los notebooks de
  entrenamiento y test adaptados están en la PR #11 de Alejandro.

Actualización del 10/10/2026 en `alejandro-cuevas`. T05 hecha: lote B anotado y
validado sin errores. La calibración de Alejandro (T01) está subida.

Actualización del 10/10/2026 en `monica-fernandez`. T06 hecha: lote C anotado y
validado sin errores. La calibración de Mónica (T01) está subida ([PR #4](https://github.com/javiersaguar/PIDS-Proyecto2/pull/4)).

Actualización del 12/10/2026 en `alejandro-cuevas`. T11 y T12 en curso: `eda.ipynb`
está adaptado y ejecutado con las 808 imágenes y 1420 robots. Incluye el EDA base y
diez análisis propios en tres bloques: calidad de las etiquetas (acuerdo entre
anotadores, perspectiva, solapamiento), composición (robots por imagen, centros,
forma y anclas, diversidad visual) y candidatas para la depuración (nitidez, casi
duplicados, línea temporal). Cada análisis tiene su interpretación y su decisión
para T13, T14, T18, T19 o T20. Figuras, tablas y pies propuestos en
`ENTREGA 1/WEEK1/resultados_eda/`. Falta volver a ejecutarlo cuando termine la
revisión cruzada (T10) y revisar las conclusiones en grupo.
`metricas_imagenes.csv` es la entrada de T13.

Actualización del 14/10/2026 en `alejandro-cuevas`. T19 y T20 en curso, adelantadas
mientras se hace T13: `train.ipynb` y `test.ipynb` están adaptados a nuestros datos,
**sin ejecutar**. Falta entrenar en la GPU de JupyterHub cuando estén `data_train`,
`data_val` y `data_test` y el reparto (T18) esté acordado.

## Resumen

| ID | Prioridad | Tarea | Depende de | Responsable | Estado |
|---|---|---|---|---|---|
| T01 | P1 | Criterios v1; calibración de los cinco medida (IoU 0,81); falta cerrarla en grupo | — | Javier Saguar; calibración: los cinco | En curso |
| T02 | P1 | Ficha de cada vídeo y revisión de la variabilidad | — | Javier Saguar | Hecha |
| T03 | P1 | Dataset listo para JupyterHub ([guía](docs/jupyterhub.md)); falta subirlo en el laboratorio | — | Javier Saguar | En curso |
| T04 | P1 | Anotar el lote A (vídeos 01 y 02, 157 imágenes) | T01, T03 | Javier Saguar | Hecha |
| T05 | P1 | Anotar el lote B (vídeos 03 y 04, 158 imágenes) | T01, T03 | Alejandro Cuevas | Hecha |
| T06 | P1 | Anotar el lote C (vídeos 05 y 06, 168 imágenes) | T01, T03 | Mónica Fernández | Hecha |
| T07 | P1 | Anotar el lote D (vídeos 07 y 08, 179 imágenes) | T01, T03 | Pedro José Orrego | Hecha |
| T08 | P1 | Anotar el lote E (vídeos 09 y 10, 146 imágenes) | T01, T03 | Daniel Naval | Hecha |
| T09 | P1 | Copia de seguridad del dataset anotado | T04–T08 | Javier Saguar | Hecha |
| T10 | P2 | Revisión cruzada de las anotaciones | T04–T08 | Javier Saguar, Alejandro Cuevas | Hecha |
| T11 | P2 | EDA base con `eda.ipynb` | T10 | Alejandro Cuevas | En curso |
| T12 | P2 | Análisis exploratorio adicional | T11 | Alejandro Cuevas | En curso |
| T13 | P2 | Depuración del dataset | T10, T11 | Javier Saguar | Hecha |
| T14 | P2 | Aumento de datos con `data_aug.ipynb` | T13 | Javier Saguar | Hecha |
| T15 | P2 | Memoria: portada, introducción, recolección y anotación | T01, T02 | — | Pendiente |
| T16 | P2 | Memoria: EDA, depuración y aumento de datos | T12, T13, T14 | — | Pendiente |
| T17 | P2 | Memoria: reparto del trabajo, revisión final y PDF | T15, T16 | — | Pendiente |
| T18 | P3 | Separar los datos en entrenamiento, validación y test | T14 | — | Pendiente |
| T19 | P3 | Primer entrenamiento con `train.ipynb` | T18 | Alejandro Cuevas | En curso |
| T20 | P3 | Evaluación con `test.ipynb` (mAP y resultados cualitativos) | T19 | Alejandro Cuevas | En curso |

## Detalle

### T01 · Acordar y documentar los criterios de anotación (P1)

Va antes que nada: si cada uno anota a su manera, el modelo aprende cajas inconsistentes. Los **criterios operativos v1** están en [`docs/criterios_anotacion.md`](docs/criterios_anotacion.md), con reglas justificadas y opciones adoptadas por Javier para preparar los lotes. Hay que revisarlos **entre los cinco** y hacer la calibración.
- ¿Se anotan los robots parcialmente ocluidos? ¿A partir de qué porcentaje visible?
- ¿Y los robots muy lejanos, desenfocados o cortados por el borde de la imagen?
- ¿Qué tan ajustada va la caja: al chasis, o incluyendo el cañón y las antenas?
- Una sola clase: `robot`. Formato PascalVOC.

**Preparado:** veinte originales comunes, dos por vídeo, con nombres únicos y carpetas de etiquetas por integrante en [`ANOTACION/calibracion`](ENTREGA%201/WEEK1/ANOTACION/calibracion/README.md). El script rechaza rondas vacías o incompletas.

**Hecha cuando:** revisión y decisiones colectivas registradas; los cinco anotan las mismas veinte imágenes y cada pareja llega a IoU medio ≥ 0,80, sin robots sin emparejar a IoU ≥ 0,50. Ejecutar `herramientas/revisar_anotaciones.py acuerdo` como indica el README de calibración. No hay todavía una medida real ni un acuerdo colectivo.

### T02 · Ficha de cada vídeo y revisión de la variabilidad (P1)

Completar en `ESTADO.md`, para cada vídeo, el escenario y sus condiciones: lugar, interior o exterior, iluminación, oclusiones, número de robots, distancia y movimiento de la cámara. Después, comprobar si el conjunto cubre lo que pide el enunciado. Si falta algo (por ejemplo, ningún vídeo en exterior o sin oclusiones), proponer grabar más **cuanto antes**.

**Hecha cuando:** la tabla está completa y está decidido si hace falta grabar más.

**Resultado:** fichas completas en [`docs/fichas_videos.md`](docs/fichas_videos.md) y 120 muestras registradas en [`docs/revision_videos.csv`](docs/revision_videos.csv). Hay interior/exterior, distancias aparentes, movimiento, distintas orientaciones, luz y oclusiones. No hace falta repetir ahora un escenario para empezar; reservar material complementario si al depurar se necesitan más originales y grabar el circuito real para el Bloque 3.

### T03 · Extraer fotogramas en JupyterHub (P1)

**Extracción realizada localmente:** 808 imágenes con `INTERVAL = 24`, resolución original y calidad JPEG 95. Están organizadas en [`ANOTACION/`](ENTREGA%201/WEEK1/ANOTACION/README.md). `video2frames.ipynb` comparte el extractor reproducible y se ha ejecutado para comprobar la integridad. `manifest.csv` y `videos.json` conservan procedencia, metadatos y SHA-256.

**Pendiente:** importar a JupyterHub. Crear el ZIP con `python herramientas/empaquetar_anotacion.py ../fotogramas_pids.zip`, subirlo a `/workspace` y descomprimir en un destino vacío. El ZIP ya contiene `data_train/ROBOMASTER_VIDEO_XX/{images,labels}`, sin la capa de lotes. No se ha accedido todavía a JupyterHub.

**Hecha cuando:** existen `data_train/ROBOMASTER_VIDEO_XX/images` y `labels` para los 10 vídeos, y el zip con las imágenes está compartido con el grupo para anotar.

**Estado a 14/10/2026:** la anotación se hizo en local, así que lo que hay que llevar a JupyterHub es el dataset ya repartido y aumentado. [`docs/jupyterhub.md`](docs/jupyterhub.md) explica las dos formas (clonar el repositorio y ejecutar `data_aug.ipynb` allí, o subir `dataset_pids.zip`) y cómo dejar el entrenamiento corriendo. Falta hacerlo en el laboratorio.

### T04–T08 · Anotar los lotes A–E (P1)

Cada integrante tiene asignado un lote de dos vídeos, como indica la tabla. Las carpetas y el README de cada lote están en `ENTREGA 1/WEEK1/ANOTACION/`. Se anota con `labelImg` siguiendo los criterios de T01:
- *View* → *Single Class Mode*
- Formato **PascalVOC**
- Clase `robot`
- *Open Dir* sobre `images` y *Change Save Dir* sobre `labels`

**Hecha cuando:** `python herramientas/revisar_anotaciones.py validar "ENTREGA 1/WEEK1/ANOTACION/<tu-lote>"` no da errores y el lote anotado está de vuelta en JupyterHub. Las carpetas `labels/` tienen solo `.gitkeep` hasta empezar: no hay XML negativos creados sin revisar imágenes.

### T09 · Copia de seguridad del dataset anotado (P1)

Comprimir `data_train/` en JupyterHub (`zip -r`), descargarlo y guardarlo en la nube compartida del grupo. Versionar también los `.xml` en el `labels/` de su secuencia dentro de `ANOTACION/<tu-lote>/`. Los originales ya se versionan por autorización de Javier (ver `AGENTS.md`); no se suben aumentos ni MP4 sueltos.

**Hecha cuando:** hay una copia fuera de JupyterHub y las etiquetas están en `main`.

**Hecha (14/10/2026):** los 808 fotogramas originales y sus `.xml` revisados están versionados en `main` (`ENTREGA 1/WEEK1/ANOTACION/`), que es la copia de referencia fuera de JupyterHub. Los conjuntos aumentados no se copian: `data_aug.ipynb` los regenera idénticos a partir de esa copia.

### T10 · Revisión cruzada de las anotaciones (P2)

Cada integrante revisa un lote que no ha anotado (A→B→C→D→E→A) y busca cajas mal ajustadas, robots sin anotar o criterios aplicados de forma distinta. Los errores los corrige quien anotó el lote.

**Hecha cuando:** los cinco lotes están revisados y corregidos.

**Hecha (12/10/2026):** Javier revisó los lotes B, D y E (PR #3 y #7) y Alejandro el C (PR #8). Los cambios de cada lote están descritos en sus PRs y los casos dudosos en `docs/casos_dudosos.md`.

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

**Hecha (14/10/2026):** se revisaron a ojo las 69 candidatas (52 poco nítidas, 11 casi duplicadas y 6 casos dudosos) y se excluyen 12: una con un robot sin caja y 11 casi duplicadas. Quedan 796 imágenes. Criterios y lista en [`docs/depuracion.md`](docs/depuracion.md); `data_aug.ipynb` aplica la exclusión leyendo `docs/depuracion_excluir.csv`. No se borra ningún original. El dataset limpio llega a JupyterHub con T03.

### T14 · Aumento de datos con `data_aug.ipynb` (P2)

**Hecha (14/10/2026):** regenerado con la depuración y con el reparto nuevo: 796 imágenes de entrenamiento y 2388 copias (3184 en total); validación (672) y test (718) son los conjuntos de la asignatura.

**Estado a 12/10/2026 (rama `javier-saguar`):** `data_aug.ipynb` está reescrito y ejecutado con las 808 imágenes. Propone el reparto por vídeos (T18), justifica doce transformaciones y descarta siete, genera `data_train/` (483 originales y 1449 copias), `data_val/` y `data_test/`, y comprueba el resultado. Figuras y tablas en [`resultados_aug/`](ENTREGA%201/WEEK1/resultados_aug/README.md). **Falta** repetirlo tras la depuración (T13), ejecutarlo una vez en JupyterHub y acordar en grupo el reparto y las transformaciones.

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
  **Estado a 14/10/2026:** la asignatura ha dado conjuntos de validación y test anotados por otros grupos (`ENTREGA 1/WEEK2/DATOS_ASIGNATURA/`, 672 y 718 imágenes con `.xml`). Por decisión de Javier, se entrena con nuestros diez vídeos y se valida y mide con esos conjuntos; `data_aug.ipynb` lo aplica y lo justifica en su sección 1. Ya no hace falta acordar un reparto de nuestros vídeos.
- **T19:** primer entrenamiento con `train.ipynb` (`faster_rcnn_v1`) en el entorno GPU de JupyterHub.
- **T20:** evaluar con `test.ipynb` (mAP y resultados cualitativos).

**Estado de T19 y T20 a 14/10/2026 (rama `alejandro-cuevas`):** los dos notebooks están
adaptados y **sin ejecutar**.

- `train.ipynb` elige el mejor modelo por el mAP de validación, calcula ese mAP en cada
  época, entrena con o sin las copias `-aug` (`usar_aumento`) y separa los experimentos
  en `models/<experimento>/`. Antes de entrenar comprueba que no falten imágenes, que no
  haya cajas no válidas y que ningún vídeo esté en dos conjuntos. Guarda el historial
  en `resultados_train/`.
- `test.ipynb` da el mAP con y sin los `difficult` y por vídeo, cuenta aciertos,
  detecciones falsas y robots perdidos con el umbral de confianza, dibuja la curva de
  precisión y exhaustividad según el umbral, mide el tiempo por imagen y guarda las
  imágenes con más errores en `resultados_test/`. Con `conjunto = 'val'` evalúa en
  validación, que es donde se ajusta; test se mira una sola vez al final.

**Hecha cuando:** hay un modelo entrenado en JupyterHub con su historial, el mAP en
test con su interpretación, y la comparación con y sin aumento.
