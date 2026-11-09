# Informes sobre la plantilla oficial

Contenido actualizado el **09/11/2026**.

| Documento | Contenido |
|---|---|
| [`informe_entrega3.docx`](informe_entrega3.docx) | **Borrador de la memoria de la entrega 3**: la de la entrega 2 más el Bloque 3 (apartados 13 a 17), creada con `herramientas/generar_entrega3.py` a partir de [`../informe_bloque3_borrador.md`](../informe_bloque3_borrador.md). Incluye las correcciones de la revisión de la entrega 2 (`herramientas/correcciones_entrega2.py`). Lo marcado en amarillo como [PENDIENTE] falta por medir o decidir. Ahora tiene 44 páginas, 30 de cuerpo (de la 4 a la 33); el límite de la entrega 3 es 30 (Bloques 1 a 3, sin portada, índice, respuesta a la revisión, reparto, referencias ni anexos). Se entrega como `PIDS_grupo2_entrega3.pdf`. |
| [`informe_entrega2.docx`](informe_entrega2.docx) | **Memoria de la entrega 2**: Bloque 1 corregido según la revisión de la entrega 1, con la tabla de respuesta a la revisión, y Bloque 2 completo con anexos. El PDF para subir es `docs/entregas/PIDS_grupo2_entrega2.pdf` (34 páginas, 20 de cuerpo, de la 4 a la 23; el límite es 20). |
| [`informe_fase1.docx`](informe_fase1.docx) | Fuente de la memoria de la entrega 1 (Bloque 1), base de `generar_entrega2.py`. El PDF entregado está en `docs/entregas/PIDS_grupo2_entrega1.pdf` y difiere en algo de redacción. |
| `figuras/` | Figuras de maquetación que no están en `ENTREGA 1/WEEK1/` ni en `WEEK2/`, incluidas las añadidas por la revisión. |

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

## Entrega 3: borrador del Bloque 3

El texto del Bloque 3 se escribe en `docs/informe_bloque3_borrador.md`, que se puede revisar en las PR.
`herramientas/generar_entrega3.py` copia `informe_entrega2.docx` (que no se toca) y le añade:
- en la portada, «Fases 1, 2 y 3» y «Entrega 3 · Bloques 1, 2 y 3», con la fecha pendiente;
- el borrador antes de «Referencias», con los mismos estilos de títulos, pies, tablas y figuras;
- la referencia [21] al estudio del robot camuflado (`docs/senuelo_aliado.md`).

Tablas y figuras nuevas llevan el prefijo B3 (Tabla B3.1, Figura B3.1) hasta numerar toda la memoria al
cerrarla. El script no sobrescribe el `.docx` sin `--forzar`: cuando se empiece a editar a mano en Word, los
cambios del borrador se pasan a mano. Después de generarlo, actualizar el índice (F9).

## Historial

**09/11/2026** — correcciones de la revisión de la entrega 2 y borrador de la presentación:
- `herramientas/correcciones_entrega2.py`, llamado desde `generar_entrega3.py`, responde a los comentarios
  obligatorios C2.1 a C2.8 y a los opcionales sobre los Bloques 1 y 2, sin tocar `informe_entrega2.docx`.
  También cambia la Figura 9 por un esquema de bloques (`figuras/sistema_entrenamiento.png`) y añade la curva
  precisión-exhaustividad en test como Figura 10 (`figuras/curva_pr.png`); las dos salen de
  `herramientas/figuras_revision_entrega2.py`. Además pasa las tasas a notación científica, añade la columna
  del Bloque 3 al reparto, las referencias [22] a [28] y la tabla de respuesta a la revisión de la entrega 2.
- El cuerpo ocupa ahora las 30 páginas del límite: cualquier texto nuevo del Bloque 3 tiene que compensarse.
- Borrador de la presentación de las tres fases en `presentacion/` (React), con las cifras y las imágenes de
  esta memoria; ver su README.

**08/11/2026** — el rival 2 se mueve en paralelo a nuestro robot durante la rotonda:
- nuevo texto en el apartado 15.2 (imagen nítida, velocidad prevista y parada de nuestro robot);
- la Figura B3.1 lleva la longitud y la velocidad de cada tramo, dónde va cada rival y a qué
  distancia queda;
- el rival 3 pasa a (5,35; −0,7): en (5,0; −0,7) chocaba con la rotonda.

**06/11/2026** — borrador de la entrega 3: Bloque 3 (integración en el robot, circuito, puntería y
disparo, ataque en marcha, robot camuflado y aliados, pruebas), con la Figura B3.1
(`figuras/circuito_demo.png`, de `herramientas/figura_circuito.py`) y las imágenes del estudio del
señuelo (`figuras/senuelo/`).

**03/11/2026** — métricas de test de todos los modelos y fecha de entrega:
- El Anexo E (ahora «Métricas de test») añade las Tablas 26 y 27 con los siete modelos y, para cada uno, todos,
  normales y difficult: AP 0,50:0,95, AP@0,5, AP@0,75, AP por tamaño, AR@100, TP, FP, FN, TN, precisión,
  exhaustividad, F1 y exactitud. TN = 0 porque en detección el fondo no se cuenta y el test no tiene imágenes sin
  robots; la exactitud queda en TP/(TP+FP+FN). FP, precisión, F1 y exactitud solo se dan para todos los robots.
- Los datos están en `ENTREGA 1/WEEK2/cadena/metricas_test_modelos.csv`. Los de cinco modelos se copiaron de
  `~/pids_main/ENTREGA 1/WEEK2/resultados_test/<experimento>_test/` en el laboratorio y se comprobaron con la
  huella sha256 de cada `map.csv` y de la fila `Total` de `errores_por_video.csv`; no se ha vuelto a evaluar nada.
- La tabla de respuesta a la revisión pasa a ser la Tabla 28.
- Fecha de entrega de la portada: 03/11/2026.

**02/11/2026** — números de test en el apartado de métricas:
- El apartado 10 da, para el modelo final en test, los TP, FP y FN, la precisión, la exhaustividad, el F1, la AP@0,5,
  la AP@0,75 y la AP 0,50:0,95. El nuevo Anexo E desglosa esas métricas en robots normales y difficult, añade la AP
  por tamaño y la AR@100 (Tabla 24) y muestra el efecto del umbral de confianza (Tabla 25). Los datos salen de
  `ENTREGA 1/WEEK2/resultados_test/faster_rcnn_v2_aug_robusto_v1_lr001_test/`; no se ha vuelto a evaluar nada.
- La tabla de respuesta a la revisión pasa a ser la Tabla 26.
- Para seguir en 20 páginas de cuerpo se han reducido las Figuras 14 a 17 y acortado el párrafo de pruebas sin
  aumento del 11.3 y las cifras del 11.6 que ya están en el apartado 10; el detalle sigue en los Anexos D y E.

**01/11/2026 (segunda tanda)** — lo que el enunciado pedía y faltaba:
- Pruebas cortas del orden de los experimentos (siete arquitecturas sin aumento), del lote (1, 2, 8, 16 y 32) y de
  la tasa de aprendizaje (1e−5, 0,001, 0,01 y 0,1), solo en validación. Resultados en `docs/pruebas_cortas.md` y en
  el nuevo Anexo D de la memoria; las ejecuta `herramientas/pruebas_cortas.py`. Un párrafo nuevo al final del 11.3
  los resume y el 9 enlaza con él.
- Tablas reenumeradas por orden de aparición (la de respuesta a la revisión queda al final, como Tabla 24) y los
  pies de las figuras interactivas enlazan con su fila del Anexo A.
- EDA: análisis de nitidez y dificultad (dentro de cada vídeo, el 55 % de las cajas de las imágenes menos nítidas
  son difficult, frente al 11 % en las más nítidas) con la Figura 21 en el Anexo C
  (`figuras/nitidez_dificultad.png`, de `herramientas/figura_nitidez.py` sobre `metricas_imagenes.csv`), y una
  frase que remite al notebook del EDA para el resto de análisis.

**01/11/2026** — correcciones de la revisión de la entrega 1 (todas recogidas en la tabla «Respuesta a la
revisión anterior» del documento):
- Descripción del RoboMaster EP con figura (`figuras/robot_partes.png`) y referencias [19] DJI y [20] PASCAL VOC.
- Justificación del intervalo de 24 fotogramas con una tabla de redundancia para intervalos de 6 a 96.
- Sin nombres de variables, funciones ni experimentos internos en el texto.
- EDA ampliado: tamaño frente a posición, solapamiento frente a la NMS y comparación con validación y test
  (4.4 y 4.5), y tabla de consecuencias para el entrenamiento (4.6).
- Tablas de aumento con rango y probabilidad por separado; justificación del desplazamiento RGB.
- Anexos: A (enlaces a todas las gráficas interactivas), B (transformaciones descartadas) y C (figuras
  complementarias). Nuevo apartado 11.5 con SSD300 a 40 épocas.

Figuras y datos nuevos: `herramientas/analisis_revision.py` (intervalo, dominio y perspectiva; necesita los
vídeos de `DATASET PIDS`), `herramientas/figura_transformaciones.py` (entorno con Albumentations 1.4.18) y
`herramientas/figura_ssd300_40_epocas.py`. Se ejecutan con la ruta del repositorio y la carpeta (o, en el de SSD300, el PNG) de salida.
Las tareas del Bloque 2 de Mónica y Daniel en el reparto quedan marcadas para completar.

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
