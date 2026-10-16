# Memoria del proyecto Fase 1

Autores: Javier Saguar, Alejandro Cuevas, Mónica Fernández, Pedro José Orrego, Daniel Naval

Contenido actualizado el 15 de octubre de 2026. Grupo 2 según el usuario pids2; confirmar identificación administrativa y fecha de entrega.

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

## 1. Introducción

### 1.1. Contexto y motivación

El proyecto desarrolla un detector de RoboMasters rivales desde la cámara de un robot móvil. Movimiento, cambios de tamaño, iluminación y oclusión dificultan localizar sus cajas. La percepción alimentará una futura estrategia de apuntado y actuación.

### 1.2. Objetivos del proyecto

El Bloque 1 construye y caracteriza datos; el Bloque 2 ajusta el detector y el Bloque 3 lo integrará con el robot. Se obtienen 808 originales anotados y se seleccionan 796 tras revisar sus etiquetas.

## 2. Recolección de datos

### 2.1. Estrategia y condiciones de captura

Se grabaron diez vídeos en seis tipos de escenario, variando luz, contraluces, reflejos, obstáculos y distancias. Se incluyeron movimiento y patas de sillas porque se prevén en la demo. Los dos exteriores comparten ubicación; aún falta el circuito definitivo.

### 2.2. Extracción de imágenes

La cámara entrega 1280 × 720 a unos 30,30 fps. INTERVAL=24 conserva una muestra cada 0,79 s. La suma por vídeo floor(frames/24) produce 808 imágenes a partir de 19 508 frames y 643,8 s; no se redondea la duración global. Se reduce redundancia sin multiplicar el coste de anotación.

| Vídeo | Escenario | Duración s | Frames | Imágenes |
| --- | --- | --- | --- | --- |
| V01 | Vestíbulo granito | 65,4 | 1982 | 82 |
| V02 | Aula con sillas | 59,9 | 1815 | 75 |
| V03 | Aula blanca | 60,2 | 1823 | 75 |
| V04 | Exterior | 66,1 | 2003 | 83 |
| V05 | Pasillo | 59,6 | 1807 | 75 |
| V06 | Vestíbulo de color | 74,1 | 2244 | 93 |
| V07 | Vestíbulo granito | 61,2 | 1855 | 77 |
| V08 | Vestíbulo de color | 81,2 | 2460 | 102 |
| V09 | Exterior | 56,2 | 1704 | 71 |
| V10 | Aula con sillas | 59,9 | 1815 | 75 |
| Total | 1280 × 720 a 30,30 fps | 643,8 | 19 508 | 808 |

Tabla 2. Grabaciones propias y número exacto de imágenes extraídas.

## 3. Anotación de datos

Se utilizó labelImg [1] y XML PascalVOC, con una única clase robot. Cada integrante anotó su lote y otro revisó las cajas. Se conservaron imágenes negativas con XML vacío para que el entrenamiento no las ignore.

| Caso | Criterio operativo |
| --- | --- |
| Robot rival | Incluir chasis, ruedas, gimbal y cañón; excluir antenas. |
| Elementos ajenos | No anotar el cañón propio, reflejos ni robots en pantallas. |
| Oclusión y borde | Anotar si es reconocible y se ve al menos un 30 %; caja sobre la parte visible. |
| Difficult | Marcar si tiene menos de 30 px de ancho, menos de la mitad visible o está muy movido. |
| Robot muy pequeño | No anotar por debajo de 10 px de lado; conservar criterios en el aumento. |
| Negativo | Guardar imagen y XML sin objetos. |

Tabla 3. Criterios comunes aplicados a los lotes.

Como se observa en la figura siguiente, el criterio distingue cajas normales y difficult sin crear una segunda clase. Una frontera superior distinta alteraría tamaños y centros, por lo que se excluyen antenas y se ajusta el resto del robot de manera consistente.

Figura 1. Anotaciones de interior y exterior. Azul: normal; naranja: difficult.

![Anotaciones de interior y exterior. Azul: normal; naranja: difficult.](figuras/anotaciones.png)

Los cinco anotadores etiquetaron las mismas 20 imágenes de calibración. El IoU medio entre parejas fue 0,81; el borde superior presenta la mayor discrepancia, 7 px de mediana frente a 4–5 px en los otros bordes. Esto identifica un criterio por discutir, pero no establece un techo matemático del AP del modelo. Falta cerrar en grupo la ronda de discusión de T01.

## 4. Análisis exploratorio de los datos

### 4.1. Inventario y equilibrio

El EDA se calcula sobre los 808 originales, antes de excluir imágenes. Los aumentos no se mezclan en estas estadísticas. Las cifras de la tabla y la figura permiten separar cantidad de imágenes, número de objetos y dificultad.

| Estadística | Valor |
| --- | --- |
| Secuencias / imágenes | 10 / 808 |
| Imágenes medias por secuencia | 80,8 |
| Cajas / cajas medias por imagen | 1420 / 1,76 |
| Difficult | 375 cajas · 26,4 % |
| Imágenes negativas | 41 · 5,07 % |
| Área media de caja | 33,627 miles de píxeles² |
| Área mínima / máxima | 1,020 / 661,074 miles de píxeles² |
| Aspecto mediano ancho / alto | 1,11 |

Tabla 4. Estadísticas de los originales anotados.

Figura 2. Recuento y dificultad por vídeo; sus diferencias motivan analizar cada secuencia.

![Recuento y dificultad por vídeo; sus diferencias motivan analizar cada secuencia.](figuras/inventario.png)

No basta con equilibrar imágenes: V05 contiene 170 robots y V06 solo 117. V06 tiene 22 negativos en 93 imágenes, mientras V08 no tiene negativos y concentra 65 difficult. Se conservan estas diferencias porque representan situaciones reales de captura.

### 4.2. Tamaño forma e iluminación

Figura 3. Área y forma de las cajas de los 1420 robots. El eje de área es logarítmico.

![Área y forma de las cajas de los 1420 robots. El eje de área es logarítmico.](figuras/tamano_forma.png)

La distribución de la figura tiene una cola amplia de áreas, pero no hay cajas originales de menos de 30 px de ancho. La relación de aspecto mediana es 1,11. El análisis de cobertura de anclas obtiene un 99,6 % con IoU ≥0,5: no se cambia su configuración por ahora y se evita deformar las proporciones durante el aumento.

Figura 4. Brillo y contraste por secuencia, calculados en escala de grises.

![Brillo y contraste por secuencia, calculados en escala de grises.](figuras/iluminacion.png)

Los canales RGB caracterizan el color dominante, no solo la iluminación: también dependen del suelo y las paredes. Por eso se complementan con media y desviación típica de intensidad, y con nitidez por varianza del Laplaciano. El tono azulado de exteriores justifica cambios de color suaves; no se confunde ese tono con falta de luz. Se identificaron 52 imágenes poco nítidas para revisión visual.

La miniatura más parecida a una imagen procede del mismo vídeo en el 74 % de los casos. Esa correlación aconseja separar grabaciones completas, evitando una validación artificialmente fácil con fotogramas vecinos.

### 4.3. Posición y evolución temporal

Figura 5. Selección de mapas por vídeo. Todos y difficult comparten escala; se cuentan centros por 100 imágenes, incluidos los negativos.

![Selección de mapas por vídeo. Todos y difficult comparten escala; se cuentan centros por 100 imágenes, incluidos los negativos.](figuras/mapas_seleccionados.png)

La figura compara la posición de las anotaciones en un exterior y un interior con muchos negativos. Se normalizan los centros por tamaño de imagen y el histograma 16 × 9 por número de imágenes. La paleta cálida con intensidad no lineal hace visibles frecuencias bajas, pero mantiene cero blanco y un máximo común. No representa el área cubierta por las cajas.

Figura 6. Recuento por fotograma anotado en V05 y V06; la línea discontinua es su media.

![Recuento por fotograma anotado en V05 y V06; la línea discontinua es su media.](figuras/recuentos_temporales.png)

Las curvas muestran por qué la media de V05 es 2,27 y la de V06 1,26: el segundo vídeo contiene tramos sin objetivos. El complemento HTML incluye los diez vídeos y 132 ventanas disjuntas de 5 s para comparar todos frente a difficult. Son muestras cada 24 frames, no trayectorias individuales ni presencia inferida entre fotogramas.

## 5. Aumento de datos

Se aplica solo al entrenamiento y desde originales. Tres copias por imagen se combinan con las 796 originales depuradas: 3184 imágenes y 5566 cajas. Las 672 imágenes de validación y las 718 de test son secuencias independientes de otros grupos y no reciben aumento. Se mantiene un manifiesto de semillas y transformaciones [2].

| Técnica | Probabilidad | Variabilidad simulada |
| --- | --- | --- |
| Volteo horizontal | 0,50 | Orientaciones válidas de robots; no se invierte el suelo. |
| Afín sin deformación | 0,70 | Escala ×0,6–1,25; giro ±6°; desplazamiento horizontal ±8 % y vertical ±5 %. |
| Brillo y contraste o gamma | 0,50 conjunta | Exposición y sombras de intensidad global. |
| Tono y saturación o RGB | 0,30 conjunta | Balance de blancos y cambios suaves de color. |
| MotionBlur 3–9 px | 0,15 | Movimiento de cámara y objetivos. |
| JPEG o ruido o resolución | 0,30 conjunta | Una degradación entre JPEG, ruido gaussiano, ISO o resolución ×0,5–0,75. |
| Oclusión de barras | 0,15 | Obstáculos finos; cada barra limita la anchura tapada de cada robot. |

Tabla 5. Configuración del aumento base. Las alternativas OneOf no se aplican todas a la vez.

Figura 7. Original y una copia del aumento base, con las cajas transformadas.

![Original y una copia del aumento base, con las cajas transformadas.](figuras/ejemplo_aumento.png)

Se descartan volteo vertical y giros de 90°, el recorte 4:3 redimensionado a 16:9 que ensancha robots y la perspectiva con cajas incorrectas en Albumentations 1.4.18. El relleno gris evita duplicar robots sin etiqueta en los bordes. Se usan cajas ajustadas y filtros de lado mínimo 10 px y visibilidad 30 %.

## 6. Depuración de datos

Se revisaron visualmente 69 imágenes: 52 de baja nitidez, 11 casi duplicadas y 6 casos dudosos. Se excluyeron una imagen con un robot visible imposible de anotar de forma consistente y 11 redundantes. Se conservaron 41 imágenes movidas con sus robots difficult y los negativos difíciles. La baja nitidez no es por sí sola un motivo para borrar.

| Conjunto | Imágenes | Cajas |
| --- | --- | --- |
| Original anotado | 808 | 1420 |
| Original tras depuración | 796 | 1399 |
| Copias del aumento base | 2388 | 4167 |
| Entrenamiento total | 3184 | 5566 |

Tabla 6. Efecto de la depuración y del aumento base.

Las exclusiones están identificadas en docs/depuracion_excluir.csv; no se borra ningún original. Quedan cuatro imágenes por debajo del objetivo de unas 800. Se prioriza no entrenar con etiquetas contradictorias, y se mantiene prevista una captura complementaria si el grupo o el profesorado exige reponerlas.

Al aumentar se pierden 30 de las 4197 cajas que entrarían en las copias, un 0,715 %, frente al 14,1 % del aumentador de referencia de la asignatura. La relación de aspecto mediana permanece en 1,10 frente a 1,11 original. Es una comprobación de integridad del dataset, no una prueba de mejora del detector.

### 6.1. Ampliaciones preparadas y límites

Se han implementado perfiles optativos con sombras y llovizna solo en V04/V09, obstáculos con textura y oscuridad o movimiento adicionales en una copia de imágenes con difficult. La unión de máscaras de los obstáculos se limita al 25 % del área de cada caja, que no equivale al área visible del cuerpo del robot. El combinado se ha comprobado en memoria sobre 2388 copias, pero aún no se ha entrenado.

Estas ampliaciones tienen destinos separados y no sustituyen el aumento base de los experimentos ya medidos. La lluvia sintética no acredita robustez en lluvia real. Los límites principales del Bloque 1 son la variedad de exteriores, el desacuerdo sobre el borde superior y la falta de ejemplos del circuito definitivo.

## Referencias

[1] labelImg. Herramienta de anotación PascalVOC. https://github.com/HumanSignal/labelImg

[2] Albumentations 1.4.18. Código de transformaciones. https://github.com/albumentations-team/albumentations/tree/1.4.18

[3] S. Ren et al. Faster R-CNN Towards Real-Time Object Detection with Region Proposal Networks. 2015. https://arxiv.org/abs/1506.01497

[4] torchvision 0.19. Faster R-CNN ResNet-50 FPN. https://docs.pytorch.org/vision/0.19/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn.html

[5] Repositorio del grupo. Datos, criterios, notebooks y resultados. https://github.com/javiersaguar/PIDS-Proyecto2

Los originales, XML, exclusiones y manifiestos están en el repositorio. Los HTML del EDA son material complementario; las figuras del cuerpo son exportaciones estáticas. Los experimentos y tablas de esta versión se han medido en validación, salvo las comprobaciones de integridad del aumento.
