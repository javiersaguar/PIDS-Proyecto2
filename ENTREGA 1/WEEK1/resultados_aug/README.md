# Resultados del aumento de datos

Figuras y tablas que genera [`data_aug.ipynb`](../data_aug.ipynb) (T14). Se
sobrescriben cada vez que se ejecuta el notebook, así que **no se editan a mano**.
Las cifras actuales corresponden a las etiquetas del 12/10/2026, **antes de la
depuración (T13)**.

Las imágenes aumentadas no están en el repositorio: el notebook las crea en
`data_train/`, `data_val/` y `data_test/`, en la raíz, que Git ignora. Son 352 MB.

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
| Entrenamiento original | 483 | 837 | — | 1,11 |
| Copias aumentadas | 1449 | 2496 | 0,6 % | 1,11 |
| Aumentador del notebook original (simulado) | 1449 | 2164 | 13,8 % | 1,18 |
