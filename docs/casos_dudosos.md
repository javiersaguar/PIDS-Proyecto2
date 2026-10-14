# Casos dudosos de anotación

Aquí se apunta todo fotograma que no encaje claramente en las reglas de [`criterios_anotacion.md`](criterios_anotacion.md), por ejemplo un robot que se sabe que está pero que no se reconoce. Estos casos se revisan en la depuración (T13) y los más representativos van a la memoria.

| Vídeo | Fichero | Quién | Problema | Decisión |
|---|---|---|---|---|
| V01 | frame_0552.jpg | Javier | Fotograma muy movido: dos estelas de luz (naranja y cian) donde había robots, irreconocibles | Sin caja; revisar en T13 (probable eliminación) |
| V01 | frame_0840.jpg | Javier | Estela naranja al fondo (x≈830-868) irreconocible; el robot morado sí se anota (difficult) | Sin caja para la estela |
| V01 | frame_0864.jpg | Javier | Estelas cian y naranja irreconocibles; el robot morado sí se anota (difficult) | Sin caja para las estelas |
| V01 | frame_1296.jpg | Javier | Fotograma muy movido; solo restos de robots en ambos bordes | Sin caja; revisar en T13 (probable eliminación) |
| V01 | frame_1368.jpg | Javier | Resto naranja cortado por el borde izquierdo, irreconocible | Sin caja para ese resto |
| V01 | frame_1464.jpg | Javier | Estela morada cortada por el borde derecho, irreconocible | Sin caja para la estela |
| V01 | frame_1704.jpg | Javier | Fotograma muy movido: solo estelas naranjas | Sin caja; revisar en T13 (probable eliminación) |
| V02 | frame_0168.jpg | Javier | Fotograma muy movido: robots reconocibles solo por las luces | Cajas marcadas difficult |
| V02 | frame_0336.jpg … frame_0408.jpg | Javier | Sin robots a la vista (aula vacía o muy movido) | XML sin objetos |
| V02 | frame_1224.jpg, frame_1248.jpg | Javier | Fotograma totalmente movido, sin robots reconocibles | Sin caja; revisar en T13 (probable eliminación) |
| V09 | frame_0672.jpg | Daniel | Fotograma muy movido: a la derecha solo se ven formas oscuras con luces roja y morada donde podría haber robots, irreconocibles | Sin caja; revisar en T13 (probable eliminación) |
| V09 | frame_1320.jpg | Daniel | Fotograma muy movido | Sin caja; revisar en T13 (probable eliminación) |
| V10 | frame_0960.jpg | Daniel | Fotograma muy movido | Sin caja; revisar en T13 (probable eliminación) |
| V10 | frame_1056.jpg | Daniel | Fotograma muy movido | Sin caja; revisar en T13 (probable eliminación) |
| V10 | frame_1152.jpg | Daniel | Fotograma muy movido | Sin caja; revisar en T13 (probable eliminación) |
| V03 | frame_1560.jpg | Javier | Fotograma muy movido: solo estelas moradas a la izquierda, irreconocibles | Sin caja; excluida en la depuración (T13, criterio D1) |
| V08 | frame_0480.jpg | Javier | Caja sobre una única estela blanca (x≈288-356, y≈262-294), sin cuerpo reconocible | Caja eliminada en la revisión del lote D |
| V08 | frame_1944.jpg | Javier | Caja sobre estelas blancas finas (x≈1086-1176, y≈250-284), sin cuerpo reconocible | Caja eliminada en la revisión del lote D |
| V08 | frame_2040.jpg | Javier | Caja sobre una mancha de luz blanca (x≈826-864, y≈262-296), sin cuerpo reconocible | Caja eliminada en la revisión del lote D |
| V08 | frame_2184.jpg | Javier | Caja sobre estelas blancas (x≈1124-1212, y≈392-456), sin cuerpo reconocible | Caja eliminada en la revisión del lote D |
| V07 | frame_1200.jpg | Javier | Solo se ve una rueda en el borde derecho (x>1190, y≈480-600): menos del 30 % del robot | Sin caja |
| V07 | frame_0384.jpg | Javier | Mancha oscura con una luz en el borde izquierdo (x<80, y≈460-560), irreconocible | Sin caja |
| V09 | frame_0672.jpg, frame_1320.jpg | Javier | Fotogramas muy movidos que estaban sin caja: los dos robots se reconocen por la silueta y las luces | Cajas añadidas como difficult en la revisión del lote E; valorar en T13 |
| V10 | frame_0816.jpg, frame_0960.jpg | Javier | Robot muy movido que estaba sin caja; se reconoce por el patrón de luces | Caja añadida como difficult en la revisión del lote E; valorar en T13 |
| V10 | frame_0840.jpg, frame_1056.jpg, frame_1152.jpg | Javier | Solo estelas de luz, sin cuerpo reconocible | Sin caja (XML vacío) |
| V10 | frame_1008.jpg | Javier | En el borde izquierdo solo se ve una rueda: menos del 30 % del robot | Sin caja para ese robot |
