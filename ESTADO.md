# Estado del proyecto

Última actualización: 14/10/2026, desde la rama `javier-saguar`.

**Fase actual:** Bloque 1 (recolección, anotación, análisis y depuración de datos), de cara a la **primera entrega** de la memoria. **Bloque 1 terminado salvo los acuerdos de grupo (T01, T18)**: 808 imágenes anotadas y revisadas, 796 tras la depuración, con EDA y aumento hechos. Los datos están listos para entrenar en JupyterHub.

Las tareas pendientes, por orden de prioridad y con su responsable, están en [`TAREAS.md`](TAREAS.md).

## Resumen

| Bloque | Estado | Hito |
|---|---|---|
| 1. Datos | 808 imágenes anotadas y revisadas, 796 tras la depuración; falta cerrar T01 en grupo | Dataset de ~800 imágenes anotadas |
| 2. Entrenamiento | En preparación: `train.ipynb` y `test.ipynb` adaptados, sin ejecutar (T19, T20) | Modelo que detecta RoboMasters |
| 3. Integración en el robot | Sin empezar | *Demo* en circuito |

## Hecho

- Repositorio montado: `main` como rama por defecto y una rama personal por integrante. Se trabaja con PRs revisadas por otro integrante.
- Grabados **10 vídeos** con el RoboMaster (`ENTREGA 1/WEEK1/DATASET PIDS/`, un `.zip` por vídeo).
- T02: fichas de los vídeos y revisión de variabilidad en [`docs/fichas_videos.md`](docs/fichas_videos.md).
- T03: **808 JPEG a 1280×720** extraídos con `INTERVAL = 24` y repartidos en cinco lotes.
- T04–T08: **los cinco lotes anotados**, con 1420 robots. T10: revisión cruzada de todos los lotes.
- T01: criterios v1 en [`docs/criterios_anotacion.md`](docs/criterios_anotacion.md), guía práctica en [`docs/guia_anotacion.md`](docs/guia_anotacion.md) y calibración de los cinco: IoU medio de 0,81 entre anotadores.
- T11–T12: EDA completo en `eda.ipynb`, con figuras y tablas en `ENTREGA 1/WEEK1/resultados_eda/`.
- T13: depuración. Se excluyen 12 imágenes (una con un robot sin caja y 11 casi duplicadas) y quedan **796**. Criterios en [`docs/depuracion.md`](docs/depuracion.md).
- T14 y T18: `data_aug.ipynb` genera **3184 imágenes de entrenamiento** (nuestras 796 y 2388 copias). Validación (672) y test (718) son los conjuntos de otros grupos que da la asignatura, en `ENTREGA 1/WEEK2/DATOS_ASIGNATURA/`. Figuras en `ENTREGA 1/WEEK1/resultados_aug/`.
- Bloque 3: material de la semana 3 en `ENTREGA 2/WEEK3/` (SDK del robot y demo por completar).
- T09: los originales y sus etiquetas están versionados en `main`, que es la copia de seguridad.

## Datos de los vídeos

Medidos con OpenCV sobre los ficheros subidos. La memoria pide duración, resolución y fps de cada vídeo.

| Vídeo | Duración (s) | Resolución | FPS | Fotogramas |
|---|---|---|---|---|
| ROBOMASTER_VIDEO_01 | 65,4 | 1280x720 | 30,30 | 1982 |
| ROBOMASTER_VIDEO_02 | 59,9 | 1280x720 | 30,30 | 1815 |
| ROBOMASTER_VIDEO_03 | 60,2 | 1280x720 | 30,30 | 1823 |
| ROBOMASTER_VIDEO_04 | 66,1 | 1280x720 | 30,30 | 2003 |
| ROBOMASTER_VIDEO_05 | 59,6 | 1280x720 | 30,30 | 1807 |
| ROBOMASTER_VIDEO_06 | 74,1 | 1280x720 | 30,30 | 2244 |
| ROBOMASTER_VIDEO_07 | 61,2 | 1280x720 | 30,30 | 1855 |
| ROBOMASTER_VIDEO_08 | 81,2 | 1280x720 | 30,30 | 2460 |
| ROBOMASTER_VIDEO_09 | 56,2 | 1280x720 | 30,30 | 1704 |
| ROBOMASTER_VIDEO_10 | 59,9 | 1280x720 | 30,30 | 1815 |
| **Total** | **643,8 (10 min 44 s)** | | | **19 508** |

**`INTERVAL` utilizado: 24.** Se guardan los fotogramas 24, 48, 72… de cada vídeo, numerados desde 1. El resultado exacto es `sum(floor(n_frames / 24)) = 808`, no 813: hay que descontar el resto de cada vídeo. Con 20 serían 972 y con 30, 645, usando el mismo código.

| Vídeo | Imágenes extraídas | Lote | Responsable |
|---|---:|---|---|
| ROBOMASTER_VIDEO_01 | 82 | A | Javier Saguar |
| ROBOMASTER_VIDEO_02 | 75 | A | Javier Saguar |
| ROBOMASTER_VIDEO_03 | 75 | B | Alejandro Cuevas |
| ROBOMASTER_VIDEO_04 | 83 | B | Alejandro Cuevas |
| ROBOMASTER_VIDEO_05 | 75 | C | Mónica Fernández |
| ROBOMASTER_VIDEO_06 | 93 | C | Mónica Fernández |
| ROBOMASTER_VIDEO_07 | 77 | D | Pedro José Orrego |
| ROBOMASTER_VIDEO_08 | 102 | D | Pedro José Orrego |
| ROBOMASTER_VIDEO_09 | 71 | E | Daniel Naval |
| ROBOMASTER_VIDEO_10 | 75 | E | Daniel Naval |
| **Total** | **808** | | |

Las fichas por vídeo (escenario, interior/exterior, iluminación, oclusiones, número visible de robots, distancia aparente, orientación y movimiento de cámara) están en [`docs/fichas_videos.md`](docs/fichas_videos.md). Se revisaron doce muestras por secuencia; no es una anotación exhaustiva ni se miden distancias en metros.

**Decisión de T02:** la variabilidad permite empezar la anotación sin repetir ahora un escenario. Reservar una grabación complementaria para reponer originales si la depuración deja menos de 800; para el Bloque 3 añadir secuencias del circuito real y de sus obstáculos. Las limitaciones y justificación están en las fichas.

## Pendiente antes de entrenar

- **T01:** cerrar los criterios en grupo. El borde superior del robot (gimbal y antenas) es donde más discrepamos.
- **T03:** en JupyterHub, instalar `albumentations` y `pycocotools`, generar los datos y lanzar el entrenamiento, siguiendo [`docs/jupyterhub.md`](docs/jupyterhub.md).

Después vienen el entrenamiento y la evaluación (T19, T20) y la memoria (T15–T17).

## Por confirmar

- Número de grupo (usuario `pidsX` de JupyterHub y nombre del PDF `PIDS_grupoX_entrega1.pdf`).
- Fecha de la primera entrega.

## Riesgos

- **Anotaciones inconsistentes entre nosotros.** Por eso los criterios comunes (T01) van antes que nada.
- **Justos de imágenes:** quedan 796 tras depurar, cuatro por debajo de las ~800 del objetivo. Si hace falta, hay prevista una grabación complementaria (T02).
- **Criterios distintos en validación y test:** los anotaron otros grupos, sin `difficult` y quizá con otro criterio para antenas y robots cortados. Parte del error medido puede venir de ahí.
- **Filtración entre conjuntos:** separar por secuencia y mantener sus aumentos en el mismo conjunto. Excluir las copias de calibración del entrenamiento como muestras adicionales.
- **Perder datos en JupyterHub.** No se pueden borrar carpetas desde el panel y `rm -r` no tiene vuelta atrás. Las etiquetas están a salvo en `main` y `data_aug.ipynb` regenera el resto.
- **Que el JupyterHub no esté disponible.** El servicio está deshabilitado por las mañanas en horas de docencia.
- **No llegar al hito del Bloque 1.** Si no lo conseguimos, los profesores nos dan el dataset, pero con penalización en la nota.
