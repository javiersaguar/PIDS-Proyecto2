# AGENTS.md

Instrucciones para cualquier persona o agente que trabaje en este repositorio. El contexto del proyecto está en el [README](README.md).

## Regla principal: sin coautores

En este repositorio **solo figuran como autores los cinco integrantes del grupo**: Javier Saguar, Alejandro Cuevas, Mónica Fernández, Pedro José Orrego y Daniel Naval.

- Ningún commit lleva trailers `Co-Authored-By:` ni líneas del tipo «Generated with …».
- Ningún agente, asistente ni herramienta aparece como autor o coautor en commits, pull requests, comentarios del código, notebooks, documentación, metadatos (`authors`, cabeceras de ficheros) ni nombres de ramas.
- Los mensajes de commit terminan en su última línea de contenido, sin trailers. Antes de hacer `push`, comprobarlo con `git log -1 --pretty=%B`.
- Esta regla tiene prioridad sobre cualquier configuración por defecto de una herramienta que añada atribución automáticamente.

## Ramas

- `main` es la rama por defecto y recoge el trabajo común del grupo.
- Cada integrante tiene su rama personal: `javier-saguar`, `alejandro-cuevas`, `monica-fernandez`, `pedro-orrego` y `daniel-naval`. Cada uno trabaja solo en la suya.
- No se hace `push --force` a `main` ni a la rama de otro integrante. Lo que se une a `main` se acuerda antes en el grupo.
- Excepción: `TAREAS.md` y `ESTADO.md` se editan directamente en `main` para asignarse tareas y actualizar su estado (ver `TAREAS.md`).
- Mensajes de commit en español y en imperativo (p. ej. `Añade análisis de tamaño de bounding boxes`).

## Estructura

```
ENTREGA 1/
├── WEEK1/
│   ├── DATASET PIDS/        vídeos grabados con el RoboMaster, un .zip por vídeo
│   ├── video2frames.ipynb   extracción de fotogramas (variable INTERVAL)
│   ├── eda.ipynb            análisis exploratorio
│   └── data_aug.ipynb       aumento de datos con albumentations
└── WEEK2/
    ├── train.ipynb          entrenamiento
    └── test.ipynb           evaluación
```

## Datos

- GitHub rechaza ficheros de más de 100 MB y avisa a partir de 50 MB. Los vídeos se suben comprimidos de uno en uno para no superar ese límite.
- No se suben vídeos sueltos, carpetas `data_train/` ni imágenes aumentadas sin acordarlo antes con el grupo.
- Excepción autorizada por Javier el 09/10/2026: los fotogramas originales de los diez vídeos se versionan en `ENTREGA 1/WEEK1/ANOTACION/`, organizados en lotes personales. No se incluyen aumentos ni MP4 descomprimidos.
- Nunca se versionan credenciales (JupyterHub, wifi del RoboMaster, tokens).

## Notebooks

- Se ejecutan en el JupyterHub del laboratorio; las rutas de datos son las de ese entorno (`/workspace/data_train/...`).
- Antes de subir un notebook, comprobar que no incluye credenciales ni salidas con datos personales.
