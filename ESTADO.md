# Estado del proyecto

Última actualización: 09/10/2026. Trabajo preparado en la rama `javier-saguar`.

**Fase actual:** Bloque 1 (recolección, anotación, análisis y depuración de datos), de cara a la **primera entrega** de la memoria.

Las tareas pendientes, por orden de prioridad y con su responsable, están en [`TAREAS.md`](TAREAS.md).

## Resumen

| Bloque | Estado | Hito |
|---|---|---|
| 1. Datos | Vídeos revisados y 808 originales extraídos en cinco lotes; anotación pendiente | Dataset de ~800 imágenes anotadas |
| 2. Entrenamiento | Sin empezar (los notebooks base ya están en `ENTREGA 1/WEEK2/`) | Modelo que detecta RoboMasters |
| 3. Integración en el robot | Sin empezar | *Demo* en circuito |

## Hecho

- Repositorio montado: `main` como rama por defecto y una rama personal por integrante.
- Grabados **10 vídeos** con el RoboMaster (`ENTREGA 1/WEEK1/DATASET PIDS/`, un `.zip` por vídeo).
- T02: metadatos comprobados y 120 muestras revisadas (doce por vídeo); fichas y revisión de variabilidad completas en [`docs/fichas_videos.md`](docs/fichas_videos.md).
- Extracción local: **808 JPEG a 1280×720**, calidad 95, intervalo 24 y sin transformaciones. Todos los fotogramas anunciados por cada vídeo se han decodificado. El manifiesto registra procedencia y SHA-256 por imagen.
- Cinco lotes asignados en [`ANOTACION/README.md`](ENTREGA%201/WEEK1/ANOTACION/README.md), con `images/` y `labels/` por vídeo. No hay XML todavía: falta anotar.
- T01: criterios operativos v1 revisados y veinte fotogramas comunes preparados. **Pendientes la revisión del grupo y las cinco anotaciones de calibración**; no se ha medido IoU ni se declara un acuerdo colectivo.
- `video2frames.ipynb` adaptado y ejecutado para comprobar el dataset extraído. EDA, aumento, entrenamiento y test siguen siendo ejemplos de los profesores.

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

## Pendiente para cerrar T01 y T03

- T01: revisión colectiva, anotación independiente de los veinte originales comunes por cada integrante y medición de IoU. Ver [`calibracion/README.md`](ENTREGA%201/WEEK1/ANOTACION/calibracion/README.md).
- T03: importar las secuencias en JupyterHub. La extracción local está completa y preparada para GitHub; no se ha accedido al laboratorio. `herramientas/empaquetar_anotacion.py` crea un ZIP listo para `/workspace/data_train/`. Importarlo en una carpeta vacía para conservar las etiquetas existentes.
- T04–T08: anotaciones de los lotes asignados. Una asignación no implica que la persona haya empezado.

## Por confirmar

- Número de grupo (usuario `pidsX` de JupyterHub y nombre del PDF `PIDS_grupoX_entrega1.pdf`).
- Fecha de la primera entrega.
- Dónde guardamos la copia de seguridad del dataset anotado (Drive, OneDrive…).

## Riesgos

- **Anotaciones inconsistentes entre nosotros.** Por eso los criterios comunes (T01) van antes que nada.
- **Poco margen para depurar:** 808 originales; complementar si se necesita. Las veinte copias de calibración no son imágenes nuevas.
- **Filtración entre conjuntos:** separar por secuencia y mantener sus aumentos en el mismo conjunto. Excluir las copias de calibración del entrenamiento como muestras adicionales.
- **Perder datos en JupyterHub.** No se pueden borrar carpetas desde el panel y `rm -r` no tiene vuelta atrás: hay que hacer una copia (T09) en cuanto esté anotado.
- **Que el JupyterHub no esté disponible.** El servicio está deshabilitado por las mañanas en horas de docencia.
- **No llegar al hito del Bloque 1.** Si no lo conseguimos, los profesores nos dan el dataset, pero con penalización en la nota.
