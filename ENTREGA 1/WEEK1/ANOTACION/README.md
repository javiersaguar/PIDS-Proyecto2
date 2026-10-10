# Fotogramas para anotar

**808 imágenes originales**, extraídas el 09/10/2026 a 1280×720, una por cada 24
fotogramas, sin transformaciones. JPEG con calidad 95: conversión desde el vídeo,
sin reducir resolución. Ocupan aproximadamente 120,7 MiB. Los veinte duplicados de
calibración no entran en ese total. El estado de cada lote está en su README.

| Lote / carpeta | Responsable | Vídeos | Imágenes |
|---|---|---|---:|
| [A_javier-saguar](A_javier-saguar/) | Javier Saguar | 01, 02 | 157 |
| [B_alejandro-cuevas](B_alejandro-cuevas/) | Alejandro Cuevas | 03, 04 | 158 |
| [C_monica-fernandez](C_monica-fernandez/) | Mónica Fernández | 05, 06 | 168 |
| [D_pedro-orrego](D_pedro-orrego/) | Pedro José Orrego | 07, 08 | 179 |
| [E_daniel-naval](E_daniel-naval/) | Daniel Naval | 09, 10 | 146 |

Cada lote contiene dos secuencias, y cada secuencia tiene `images/` y `labels/`:

```
A_javier-saguar/
├── ROBOMASTER_VIDEO_01/
│   ├── images/frame_0024.jpg ... frame_1968.jpg
│   └── labels/.gitkeep
└── ROBOMASTER_VIDEO_02/
    ├── images/frame_0024.jpg ... frame_1800.jpg
    └── labels/.gitkeep
```

`.gitkeep` conserva las carpetas vacías en Git; **no es una etiqueta**. No se han
creado XML vacíos para imágenes sin revisar. Después de revisar una imagen sin
robots, guárdala en PascalVOC sin objetos y comprueba que existe su XML.

## Cómo anotar

**Guía paso a paso (configuración, reglas y errores comunes): [`docs/guia_anotacion.md`](../../../docs/guia_anotacion.md).**

1. Completar primero la [calibración común](calibracion/README.md).
2. Leer los [criterios de anotación](../../../docs/criterios_anotacion.md).
3. En labelImg: `Open Dir` en `images/` de un vídeo y `Change Save Dir` en su
   `labels/`. Activar PascalVOC, `Single Class Mode`, clase `robot` y guardado automático.
4. Revisar todas las imágenes, incluidos los negativos. Mantener nombres y originales.
5. Validar el lote desde la raíz del repositorio, por ejemplo:

```bash
python herramientas/revisar_anotaciones.py validar "ENTREGA 1/WEEK1/ANOTACION/A_javier-saguar"
```

Cada integrante sube sus XML en su rama personal; se conserva esta estructura al
integrar. `TAREAS.md` contiene las asignaciones. Una asignación no significa que la
persona haya empezado ni terminado la anotación.

## Descargar y llevar al laboratorio

Los originales están en la rama **javier-saguar**. Se puede clonar esa rama o usar
`Code → Download ZIP` en GitHub. Cada carpeta de lote contiene lo necesario para
anotar sus dos vídeos.

Para generar un ZIP compacto con las diez secuencias directamente dentro de
`data_train/`, sin la capa de lotes:

```bash
python herramientas/empaquetar_anotacion.py ../fotogramas_pids.zip
```

Para empaquetar solo un lote:

```bash
python herramientas/empaquetar_anotacion.py ../lote_A.zip --lote A_javier-saguar
```

Subir ese ZIP a `/workspace` en JupyterHub y descomprimirlo **en un destino vacío**;
evitar sustituir un dataset que ya tenga anotaciones. El resultado es
`/workspace/data_train/ROBOMASTER_VIDEO_XX/{images,labels}`. El script incluye los XML
existentes al empaquetar. La subida a JupyterHub queda pendiente; la extracción se
ha ejecutado localmente. Para EDA/aumento usar `PATH_DATA = '/workspace/data_train'`.

## Procedencia y reproducción

- `manifest.csv`: 808 filas con lote, responsable, vídeo, índice del fotograma,
  segundo aproximado, ruta, bytes y SHA-256 de cada imagen.
- `videos.json`: metadatos medidos, SHA-256 de los ZIP originales, intervalo,
  calidad JPEG y versión de OpenCV.
- El índice es **desde 1**: se guardan 24, 48, 72… y el tiempo nominal es
  `(frame - 1) / fps`. No es una medición exacta de cada timestamp del contenedor.
- El recuento es `sum(floor(fotogramas_del_video / 24)) = 808`, no 813.
- Reproducir en una carpeta nueva (el extractor rechaza destinos existentes):

```bash
python herramientas/preparar_fotogramas.py --destino ../fotogramas_reproducidos
```

`video2frames.ipynb` usa el mismo extractor y comprueba la integridad si ya existe
el dataset. Los hashes JPEG pueden cambiar con otra versión del codificador.
