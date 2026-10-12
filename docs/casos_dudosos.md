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
| V03 | frame_1560.jpg | Javier | Fotograma muy movido: solo estelas moradas a la izquierda, irreconocibles | Sin caja; revisar en T13 (probable eliminación) |
