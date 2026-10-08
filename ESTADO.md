# Estado del proyecto

Última actualización: 08/10/2026.

**Fase actual:** Bloque 1 (recolección, anotación, análisis y depuración de datos), de cara a la **primera entrega** de la memoria.

Las tareas pendientes, por orden de prioridad y con su responsable, están en [`TAREAS.md`](TAREAS.md).

## Resumen

| Bloque | Estado | Hito |
|---|---|---|
| 1. Datos | En curso: vídeos grabados, falta todo lo demás | Dataset de ~800 imágenes anotadas |
| 2. Entrenamiento | Sin empezar (los notebooks base ya están en `ENTREGA 1/WEEK2/`) | Modelo que detecta RoboMasters |
| 3. Integración en el robot | Sin empezar | *Demo* en circuito |

## Hecho

- Repositorio montado: `main` como rama por defecto y una rama personal por integrante.
- Grabados **10 vídeos** con el RoboMaster (`ENTREGA 1/WEEK1/DATASET PIDS/`, un `.zip` por vídeo).
- Subidos los notebooks base de la asignatura (`video2frames`, `eda`, `data_aug`, `train` y `test`). **Todavía no se han adaptado ni ejecutado con nuestros datos**: las salidas que traen son las del ejemplo de los profesores.

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

**`INTERVAL` recomendado: 24.** Con 19 508 fotogramas salen unas 813 imágenes, justo por encima de las ~800 que piden. Con 20 serían ~975 y con 30, ~650.

Falta anotar en la tabla de arriba el escenario y las condiciones de cada vídeo (lugar, iluminación, oclusiones, distancia, movimiento de cámara). Es la tarea T02 de [`TAREAS.md`](TAREAS.md).

## Por confirmar

- Número de grupo (usuario `pidsX` de JupyterHub y nombre del PDF `PIDS_grupoX_entrega1.pdf`).
- Fecha de la primera entrega.
- Dónde guardamos la copia de seguridad del dataset anotado (Drive, OneDrive…).

## Riesgos

- **Anotaciones inconsistentes entre nosotros.** Por eso los criterios comunes (T01) van antes que nada.
- **Perder datos en JupyterHub.** No se pueden borrar carpetas desde el panel y `rm -r` no tiene vuelta atrás: hay que hacer una copia (T09) en cuanto esté anotado.
- **Que el JupyterHub no esté disponible.** El servicio está deshabilitado por las mañanas en horas de docencia.
- **No llegar al hito del Bloque 1.** Si no lo conseguimos, los profesores nos dan el dataset, pero con penalización en la nota.
