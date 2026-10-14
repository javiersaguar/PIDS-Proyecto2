# Depuración del dataset (T13)

Revisión del 14/10/2026 sobre las 808 imágenes anotadas, después de la revisión
cruzada (T10). **Se excluyen 12 imágenes y quedan 796.**

Las imágenes y sus `.xml` **no se borran** de `ENTREGA 1/WEEK1/ANOTACION/`: siguen
versionadas para poder repetir el análisis. La exclusión se aplica al generar los
conjuntos de entrenamiento, validación y test, porque
[`data_aug.ipynb`](../ENTREGA%201/WEEK1/data_aug.ipynb) lee la lista
[`depuracion_excluir.csv`](depuracion_excluir.csv).

## Qué se revisó

| Origen | Imágenes |
|---|---:|
| Poco nítidas según el EDA (`nitidez_rel < 0,35` en `metricas_imagenes.csv`) | 52 |
| Casi duplicadas de la anterior según el EDA (diferencia < 5) | 11 |
| Apuntadas en [`casos_dudosos.md`](casos_dudosos.md) como «revisar en T13» y no incluidas arriba | 6 |
| **Total revisado a ojo, con sus cajas dibujadas** | **69** |

Las 15 cajas atípicas de `cajas_atipicas.csv` ya las revisó el EDA y son correctas.

## Criterios

| # | Criterio | Decisión | Por qué |
|---|---|---|---|
| D1 | Hay un robot en la imagen que no se puede anotar (solo una estela) y no tiene caja | **Se excluye** | La red aprendería como fondo algo que es un robot. Es una etiqueta contradictoria, no un caso difícil. |
| D2 | Casi duplicada de la imagen anterior (robots y cámara parados) | **Se excluye**; se conserva la primera del tramo | No aporta información nueva y da más peso a los momentos en que nada se mueve. En validación y test, además, cuenta dos veces el mismo acierto o error. |
| D3 | Imagen movida con sus robots bien anotados como `difficult` | **Se conserva** | El robot se moverá en el Bloque 3. Quitarlas haría el entrenamiento más fácil que la realidad. |
| D4 | Imagen movida o vacía sin robots: suelo, piernas, nuestro propio robot | **Se conserva** | Son negativos difíciles: enseñan qué no es un robot. El EDA recomienda no perderlos. |
| D5 | Robot cortado por el borde con menos del 30 % visible y sin caja | **Se conserva** | Sigue la regla R5 de los criterios de anotación: es la etiqueta correcta. |

## Resultado

| Imagen | Criterio | Motivo |
|---|---|---|
| V03 frame_1560 | D1 | Solo estelas moradas a la izquierda donde hay un robot; no se puede anotar |
| V03 frame_1176 | D2 | Igual que frame_1152 |
| V04 frame_0120 | D2 | Igual que frame_0096 |
| V05 frame_1584 | D2 | Igual que frame_1560 |
| V05 frame_1800 | D2 | Igual que frame_1776 |
| V06 frame_0168 | D2 | Igual que frame_0144 |
| V07 frame_1824, frame_1848 | D2 | Iguales que frame_1800 |
| V09 frame_1416 | D2 | Igual que frame_1392 |
| V10 frame_1752, frame_1776, frame_1800 | D2 | Iguales que frame_1728 |

Se conservan las otras 57 imágenes revisadas:

- **41 movidas con sus robots anotados** (D3).
- **Negativos difíciles** (D4): piernas en V02 1224 y 1248, el brazo de nuestro propio
  robot en V05 1104 y V06 2088 y 2112, y suelo o sala vacía en V01 1728, V03 1488 y 1536,
  V06 0096, 1032, 1536, 1632 y 1656, y V10 0144.
- **Robots cortados por debajo del 30 %** (D5): V01 1296 y V03 1080.

Varias imágenes que el 12/10 se apuntaron como «probable eliminación» (V01 0552 y
1704, V09 0672 y 1320, V10 0840, 1056 y 1152) tienen ya sus robots anotados como
`difficult` tras la revisión cruzada, así que pasan a D3.

## Efecto

Las 796 imágenes que quedan son el conjunto de entrenamiento: desde el 14/10/2026,
validación y test son los conjuntos de otros grupos que da la asignatura (ver T18).

| Vídeo | Excluidas |
|---|---:|
| V03 | 2 |
| V04 | 1 |
| V05 | 2 |
| V06 | 1 |
| V07 | 2 |
| V09 | 1 |
| V10 | 3 |
| **Total** | **12** |

Quedan 796 imágenes, cuatro por debajo de las ~800 del objetivo. Se han anotado 808,
y depurar es parte del Bloque 1: es preferible un dataset algo menor y sin etiquetas
contradictorias. Si el grupo quiere superar las 800, T02 dejó prevista una grabación
complementaria.
