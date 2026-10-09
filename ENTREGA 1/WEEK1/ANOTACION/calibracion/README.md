# Calibración común (T01)

Las veinte imágenes de `images/` son copias de originales ya incluidos en los lotes,
dos por vídeo. **No cuentan como otras veinte imágenes del dataset**. `seleccion.csv`
registra el original, el tiempo aproximado, el motivo y su SHA-256. El motivo orienta
la discusión; la caja se decide mirando la imagen, sin deducir partes del vídeo.

Cada integrante abre esta misma carpeta `images/` en labelImg y guarda los XML en
`<su-rama>/labels/`. Los nombres llevan el vídeo para evitar colisiones. No hay
etiquetas de referencia: cada persona hace su anotación por separado. Sigue los
[criterios](../../../../docs/criterios_anotacion.md), clase `robot`, PascalVOC.

Desde la raíz del repositorio, cuando estén los veinte XML de cada persona:

```bash
python herramientas/revisar_anotaciones.py acuerdo "ENTREGA 1/WEEK1/ANOTACION/calibracion/javier-saguar/labels" "ENTREGA 1/WEEK1/ANOTACION/calibracion/alejandro-cuevas/labels" "ENTREGA 1/WEEK1/ANOTACION/calibracion/monica-fernandez/labels" "ENTREGA 1/WEEK1/ANOTACION/calibracion/pedro-orrego/labels" "ENTREGA 1/WEEK1/ANOTACION/calibracion/daniel-naval/labels"
```

El script exige las mismas veinte imágenes como mínimo, IoU medio de cada pareja
≥ 0,80 y ningún robot sin emparejar a IoU ≥ 0,50. Las discrepancias se comentan y se
repite la ronda tras aclarar las reglas. **La calibración y el acuerdo del grupo
están pendientes; no hay un IoU medido todavía.**
