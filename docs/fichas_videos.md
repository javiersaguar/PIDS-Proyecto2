# Fichas de los vídeos y revisión de variabilidad (T02)

Revisión del 09/10/2026: 120 muestras repartidas uniformemente, doce por vídeo.
[`revision_videos.csv`](revision_videos.csv) registra las imágenes, sus índices y
tiempos. Los metadatos se han comprobado al decodificar todos los vídeos con OpenCV;
se conservan en [`videos.json`](../ENTREGA%201/WEEK1/ANOTACION/videos.json).

Los recuentos visibles son cualitativos en las muestras, no una anotación exhaustiva.
«Hasta 3» indica el máximo de rivales distinguibles observado, sin contar el cañón
propio. Las distancias se describen por tamaño aparente, sin medición en metros.

| Vídeo | Escenario y ambiente | Iluminación | Oclusiones y distractores | Robots observados | Distancia aparente y orientación | Cámara |
|---|---|---|---|---|---|---|
| V01 | Interior, vestíbulo de suelo pulido; motos expuestas al fondo | Natural de cristaleras y artificial; contraluz y reflejos fuertes | Personas, piernas, solapamientos, reflejos de robots y LED | Hasta 3 simultáneos | Lejanos a próximos; frontal, lateral y posterior | Avance y giros; desenfoque en cambios de dirección |
| V02 | Interior, aula con filas de sillas y personas | Artificial de techo y luz ambiental | Patas de sillas, piernas y solapamientos | Hasta 3 simultáneos | Lejanos a muy próximos; varias orientaciones | Traslaciones y giros, pasadas rápidas de rivales |
| V03 | Interior, aula de paredes blancas, mesas y sillas | Artificial y luz natural de ventana | Robots solapados, patas de mesas/sillas y piernas | Hasta 3 simultáneos | Distancias variadas, incluido primer plano; varias orientaciones | Movimiento, giros e inclinación; desenfoque en acercamientos |
| V04 | Exterior, explanada pavimentada junto a edificio y vegetación | Diurna, zonas de sombra y fondo más luminoso | Piernas, robots próximos al borde; suelo irregular | Hasta 3 simultáneos | Lejanos a próximos; frontal, lateral y posterior | Avances, giros y balanceo al desplazarse |
| V05 | Interior, pasillo largo de paredes claras y cerramiento gris | Artificial de techo | Personas, solapamientos, antenas visibles de cerca; perspectiva profunda | Hasta 3 simultáneos | Gran variación de tamaño, lejanos y próximos; varias orientaciones | Avance/retroceso y giros; desenfoque en pasadas |
| V06 | Interior, vestíbulo con suelo amarillo/verde y cristaleras | Mezcla natural/artificial; reflejos y LED saturados | Piernas, solapamientos, robots cortados por bordes y cañón propio | Hasta 3 simultáneos; algunas muestras muy borrosas | Lejanos a muy próximos; varias orientaciones | Giros, inclinación y sacudidas fuertes; desenfoque marcado |
| V07 | Interior, vestíbulo de suelo pulido, zona de exposición | Mezcla natural/artificial, contraluz de cristaleras | Reflejos, personas, solapamientos y robots en los bordes | Hasta 3 simultáneos | Lejanos a próximos; distintas orientaciones | Avance y giros, con muestras movidas |
| V08 | Interior, vestíbulo amarillo/verde y transición a suelo pulido | Mixta; reflejos fuertes del fondo y los LED | Piernas, solapamientos, cortes por el borde y reflejos | Hasta 3 simultáneos | Lejanos a próximos; distintas orientaciones | Desplazamientos, giros e inclinación; desenfoque variable |
| V09 | Exterior, explanada pavimentada con personas y vegetación | Diurna, sombra en suelo y fondo más iluminado | Piernas, solapamientos y robots cortados por bordes | Hasta 3 simultáneos | Lejanos a muy próximos; frontal, lateral y posterior | Giros y acercamientos, balanceo y cortes por el borde |
| V10 | Interior, aula con filas de sillas y personas | Artificial de techo y luz ambiental | Patas de sillas, piernas, robots solapados y bordes | Hasta 3 simultáneos | Lejanos a muy próximos; varias orientaciones | Recorrido entre sillas y giros; desenfoque en movimientos rápidos |

## Cobertura y decisión sobre nuevas grabaciones

El material cubre las variaciones descritas en el README: interior/exterior,
iluminación mixta y natural, distintos fondos, orientación, distancia aparente,
movimiento y oclusión. Hay distractores difíciles (reflejos, cañón propio, sillas y
personas); no equivalen a imágenes totalmente vacías de rivales.

**Decisión:** no hace falta repetir ahora una categoría de escenario para empezar
a anotar. Sí conviene reservar una grabación complementaria: 808 originales dejan
muy poco margen si se exige conservar 800 tras depurar. Si se eliminan más de ocho,
extraer originales adicionales de instantes no usados o grabar una secuencia nueva.
Las copias de calibración y los aumentos no compensan la pérdida de originales.

Límites: las dos grabaciones de exterior diurno son de un mismo entorno, hay
interiores similares y pocos ejemplares físicos. No se observa una secuencia
dedicada de circuitos con obstáculos fijos ni una de iluminación muy baja. Para el
Bloque 3 se recomienda añadir escenas del circuito real, obstáculos y cambios de
iluminación, reservando secuencias independientes para validación/test.

Esta revisión es un muestreo; no certifica todos los casos del vídeo. En el EDA se
cuantificarán tamaños de cajas, negativos, oclusiones y desenfoque tras anotar.
