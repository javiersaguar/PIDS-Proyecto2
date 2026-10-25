# Informes sobre la plantilla oficial

Contenido actualizado el **25/10/2026**.

| Documento | Contenido |
|---|---|
| [`informe_entrega2.docx`](informe_entrega2.docx) | **Memoria de la entrega 2**: Bloque 1 (redactado a mano) y Bloque 2 completo, sin tabla de respuesta a la revisión (no se recibieron comentarios). El PDF para subir es `docs/entregas/PIDS_grupo2_entrega2.pdf` (23 páginas, 19 de cuerpo; el límite es 20). |
| [`informe_fase1.docx`](informe_fase1.docx) | Fuente de la memoria de la entrega 1 (Bloque 1), base de `generar_entrega2.py`. El PDF entregado está en `docs/entregas/PIDS_grupo2_entrega1.pdf` y difiere en algo de redacción. |
| `figuras/` | Figuras de maquetación del Bloque 2 que no están en `ENTREGA 1/WEEK2/`. |

Se conserva Calibri 11, interlineado 1,15, geometría, cabecera y pie de la plantilla
(`docs/PIDS-template.docx`, que permanece sin modificar). Las figuras van incrustadas.

## Entrega 2: versión final editada a mano

`informe_entrega2.docx` partió de `herramientas/generar_entrega2.py` (Bloque 1 de `informe_fase1.docx` con la redacción del
PDF entregado, más el Bloque 2 de `generar_informes.py`), pero **la versión final se ha editado a mano en Word**.
Por eso el script ya no sobrescribe ese fichero: sin argumentos se niega, y con una ruta de salida genera una copia.
Los cambios posteriores se hacen en el `.docx`; después hay que actualizar el índice (F9) y exportar a PDF
como `docs/entregas/PIDS_grupo2_entrega2.pdf`.

`generar_informes.py` no genera nada sin argumentos. `fase1` y `completo` sobrescriben los
`.docx` con el texto del script; `informe_fase1.docx` tiene correcciones manuales (título,
numeración de figuras, apartados 5.1–5.5, referencias [6]–[8]) que el script no reproduce,
así que no se debe regenerar.

## Historial

**25/10/2026** — se comprueba si las doce épocas se quedaban cortas, tras el comentario de que había
infraajuste. No era así: SSD300 VGG16, la única que seguía mejorando al final, repetida con 40 épocas
(`cadena/resumen_largo.csv`, acción `largo`) pasa de 0,9008 a 0,9009 de AP@0,5 y la pérdida de
validación sube mientras la de entrenamiento baja. Se corrigen en `informe_entrega2.docx` (a mano, sin
regenerarlo) la tabla de hiperparámetros («30 épocas»), el párrafo de épocas, la frase sobre SSD300 y la
de la tasa 0,002 («entrenamiento insuficiente», que era inestabilidad y sobreajuste). El PDF se
exporta de nuevo y sigue en 23 páginas.

**24/10/2026** — cadena de entrenamientos y test (detalle en `ENTREGA 1/WEEK2/cadena/`):
siete arquitecturas con lr 0,001 y perfil `robusto_v1`, tres tasas con las tres mejores y
test evaluado una sola vez por modelo con el umbral fijado antes en validación
(`docs/seleccion_modelo_final.md`). Modelo final: `faster_rcnn_v2`, AP@0,5 de 0,9523 en test
y F1 de 0,9389 con umbral 0,95. Opción rápida: `faster_rcnn_v3`, 0,9240 en test y 16,0 ms
por imagen frente a 96,3.

**20/10/2026** — `informe_fase1.docx`, editado a mano: fecha de entrega, reparto del trabajo
acordado, «2. Recolección de datos» como encabezado de primer nivel, «Tabla 9» en la
depuración y referencia [9] a `video2frames.ipynb`. A Moodle se subió solo el PDF
`PIDS_grupo2_entrega1.pdf`.

**19/10/2026** — enlaces a los notebooks ejecutados (`eda.html`, `data_aug.html`, generados
con `jupyter nbconvert --to html --embed-images`; no se usa nbviewer.org porque falla por el
límite de la API de GitHub) y a las figuras interactivas de GitHub Pages.

**Hasta el 16/10/2026** — experimentos `lr001` y `res1024`, curvas, secuencias, umbral de
confianza y latencia; anotación incompleta confirmada en `PIDS2024_GR02_0001/frame_0444.jpg`.
