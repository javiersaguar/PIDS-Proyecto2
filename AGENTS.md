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
- Los cambios se suben a la rama personal y se integran en `main` mediante una **pull request (PR)**. Esto también se aplica a `TAREAS.md` y `ESTADO.md`; sustituye la indicación anterior de editarlos directamente en `main`.
- Mensajes de commit en español y en imperativo (p. ej. `Añade análisis de tamaño de bounding boxes`).

## Pull requests y seguimiento del trabajo

Trabajamos con PRs para conservar el hilo de las tareas, las decisiones y las revisiones.

- Abrir una PR desde la rama personal hacia `main` por cada tarea o conjunto coherente de tareas. Si el trabajo aún está en curso, abrirla como borrador.
- Escribir el título y la descripción en español. La descripción indica las tareas relacionadas (`T01`, `T02`…), el problema u objetivo, los cambios realizados, las comprobaciones y los pasos pendientes. No dar por terminada una tarea si falta trabajo del grupo o del laboratorio.
- Al continuar el mismo trabajo, añadir commits a su PR y actualizar la descripción para reflejar el estado actual. No abrir otra PR para duplicar una que sigue abierta.
- Registrar en la PR las decisiones y los resultados de la revisión. Mantener `TAREAS.md` y `ESTADO.md` coherentes con el trabajo e incluir enlaces a las PRs cuando ayuden a seguirlo.
- Fusionar cuando Javier lo solicite expresamente o el grupo acuerde la integración, una vez cumplidas las revisiones y la protección de `main`. Abrir una PR o terminar una tarea no autoriza por sí solo su fusión. No integrar directamente mediante `push` a `main` ni saltarse su protección.
- Al entregar el trabajo, indicar el enlace de la PR, qué se ha comprobado y cualquier pendiente. La regla de **sin coautores ni atribuciones a herramientas** también se aplica a las PRs.

## Protección de main y aprobación de PRs

- `main` exige PR y **una aprobación de otro integrante** con permisos de escritura. El autor pide revisión a un compañero; no puede aprobar su propia PR.
- Si se añaden nuevos commits que cambian el contenido revisado, se invalida la aprobación y se vuelve a revisar. Todas las conversaciones de revisión deben estar resueltas antes de fusionar.
- Para cambios importantes en criterios de anotación, dataset o modelo, pedir **dos revisiones** como acuerdo del grupo. El mínimo técnico de GitHub sigue siendo una aprobación; no presentar la segunda como un bloqueo automático.
- Una vez aprobado el trabajo y acordada su integración, el autor o un compañero puede fusionar con **Create a merge commit**, conservando los commits y el vínculo con la PR. Mantener las ramas personales para seguir trabajando.
- El borrado de `main` y el `push --force` están bloqueados. La protección se aplica también a administradores, sin actores con permiso para saltársela. No desactivar estas reglas para integrar una PR sin revisar.
- Se añadirán comprobaciones automáticas obligatorias cuando exista CI configurada. Por ahora, cada PR documenta las comprobaciones realizadas.
- La configuración de estas reglas está en [`docs/proteccion_main.json`](docs/proteccion_main.json). Es configuración de GitHub, no una protección que Git aplique por leer este archivo.

## Issues cuando sean necesarias

Usamos Issues para asuntos que requieren seguimiento propio: errores, bloqueos,
decisiones que necesitan discusión o tareas que abarcan varias PRs o personas.

- No es obligatorio abrir una Issue para cada cambio. Una corrección pequeña o una tarea ya clara puede seguirse directamente en su PR y en `TAREAS.md`.
- Antes de abrir una Issue, comprobar si ya existe una sobre el mismo asunto y continuar allí si corresponde. Evitar duplicar la lista de tareas sin aportar contexto.
- Describir el problema u objetivo, el contexto o pasos para reproducirlo, el resultado esperado y qué falta para darlo por resuelto. Indicar las tareas relacionadas y el responsable cuando esté acordado.
- Enlazar la Issue desde las PRs que trabajen en ella. Usar `Closes #N` solo si la PR resuelve todo el asunto; si deja pendientes, usar una referencia y mantener la Issue abierta.
- Conservar las decisiones y los avances en la Issue, y cerrarla cuando se cumpla lo acordado. Usar `TAREAS.md` y `ESTADO.md` como resumen general, con enlaces cuando sean útiles.

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
