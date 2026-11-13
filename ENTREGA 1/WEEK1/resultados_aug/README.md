# Resultados del aumento de datos

Figuras y tablas que genera [`data_aug.ipynb`](../data_aug.ipynb) (T14). Se
sobrescriben cada vez que se ejecuta el notebook, así que **no se editan a mano**.
Las cifras actuales corresponden a las etiquetas del 12/10/2026 **con la depuración
(T13) aplicada**: las 796 imágenes de nuestros diez vídeos son el entrenamiento, y
validación y test son los conjuntos de la asignatura.

Las imágenes aumentadas no están en el repositorio: el notebook las crea en
`data_train/`, `data_val/` y `data_test/`, en la raíz, que Git ignora. Son unos 810 MB.

## Ampliaciones experimentales (15/10)

La sección 9 del notebook añade perfiles optativos de sombras, oclusiones
texturadas, refuerzo de imágenes con `difficult` y lluvia suave. El perfil por
defecto sigue siendo `base`: **las cifras siguientes describen el aumento usado
en los entrenamientos existentes**, no una mejora medida de las ampliaciones.

Ver [configuración, ejemplos y comprobaciones](experimentos/README.md).
Los perfiles nuevos generan en `datasets_experimentos/<perfil>/` y guardan sus
resultados en `resultados_aug/<perfil>/`; no reemplazan los datos ni las figuras
del aumento base.

**Actualización (24/10):** la cadena de entrenamientos (`herramientas/cadena_entrenamientos.py`) usó el
perfil `robusto_v1` en sus 13 modelos, incluido el final (`faster_rcnn_v2_aug_robusto_v1_lr001`). Con
Faster R-CNN v1, el único entrenado con los dos perfiles, da el mismo AP@0,5 en validación que `base`
(0,9426 frente a 0,9433). Las cifras de esta página siguen siendo las del aumento base; las imágenes de cada
transformación del perfil final están en `docs/informes/figuras/aumento/` (`herramientas/figuras_aumento.py`).

## Figuras

| Figura | Qué muestra | Pie de figura propuesto |
|---|---|---|
| `catalogo_transformaciones.jpg` | Cada transformación aplicada sola sobre la misma imagen | Transformaciones evaluadas. En verde, las que se usan; en rojo, las descartadas. `Perspective` devuelve cajas que no coinciden con los robots. |
| `ejemplos_aumento.jpg` | Una imagen de cada vídeo de entrenamiento con tres copias aumentadas | Original y tres copias aumentadas de cada secuencia de entrenamiento. En azul, robots normales; en naranja, `difficult`. |
| `cajas_antes_despues.png` | Tamaño y forma de las cajas antes y después, y frecuencia de cada transformación | El aumento propuesto conserva la forma de las cajas y añade robots más pequeños; el del notebook original las ensancha. |
| `centros_y_brillo.png` | Posición de los centros de las cajas y brillo medio, antes y después | Los robots siguen en la franja a media altura y la iluminación cubre un rango más amplio. |

Para la memoria, que tiene un máximo de 10 páginas, bastan
`catalogo_transformaciones.jpg` y `cajas_antes_despues.png`.

## Tablas

| Tabla | Contenido | Uso |
|---|---|---|
| `resumen_aumento.csv` | Imágenes, robots, robots perdidos, `difficult`, truncados, tamaño y forma para el entrenamiento original, las copias aumentadas y el aumentador del notebook original | Tabla comparativa de la memoria |
| `manifest_aumento.csv` | Una fila por copia aumentada: imagen de origen, semilla, robots antes y después y transformaciones aplicadas | Trazabilidad: permite saber qué se hizo a cada imagen |

## Cifras principales

| | Imágenes | Robots | Robots perdidos | Relación de aspecto |
|---|---:|---:|---:|---:|
| Entrenamiento original | 796 | 1399 | — | 1,11 |
| Copias aumentadas | 2388 | 4167 | 0,7 % | 1,10 |
| Aumentador del notebook original (simulado) | 2388 | 3606 | 14,1 % | 1,18 |
