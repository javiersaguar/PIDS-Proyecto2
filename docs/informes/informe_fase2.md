# Memoria del proyecto Fase 2

Autores: Javier Saguar, Alejandro Cuevas, Mónica Fernández, Pedro José Orrego, Daniel Naval

Contenido actualizado el 16 de octubre de 2026. Grupo 2 según el usuario pids2; confirmar identificación administrativa y fecha de entrega.

## Respuesta a la revisión anterior

No aplica a la primera entrega. No hay comentarios docentes incorporados en esta versión de trabajo.

## Reparto del trabajo

Distribución documentada en los commits y tareas. La participación final se revisará en grupo antes de entregar.

| Integrante | Datos y análisis | Entrenamiento y evaluación |
| --- | --- | --- |
| Javier Saguar | Organización, extracción, lote A, revisión, depuración, aumento y ampliaciones del EDA | Experimentos en laboratorio, evaluación y memoria |
| Alejandro Cuevas | Lote B, revisión de C y EDA | Adaptación de train/test y propuestas de mejora |
| Mónica Fernández | Lote C y calibración | Pendiente de consolidar reparto |
| Pedro José Orrego | Lote D, calibración y selección de figuras | Pendiente de consolidar reparto |
| Daniel Naval | Lote E y calibración | Pendiente de consolidar reparto |

Tabla 1. Reparto provisional del trabajo documentado.

## Índice

## 7. El pipeline de entrenamiento

Se entrena sobre 3184 imágenes con aumento base o sobre las 796 originales. Validación contiene 672 imágenes de 11 secuencias externas, con 1561 robots, 255 difficult y ningún negativo. Test contiene 718 imágenes y se reserva para evaluar el modelo definitivo una sola vez; no hay resultados de test en este informe.

Figura 1. Flujo realmente usado para ajustar pesos y seleccionar el checkpoint con validación.

![Flujo realmente usado para ajustar pesos y seleccionar el checkpoint con validación.](figuras/pipeline.png)

La imagen se carga en RGB, se pasa a tensor en [0,1] y el modelo normaliza y escala internamente. Los primeros experimentos usan lote físico 8; res1024 acumula dos microbatches de 4 antes de actualizar. Una época recorre todo entrenamiento. Se suman las pérdidas de RPN, clasificación y regresión; SGD actualiza los pesos mediante retropropagación.

Las cajas difficult también participan en el entrenamiento: sin_difficult elimina el flag del diccionario que se entrega al detector, no sus cajas. Para la pérdida de validación se usa no_grad; para las detecciones y AP, eval. Cada época se guarda model_last y solo se reemplaza model_best cuando sube AP@0,5.

## 8. Modelos

Se ha probado Faster R-CNN ResNet-50 con FPN [3,4], una red de dos etapas: el RPN propone regiones y la cabeza clasifica y ajusta sus cajas. Se inicializa con COCO y se sustituye la cabeza por fondo y robot. FPN combina escalas, relevante para objetivos a distancias diferentes. No se ha realizado todavía una comparación de arquitecturas.

El código contempla Faster R-CNN v2 y una variante MobileNet, entre otras. Los resultados de COCO no predicen la ganancia en nuestros datos. Cualquier comparación futura debe medir precisión y latencia para el uso en el robot.

## 9. Hiperparámetros

| Parámetro | Valor aplicado |
| --- | --- |
| Épocas / lote efectivo / semilla | 30 / 8 / 0; res1024: microbatch 4 × 2 |
| Optimizador | SGD; momentum 0,9; weight decay 0,0005 |
| Tasa inicial | 0,0001 en originales; 0,001 en lr001 y res1024 |
| Programador | ReduceLROnPlateau con pérdida de validación |
| Bajada / paciencia / mínimo | ×0,1 / 5 épocas / 1e−10 |
| Resolución del detector | 800/1333; res1024: 1024/1820 |
| Datos aumentados | Originales y 3 copias; mismo aumento base |
| Checkpoint seleccionado | Mayor AP@0,5 en validación |
| Entorno | PyTorch 2.4.1; torchvision 0.19.1; RTX 3060 12 GB |

Tabla 2. Configuración común de los experimentos medidos.

La tasa 0,001 se ensayó como salto de diez veces manteniendo los otros parámetros. No se añadieron warmup, otra arquitectura ni los perfiles nuevos de aumento. Cambiar una variable facilita interpretar el resultado, aunque una sola semilla no mide su variabilidad.

## 10. Métricas

IoU es la intersección entre caja predicha y real dividida por su unión. Con IoU≥0,5 y confianza≥0,5 se emparejan detecciones por confianza: acierto TP, detección sin pareja FP y robot sin pareja FN. Precisión es TP/(TP+FP), exhaustividad TP/(TP+FN) y F1 la media armónica de ambas.

AP resume la curva precisión–exhaustividad al variar confianza. AP@0,5 fija IoU en 0,5; AP@0,75 exige cajas más ajustadas; AP 0,50:0,95 promedia umbrales de IoU de 0,50 a 0,95. Al haber una clase, la media entre clases coincide con su AP. En los grupos normales/difficult se ignoran las anotaciones y detecciones emparejadas del otro grupo.

AP small usa la categoría de área de COCO, no el criterio de ancho <30 px de nuestra anotación. El AP de grupos y el recall a confianza fija responden a preguntas distintas. Además, las etiquetas incompletas de validación pueden penalizar detecciones correctas como FP; no se interpreta el recuento como error visual confirmado.

## 11. Experimentos

### 11.1. Comparación del aumento y de la tasa

| Experimento | Mejor época | AP50 historial | AP50 evaluación | AP evaluación |
| --- | --- | --- | --- | --- |
| Sin aumento lr 0,0001 | 20 | 0,9229 | 0,9228 | 0,5809 |
| Aumento base lr 0,0001 | 29 | 0,9425 | 0,9416 | 0,6081 |
| Aumento base lr 0,001 | 5 | 0,9432 | 0,9433 | 0,6302 |
| lr 0,001 res1024 | 2 | 0,9464 | 0,9465 | 0,6047 |

Tabla 3. Mejor checkpoint por AP50. AP sin sufijo es AP 0,50:0,95. El historial y la evaluación final se mantienen separados.

El aumento base mejora especialmente difficult: AP50 de 0,5518 a 0,6341. La comparación a igual número de épocas incluye cuatro veces más imágenes y actualizaciones con aumento; no permite atribuir toda la diferencia solo a las transformaciones. La ejecución con lr001 conserva ese mismo conjunto de 3184 imágenes.

Figura 2. Pérdidas y AP por época. Los puntos señalan los checkpoints elegidos por AP50.

![Pérdidas y AP por época. Los puntos señalan los checkpoints elegidos por AP50.](../../ENTREGA%201/WEEK2/comparaciones/lr001/curvas_comparadas.png)

Con lr001 se alcanza AP50=0,943169 en la época 5; la referencia llega a 0,942506 en la 29. Es aprendizaje más rápido y solo +0,066 puntos en el mejor AP50 del historial. La ejecución completa terminó el 15/10 a las 22:13, incluida la validación, con salida 0.

### 11.2. Curvas y resultado del cambio de tasa

La pérdida de validación mínima aparece en la época 4, 0,221198, y sube hasta 0,241296 en la 30 mientras la de entrenamiento baja a 0,065661. El AP50 final cae a 0,933178. Hay indicios de sobreajuste después del óptimo temprano: se conserva model_best de la época 5 y no model_last.

Figura 3. Tasa usada en cada época. Las bajadas de ReduceLROnPlateau no recuperan el óptimo temprano.

![Tasa usada en cada época. Las bajadas de ReduceLROnPlateau no recuperan el óptimo temprano.](../../ENTREGA%201/WEEK2/comparaciones/lr001/lr_comparado.png)

En lr001 se usa 0,001 en épocas 1–10, 0,0001 en 11–16, 0,00001 en 17–22, 0,000001 en 23–28 y 0,0000001 en 29–30. La tasa del experimento con aumento original no bajó. Más épocas con esta ejecución no solucionaron la pérdida de validación.

| Métrica en validación | lr 0,0001 | lr 0,001 | Cambio pp |
| --- | --- | --- | --- |
| AP50 todos | 0,9416 | 0,9433 | +0,17 |
| AP 0,50:0,95 todos | 0,6081 | 0,6302 | +2,21 |
| AP75 todos | 0,7146 | 0,7460 | +3,14 |
| AP50 normales | 0,9664 | 0,9740 | +0,76 |
| AP50 difficult | 0,6341 | 0,6462 | +1,21 |
| AP small | 0,1074 | 0,1182 | +1,08 |

Tabla 4. Evaluación final de los mejores checkpoints con el mismo procedimiento y conjunto.

El cambio de tasa mejora sobre todo el ajuste de cajas. AP50 ya era alto y su incremento es pequeño. La ganancia modesta en objetos pequeños motivó el experimento de resolución de los apartados 11.5 y 11.6.

### 11.3. Errores umbral y coste de inferencia

| Confianza e IoU ≥0,5 | lr 0,0001 | lr 0,001 | res1024 |
| --- | --- | --- | --- |
| TP / FN | 1478 / 83 | 1478 / 83 | 1493 / 68 |
| FN normales / difficult | 20 / 63 | 18 / 65 | 12 / 56 |
| FP frente a etiquetas | 210 | 190 | 324 |
| Precisión | 0,8756 | 0,8861 | 0,8217 |
| Recall total | 0,9468 | 0,9468 | 0,9564 |
| Recall difficult | 0,7529 | 0,7451 | 0,7804 |
| F1 | 0,9098 | 0,9155 | 0,8840 |

Tabla 5. Recuento a un umbral fijo; no debe confundirse con el AP.

El cambio de tasa reduce 20 FP y detecta dos normales adicionales, pero pierde dos difficult más; el TP total no cambia. Que AP difficult suba a 0,6462 mientras baja su recall a confianza 0,5 es compatible: el AP recorre confianzas y también depende de la ordenación y las cajas.

Figura 4. Precisión exhaustividad y F1 de lr001 en la rejilla de confianzas de validación.

![Precisión exhaustividad y F1 de lr001 en la rejilla de confianzas de validación.](../../ENTREGA%201/WEEK2/resultados_test/faster_rcnn_v1_aug_lr001_val/umbral_confianza.png)

El mejor F1 muestreado pasa de 0,95 a 0,85 con lr001 y vuelve a 0,95 con res1024. La rejilla termina en 0,95 y no determina el óptimo exacto. A confianza 0,5, res1024 detecta 15 robots más, nueve difficult, pero añade 134 FP y reduce F1. La latencia individual sube de 75,1 a 121,6 ms; no incluye captura, red ni actuación.

### 11.4. Comparación por secuencia

| Secuencia | AP50 antes | AP50 lr001 | FN antes → después |
| --- | --- | --- | --- |
| 2023 GR04 0008 | 0,9876 | 0,9886 | 2 → 2 |
| 2024 GR02 0001 | 0,9393 | 0,9380 | 1 → 0 |
| 2024 GR02 0007 | 0,9877 | 0,9873 | 1 → 1 |
| 2024 GR02 0008 | 0,9864 | 0,9782 | 0 → 0 |
| 2024 GR04 0002 | 0,9817 | 0,9844 | 0 → 0 |
| 2024 GR04 0003 | 0,8131 | 0,8096 | 6 → 6 |
| 2025 GR01 0002 | 0,9719 | 0,9775 | 2 → 3 |
| 2025 GR01 0010 | 0,9049 | 0,9404 | 4 → 1 |
| 2025 GR03 0007 | 0,9661 | 0,9678 | 8 → 9 |
| 2025 GR03 0011 | 0,8465 | 0,8473 | 30 → 28 |
| 2025 GR04 0011 | 0,9280 | 0,9290 | 29 → 33 |

Tabla 6. Secuencias de validación comparadas con las mismas etiquetas.

Figura 5. Cambio de AP50 por secuencia en puntos porcentuales.

![Cambio de AP50 por secuencia en puntos porcentuales.](../../ENTREGA%201/WEEK2/comparaciones/lr001/secuencias_comparadas.png)

AP50 mejora en 7 de 11 secuencias y baja en 4. GR01_0010 de 2025 gana 3,55 puntos y reduce sus FN de 4 a 1. En GR04_0011 de 2025 aumentan de 29 a 33 los FN y de 25 a 28 los difficult perdidos. GR04_0003 de 2024 sigue perdiendo sus seis difficult; el cambio de tasa no resuelve ese caso.

### 11.5. Resolución y evolución del entrenamiento

La propuesta de Alejandro se ejecutó desde COCO con lr=0,001 y aumento base, elevando min_size/max_size de 800/1333 a 1024/1820. Un frame pasa aproximadamente de 1333 × 750 a 1820 × 1024, un 86 % más de píxeles. Para memoria se usaron microbatch 4 y acumulación 2, frente a lote físico 8. No son idénticos numéricamente: pueden cambiar propuestas y redondeos.

Figura 6. Misma semilla y datos. Los puntos marcan el máximo AP50 de cada historial, no el máximo AP promedio.

![Misma semilla y datos. Los puntos marcan el máximo AP50 de cada historial, no el máximo AP promedio.](../../ENTREGA%201/WEEK2/comparaciones/res1024/curvas_comparadas.png)

El mejor AP50 de res1024 es 0,946440 en la época 2. Su AP 0,50:0,95 es 0,605390; el máximo de esta otra métrica aparece en la época 5, con 0,632233 y AP50 0,942070. Se respeta el criterio predefinido AP50 y se evalúa model_best de la época 2, sin seleccionar retrospectivamente por otra métrica.

La pérdida de validación mínima es 0,215909 en la época 3 y termina en 0,232343, mientras la de entrenamiento baja a 0,073149. El AP50 final cae a 0,933510. Hay indicios de sobreajuste y estancamiento tras el óptimo temprano. ReduceLROnPlateau usa 0,001 en 1–9, 0,0001 en 10–15, 1e−5 en 16–21, 1e−6 en 22–27 y 1e−7 en 28–30; no recupera el máximo.

Entrenamiento y validación finalizaron el 16/10 hacia las 08:45 Europe/Madrid, salida 0, unas nueve horas desde el lanzamiento. El máximo de 8482 MiB reservados corresponde al preflight, no a una medición del pico de las 30 épocas. Se conservan conjuntos, scheduler y aumento; no se ha evaluado test.

### 11.6. Resultado y coste de la resolución

| Mejor por AP50 en validación | lr001 800 | lr001 1024 | Cambio pp |
| --- | --- | --- | --- |
| AP50 todos | 0,9433 | 0,9465 | +0,32 |
| AP 0,50:0,95 todos | 0,6302 | 0,6047 | −2,55 |
| AP75 todos | 0,7460 | 0,6990 | −4,70 |
| AP50 difficult | 0,6462 | 0,6282 | −1,80 |
| AP small | 0,1182 | 0,1886 | +7,04 |
| AP large | 0,6919 | 0,6459 | −4,60 |

Tabla 7. Evaluación final del checkpoint seleccionado. El historial se presenta por separado.

Figura 7. La mejora de pequeños convive con retrocesos en otras métricas y mayor latencia individual.

![La mejora de pequeños convive con retrocesos en otras métricas y mayor latencia individual.](../../ENTREGA%201/WEEK2/comparaciones/res1024/precision_y_coste.png)

La inferencia individual tarda 121,6 frente a 75,1 ms, +61,9 %, aproximadamente 8,2 frente a 13,3 imágenes/s solo de inferencia. En lote son 120,5 frente a 72,7 ms/imagen, pero con lotes distintos de 4 y 8. La comparación individual es más directa; ninguna cifra mide la demo completa.

Figura 8. Cambio de AP50 frente a lr001 a resolución original; escala en puntos porcentuales.

![Cambio de AP50 frente a lr001 a resolución original; escala en puntos porcentuales.](../../ENTREGA%201/WEEK2/comparaciones/res1024/secuencias_comparadas.png)

AP50 mejora en 4 secuencias, baja en 6 y empata en una. GR03_0011 de 2025 gana 4,16 puntos y reduce FN de 28 a 22. GR04_0011 de 2025 reduce FN de 33 a 25, pero FP sube de 28 a 58. GR01_0002 de 2025 pierde 1,20 puntos. GR04_0003 de 2024 sigue perdiendo sus seis difficult. El CSV complementario conserva todas las secuencias.

## 12. Análisis cualitativo

La inspección de las predicciones distingue errores del detector y carencias de las etiquetas. En la figura siguiente se ven cuatro robots, pero el XML de GR02_0001/frame_0444 de 2024 contiene una sola caja. Una detección correcta de los otros tres puede contarse como FP. No se modifican las etiquetas para conservar la comparación.

Figura 9. Caso confirmado de anotación incompleta. La caja azul es la única del XML.

![Caso confirmado de anotación incompleta. La caja azul es la única del XML.](figuras/etiqueta_incompleta.png)

Esto limita la interpretación de los 190 FP de lr001 y los 324 de res1024, y de precisión, F1 y AP. No se ha cuantificado la extensión del problema ni se atribuyen todos los FP a omisiones. GR02_0001 pasa de 49 a 71 FP frente a etiquetas; no son necesariamente errores visuales nuevos.

Figura 10. Res1024 en PIDS2025_GR03_0011/frame_0600: TP 4, FP 4 y FN 1 frente a las etiquetas; rojo indica detección sin pareja.

![Res1024 en PIDS2025_GR03_0011/frame_0600: TP 4, FP 4 y FN 1 frente a las etiquetas; rojo indica detección sin pareja.](../../ENTREGA%201/WEEK2/comparaciones/res1024/ejemplo_errores_res1024.png)

La muestra de res1024 incluye una caja roja sobre una pierna y varias cajas solapadas en torno a un objetivo: las etiquetas omitidas no explican todos los errores. Los difficult concentran 65/83 FN de lr001 y 56/68 de res1024. Su recall al umbral 0,5 mejora, pero no su AP50 agregado; el flag agrupa tamaños, oclusión y movimiento.

### 12.1. Conclusiones y trabajo pendiente

Se conserva provisionalmente lr=0,001 a resolución 800/1333 y el checkpoint de la época 5 como referencia: mejora AP agregado, ajuste de cajas y FP frente a lr=0,0001, con una latencia similar. La diferencia de +0,17 puntos en AP50 con una única semilla no prueba una mejora estable; tampoco hay mejora uniforme en difficult al umbral fijo.

Se han completado cuatro entrenamientos y su evaluación en validación. La resolución mayor aporta +7,04 puntos de AP small y reduce 15 FN, pero aumenta FP y latencia y baja AP 0,50:0,95 en el checkpoint seleccionado. Se conserva lr001 a resolución original como referencia por su equilibrio; res1024 queda como alternativa si prima detectar pequeños y se acepta ese coste.

La selección por AP50 tiene consecuencias: en res1024 el máximo AP 0,50:0,95 del historial está en la época 5, no en la 2 elegida. No se ha reevaluado otro checkpoint ni se concluye que la resolución empeore siempre el ajuste de cajas. Una semilla y el cambio de microbatch impiden aislar completamente su efecto.

Falta comparar arquitecturas y evaluar el modelo definitivo en test; la fase 2 sigue siendo un avance. Como experimento posterior se plantea una ampliación dirigida a difficult, con los demás parámetros fijos. Los perfiles de sombras, lluvia y oclusión están preparados, pero no participan en estos resultados. Se limita la selección sobre validación y test se reserva para una única evaluación final.

## Referencias

[1] labelImg. Herramienta de anotación PascalVOC. https://github.com/HumanSignal/labelImg

[2] Albumentations 1.4.18. Código de transformaciones. https://github.com/albumentations-team/albumentations/tree/1.4.18

[3] S. Ren et al. Faster R-CNN Towards Real-Time Object Detection with Region Proposal Networks. 2015. https://arxiv.org/abs/1506.01497

[4] torchvision 0.19. Faster R-CNN ResNet-50 FPN. https://docs.pytorch.org/vision/0.19/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn.html

[5] Repositorio del grupo. Datos, criterios, notebooks y resultados. https://github.com/javiersaguar/PIDS-Proyecto2

Los originales, XML, exclusiones y manifiestos están en el repositorio. Los HTML del EDA son material complementario; las figuras del cuerpo son exportaciones estáticas. Los experimentos y tablas de esta versión se han medido en validación, salvo las comprobaciones de integridad del aumento.
