# Informes sobre la plantilla oficial

Contenido actualizado el **16/10/2026**, después de finalizar entrenamiento y
validación de `faster_rcnn_v1_aug_lr001_res1024`.

| Versión | Word editable | PDF | Contenido |
|---|---|---|---|
| Completa | [Word](informe_completo_fases_1_2.docx) | [PDF](informe_completo_fases_1_2.pdf) | Fases 1 y 2 con lo medido; conserva la estructura pendiente de fase 3 |
| Solo fase 1 | [Word](informe_fase1.docx) | [PDF](informe_fase1.pdf) | Datos, anotación, EDA, aumento y depuración; siete páginas de cuerpo |
| Solo fase 2 | [Word](informe_fase2.docx) | [PDF](informe_fase2.pdf) | Pipeline, modelo, hiperparámetros, métricas, experimentos y análisis cualitativo; diez páginas de cuerpo |

La copia de fase 2 es una extracción de trabajo solicitada para revisar ese bloque.
La segunda entrega oficial es **incremental** y debe incluir también la fase 1
corregida. Los PDF contienen 13, 14 y 23 páginas totales respectivamente para fase 1,
fase 2 y completa (portada, reparto, índice y referencias no cuentan como cuerpo).
Comprobar antes de entregar que el cuerpo sigue dentro del máximo de 10 páginas de T17.

Se conserva Calibri 11, interlineado 1,15, geometría, cabecera y pie de la plantilla.
Las figuras van incrustadas; no requieren archivos externos para abrir el Word.
El índice y la paginación se verifican en el PDF. En Word se pueden actualizar con
F9 si se cambia el contenido. La plantilla original permanece sin modificar.

**19/10/2026:** se añadieron hyperlinks reales (clicables) a los notebooks ejecutados
y a las figuras interactivas de GitHub Pages, editando los `.docx` directamente (no
con `generar_informes.py`, ver aviso debajo). Los notebooks se citan como una vista
HTML estática (`ENTREGA 1/WEEK1/eda.html` y `data_aug.html`, generados con
`jupyter nbconvert --to html --embed-images` y commiteados junto a los `.ipynb`),
abierta con `htmlpreview.github.io` — igual que ya se hace con los HTML del EDA en
`docs/plan_entrega.md` — porque **nbviewer.org no es fiable**: depende del límite de
peticiones de la API de GitHub, compartido entre todos sus usuarios, y falla con
"GitHub API rate limit" de forma intermitente:

- EDA ejecutado: https://htmlpreview.github.io/?https://github.com/javiersaguar/PIDS-Proyecto2/blob/main/ENTREGA%201/WEEK1/eda.html
- Aumento de datos ejecutado: https://htmlpreview.github.io/?https://github.com/javiersaguar/PIDS-Proyecto2/blob/main/ENTREGA%201/WEEK1/data_aug.html
- Figuras de EDA y de entrenamiento: anclas `#mapas-video`, `#mapas-tiempo`,
  `#robots-fotograma`, `#curvas`, `#grupos` y `#secuencias` en https://javiersaguar.github.io/PIDS-Proyecto2/

Si se regeneran los notebooks, hay que volver a exportarlos con el mismo comando y
commitear los `.html` de nuevo; no se generan solos.

## Aviso: `informe_fase1.docx` (y partes de la completa) ya no coincide con el generador

`informe_fase1.docx` tiene correcciones manuales en Word (título, numeración de
figuras, secciones 5.1–5.5, referencia [6] a la web) que **no están reflejadas en
`herramientas/generar_informes.py`**. Ejecutar ese script sobrescribe el `.docx`
entero con su propio texto y **borra esas correcciones**, que no se recuperan salvo
con `git checkout` a un commit anterior. `informe_fase2.docx` sí coincide con el
script. Antes de volver a generar nada, comprobar con `git diff` si el `.docx` que se
va a sobrescribir tiene cambios que el script no reproduce; si los tiene, hay que
llevar esos mismos cambios al script primero, o editar el `.docx` a mano.

También se proporcionan [versión Markdown completa](informe_completo_fases_1_2.md),
[fase 1](informe_fase1.md) y [fase 2](informe_fase2.md), para revisar diferencias en Git.

## Resultados incorporados

- `lr001`: mejor época 5, AP@0,5 de 0,9433 y AP 0,50:0,95 de 0,6302 en evaluación
  final de validación. AP@0,5 de difficult 0,6462; 190 FP y 83 FN a confianza 0,5.
- `res1024`: mejor época por AP50 2; AP50 0,9465, AP 0,50:0,95 0,6047,
  AP small 0,1886, AP50 difficult 0,6282, 324 FP y 68 FN (56 difficult).
- Curvas de resolución, selección del checkpoint, secuencias y latencia individual
  121,6 ms frente a 75,1 ms. Se documenta microbatch 4 con acumulación 2.
- La referencia provisional sigue siendo lr001 800 por su equilibrio; no se presenta
  la mayor resolución como una mejora uniforme. Se distingue AP50 de AP promedio.
- Curvas comparadas, cambios por secuencia, búsqueda del umbral y latencia.
- Anotación incompleta confirmada en `PIDS2024_GR02_0001/frame_0444.jpg`:
  cuatro robots visibles y una sola caja XML. No se alteran esas etiquetas.
- Perfiles nuevos de aumento distinguidos de los resultados del aumento base.

La fase 2 **no está cerrada**: falta comparar arquitecturas y evaluar el modelo
definitivo en test. La resolución ya está medida; lluvia, sombras y oclusión
texturada siguen pendientes de entrenamiento. Falta confirmar fecha de entrega, número
administrativo del grupo y reparto final con todos los integrantes.

## Regeneración

Con `python-docx`, `lxml`, Pillow y las figuras disponibles:

```bash
python herramientas/comparar_entrenamientos.py
python herramientas/comparar_resolucion.py
python herramientas/generar_informes.py
```

El último comando crea las tres copias Word y Markdown; no sobreescribe la
plantilla ni exporta por sí solo PDF. Para obtener los PDF, actualizar los campos
y exportar desde Word, comprobando otra vez todas las páginas. Las figuras
específicas de maquetación están en `figuras/`; las curvas y los resultados del
laboratorio conservan sus rutas en `ENTREGA 1/WEEK2/`.
