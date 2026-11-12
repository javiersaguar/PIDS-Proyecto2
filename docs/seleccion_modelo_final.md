# Selección del modelo final (fijada antes de evaluar en test)

Escrito el 24/10/2026, **antes de abrir el conjunto de test**. Todo lo de abajo sale de la
evaluación en validación (672 imágenes, 1561 robots, 255 `difficult`) de la cadena de
entrenamientos ([`cadena_entrenamientos.md`](cadena_entrenamientos.md)). La tabla completa
está en `ENTREGA 1/WEEK2/cadena/resumen.csv`.

## Regla

1. **Modelo final:** el de mayor AP@0,5 en validación con todos los robots. Si la diferencia
   con otro es menor de 0,5 puntos (una sola semilla), se considera empate y se prefiere el
   que cuesta menos (menos épocas y menos tiempo de entrenamiento).
2. **Opción rápida para la demo:** el de menor tiempo por imagen entre los que tienen AP@0,5
   en validación de al menos 0,92.
3. **Umbral de confianza:** el de mejor F1 de la curva de umbrales en **validación**, fijado
   para cada modelo antes de ver el test.
4. **Test:** los 7 modelos con lr 0,001, **una sola vez cada uno**. El test no se usa para
   elegir ni para ajustar nada.

## Validación (AP@0,5, lr 0,001 salvo indicación)

| Modelo | Todos | Difficult | F1 máx. | Umbral | ms/imagen |
|---|---:|---:|---:|---:|---:|
| faster_rcnn_v2 | **0,9513** | 0,6422 | 0,9361 | 0,95 | 99,5 |
| retinanet_v2 | 0,9447 | 0,6213 | 0,9264 | 0,65 | 67,3 |
| faster_rcnn_v1 | 0,9426 | 0,6471 | 0,9305 | 0,90 | 75,1 |
| retinanet_v1 | 0,9396 | 0,5994 | 0,9229 | 0,65 | 72,2 |
| faster_rcnn_v3 | 0,9281 | 0,6027 | 0,9167 | 0,55 | 16,0 |
| ssd_v1 | 0,9008 | 0,5199 | 0,8926 | 0,25 | 12,5 |
| ssd_v2 | 0,6823 | 0,3233 | 0,6839 | 0,20 | 4,2 |

Variantes de la fase 2: `faster_rcnn_v2` con lr 0,0005 (0,9507) y 0,002 (0,9497);
`retinanet_v2` con 0,0005 (0,9451) y 0,002 (0,9469); `faster_rcnn_v1` con 0,0005 (0,9420)
y 0,002 (0,9434). Ninguna supera a la de lr 0,001 de su modelo en más de 0,3 puntos.

## Decisión

- **Modelo final: `faster_rcnn_v2` con lr 0,001** (`faster_rcnn_v2_aug_robusto_v1_lr001`).
  Mayor AP@0,5. Con lr 0,0005 y 0,002 empata (diferencia menor de 0,5 puntos) y la de 0,001
  es la que menos épocas necesita (12).
- **Opción rápida: `faster_rcnn_v3`** (`faster_rcnn_v3_aug_robusto_v1_lr001`): 16 ms por imagen,
  unas 6 veces más rápido, con AP@0,5 de 0,928.

## Límites que se tendrán en cuenta al interpretar el test

- Una sola semilla: diferencias de menos de 0,5 puntos no son concluyentes.
- La mejor época se eligió con la validación, así que sus cifras son algo optimistas; por eso el test.
- Las etiquetas de validación y test son de otros grupos y no siguen del todo nuestro criterio
  (antenas, robots cortados), y algunas secuencias tienen robots sin anotar.
