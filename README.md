# PIDS – Proyecto 2: Sistema de detección de vehículos y conducción autónoma

Proyectos en Ingeniería de Datos y Sistemas (PIDS) · Universidad Politécnica de Madrid · Grupo de Tratamiento de Imágenes (GTI) · Curso 2026

## Equipo

| Miembro | Rama |
|---|---|
| Javier Saguar | `javier-saguar` |
| Alejandro Cuevas | `alejandro-cuevas` |
| Mónica Fernández | `monica-fernandez` |
| Pedro José Orrego | `pedro-orrego` |
| Daniel Naval | `daniel-naval` |

## Descripción del proyecto

A lo largo del proyecto desarrollamos una red neuronal para la detección de objetos en imágenes, concretamente de **RoboMasters** adversarios (robots DJI RoboMaster EP), y la integramos en el propio robot para que sea capaz de detectarlos y actuar en consecuencia. Se trabaja con PyTorch sobre un JupyterHub montado en los ordenadores del laboratorio.

El proyecto se divide en tres bloques, cada uno con un hito:

| Bloque | Contenido | Hito |
|---|---|---|
| 1 | Recolección, anotación, análisis y depuración de datos | Dataset de imágenes de RoboMasters anotadas con *bounding boxes* |
| 2 | Entrenamiento de redes neuronales (entrenamiento, validación, evaluación, ajuste de hiperparámetros) | Modelo entrenado para detectar RoboMasters |
| 3 | Integración de la red en el robot mediante el SDK de Python: recorrido con obstáculos fijos, seguimiento y detección/disparo a robots | *Demo* (circuito) |

### Bloque 1 (fase actual)

1. **Recolección:** grabar vídeo desde el RoboMaster (app RoboMaster, modo *Solo*) variando iluminación, oclusiones, fondo, posición/orientación de los adversarios, distancia y movimiento de cámara. Anotar duración, resolución y fps de cada vídeo.
2. **Extracción de fotogramas:** `video2frames.ipynb` (variable `INTERVAL`) → carpeta `data_train/videoX/{images,labels}`.
3. **Anotación:** `labelImg` en formato PascalVOC, una sola clase (`robot`), con criterios comunes acordados por todo el grupo (oclusión parcial, robots lejanos, cortados por el borde, etc.).
4. **Análisis exploratorio (EDA):** `eda.ipynb` más algún análisis adicional justificado.
5. **Aumento de datos:** `data_aug.ipynb` (albumentations); solo sobre datos originales, ajustando y justificando las transformaciones.
6. **Depuración:** revisar y corregir/eliminar imágenes o etiquetas defectuosas, explicando el criterio.

**Objetivos:** al menos ~800 imágenes anotadas, EDA, aumento de datos, depuración e informe del Bloque 1.

### Entregable

- Memoria **incremental** (3 entregas) sobre la plantilla `PIDS-template.docx`.
- Primera entrega: portada y Bloque 1 completo (máx. 10 páginas de cuerpo).
- Fichero único: `PIDS_grupoX_entregaN.pdf`.
- Se valora sobre todo la **justificación** de las decisiones, la interpretación crítica de resultados y la presentación.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `ENTREGA 1/WEEK1/DATASET PIDS/` | Vídeos grabados con el RoboMaster, un `.zip` por vídeo (`ROBOMASTER_VIDEO_01.zip` … `ROBOMASTER_VIDEO_10.zip`) |
| `ENTREGA 1/WEEK1/` | `video2frames.ipynb`, `eda.ipynb` y `data_aug.ipynb` (Bloque 1) |
| `ENTREGA 1/WEEK2/` | `train.ipynb` y `test.ipynb` (entrenamiento y evaluación) |
| `ENTREGA 1/WEEK1/ANOTACION/` | 808 originales en cinco lotes personales, manifiesto y 20 imágenes comunes de calibración |
| `docs/criterios_anotacion.md` | Criterios operativos v1; revisión colectiva y calibración pendientes |
| `docs/fichas_videos.md` | Fichas y revisión de variabilidad de los diez vídeos |
| `docs/revision_videos.csv` | Las 120 muestras inspeccionadas para las fichas |
| `herramientas/preparar_fotogramas.py` | Extracción reproducible desde los ZIP y comprobación de integridad |
| `herramientas/empaquetar_anotacion.py` | ZIP de un lote o del conjunto para importar a JupyterHub |
| `herramientas/revisar_anotaciones.py` | Validación de las etiquetas y acuerdo entre anotadores |
| `ESTADO.md` | Estado actual del proyecto y datos de los vídeos |
| `TAREAS.md` | Tareas por orden de prioridad y quién se encarga de cada una |
| `AGENTS.md` | Normas del repositorio (autoría, ramas y datos) |

## Cómo vamos a trabajar

### Ramas

- `main` es la rama por defecto y recoge el trabajo común del grupo.
- Cada miembro del equipo tiene su **propia rama personal** (ver tabla de arriba) y trabaja únicamente en ella.
- Los commits se hacen en la rama propia, con mensajes claros y en imperativo (p. ej. `Añade análisis de tamaño de bounding boxes`).
- La integración del trabajo de cada uno se hace mediante PR hacia `main`, con al menos una aprobación de otro integrante, conversaciones resueltas y nueva revisión si cambia el contenido. Se fusiona con *Create a merge commit*; `main` está protegida.

### Reparto del trabajo

Las tareas están en [`TAREAS.md`](TAREAS.md), ordenadas por prioridad. Cada integrante se asigna las que vaya a hacer escribiendo su nombre en la columna *Responsable*.

Las actualizaciones de `TAREAS.md` y `ESTADO.md` también se integran mediante PR. Usamos **Issues solo cuando hacen falta**: errores, bloqueos, decisiones por discutir o trabajo que abarque varias PRs o personas. Para cambios pequeños basta con el seguimiento en la PR. Las reglas completas están en [`AGENTS.md`](AGENTS.md).

Los [lotes de anotación](ENTREGA%201/WEEK1/ANOTACION/README.md) están preparados en `javier-saguar`: Javier (01–02, 157 imágenes), Alejandro (03–04, 158), Mónica (05–06, 168), Pedro (07–08, 179) y Daniel (09–10, 146). Antes de anotar los lotes, completar la [calibración común](ENTREGA%201/WEEK1/ANOTACION/calibracion/README.md). La extracción se ha ejecutado localmente; la importación a JupyterHub queda pendiente.

### Reglas prácticas

- En los commits solo figuran como autores los integrantes del grupo, sin coautores (ver [`AGENTS.md`](AGENTS.md)).
- Acordar los **criterios de anotación** antes de empezar a etiquetar; las anotaciones deben ser consistentes entre todos.
- Mantener siempre una **copia del dataset y del código**: JupyterHub no permite subir/eliminar carpetas desde el panel (usar `zip`/`unzip` y `rm -r` con cuidado).
- No actualizar el firmware del RoboMaster cuando la app lo pida.
- No apagar los ordenadores del laboratorio (JupyterHub); el servicio está deshabilitado por las mañanas en horas de docencia.
- No subir al repositorio datos pesados (vídeos, imágenes) sin acordarlo antes.
