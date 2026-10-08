# Criterios de anotación

> **Estado: propuesta (tarea T01).** Hay que revisarla y aprobarla entre los cinco antes de empezar a anotar (T04–T08). Lo que esté por decidir aparece en la [sección 7](#7-decisiones-que-tiene-que-tomar-el-grupo).

Este documento parte de **lo que se ve en nuestros 10 vídeos** (se revisaron 60 fotogramas repartidos entre todos) y de **cómo usan las etiquetas los notebooks** de la asignatura. Cada regla lleva su justificación, porque en la memoria se valora sobre todo eso.

Los ejemplos se citan como `Vxx ~mm:ss`, es decir, vídeo y segundo aproximado.

---

## 1. Chuleta para tener abierta mientras se anota

| # | Regla |
|---|---|
| R1 | Una sola clase: **`robot`**, en minúsculas. Vale cualquier RoboMaster real, con cualquier color de LED, orientación o equipo. |
| R2 | **No** se anotan nuestro propio cañón (naranja, abajo en el centro), los reflejos en el suelo, los robots que salen en pantallas o carteles, ni nada que no sea un RoboMaster. |
| R3 | La caja va **ajustada** a lo visible del robot: chasis, ruedas, gimbal y lanzador. **Sin antenas**, sin sombra, sin reflejo y sin el halo de los LED. Tolerancia de ±2 px. |
| R4 | **Oclusión:** solo la parte visible. Se anota si se reconoce el robot y se ve aproximadamente un **30 %** o más. Si se ve menos de la mitad, se marca `difficult`. |
| R5 | **Cortado por el borde:** se aplica el mismo umbral y la caja llega hasta el borde. Los robots muy cercanos que llenan la imagen también se anotan. |
| R6 | **Lejanos:** se anotan todos los reconocibles con al menos **10 px** de lado (usar el zoom). Si miden **menos de 30 px de ancho**, se marcan `difficult`. |
| R7 | **Movido:** si se reconoce, la caja va al cuerpo del robot, no a la estela. Si está muy movido, se marca `difficult`. Si no se reconoce, no se pone caja y se apunta en casos dudosos. |
| R8 | **Una caja por robot**, nunca una caja para un grupo. Las cajas pueden solaparse. |
| R9 | Las imágenes **sin robots también se guardan** (Ctrl+S), para que tengan su `.xml` vacío. |
| R10 | **Regla de oro:** «Si viera solo este fotograma, ¿diría sin dudar que ahí hay un robot?». Si la respuesta es sí, se pone caja. Si es no, no se pone caja y el fotograma se apunta en [`casos_dudosos.md`](casos_dudosos.md). |

---

## 2. De qué partimos

### 2.1 Lo que hay en nuestros vídeos

Todos los vídeos son de **1280x720 a 30 fps** y la cámara va a ras de suelo (es la del robot). Hay seis tipos de escenario:

| Escenario | Vídeos | Qué lo hace difícil |
|---|---|---|
| Vestíbulo con suelo de granito pulido, con motos expuestas | V01, V07 | Reflejos muy marcados de los robots y de las luces en el suelo, contraluz de las cristaleras, motos y gente de fondo |
| Vestíbulo con suelo amarillo y verde | V06, V08 | Suelo brillante y luces de colores. En V06 la cámara va muy inclinada y movida |
| Aula con sillas | V02, V10 | Robots detrás o debajo de las patas de las sillas, piernas en primer plano |
| Laboratorio de paredes blancas | V03 | Varios robots juntos que se tapan entre sí, desenfoque de movimiento |
| Pasillo largo | V05 | Robots muy lejanos al fondo y robots muy cercanos en los que se ven las antenas |
| Exterior soleado | V04, V09 | Sombras duras, robots muy cercanos que llenan la imagen, robots entre piernas de gente |

Situaciones concretas que hay que tener resueltas antes de anotar:

- **Nuestro propio cañón** aparece en *todos* los fotogramas, abajo en el centro (punta naranja). En `V06 ~0:59` un robot rival apunta de frente a la cámara y se ven **dos** puntas naranjas: la de abajo es la nuestra.
- **Reflejos** de los robots y de sus LED en el suelo (`V01 ~0:14`, `V07 ~0:01`, `V08 ~0:48`).
- **Antenas:** se ven en los robots cercanos (`V05 ~0:24`, `V05 ~0:59`), pero no en los lejanos.
- **Desenfoque de movimiento**, desde un desenfoque leve (`V01 ~0:52`, `V03 ~0:48`) hasta fotogramas en los que el robot no se puede reconocer (`V05 ~0:36`).
- **Robots cortados** por el borde (`V03 ~0:36`, `V08 ~0:33`, `V08 ~1:20`, `V10 ~0:47`) y **muy cercanos**, que llenan media imagen (`V04 ~0:52`, `V09 ~0:23`, `V09 ~0:34`).
- **Robots que se tapan entre sí** (`V03 ~0:24`, `V03 ~0:59`, `V05 ~0:47`) o que quedan tapados por patas de sillas y piernas (`V02 ~0:24`, `V09 ~0:44`).
- **Robots diminutos** al fondo (`V05 ~0:01`, `V05 ~0:47`, `V10 ~0:13`), de unos 20 a 40 px de ancho.
- **LED de varios colores** (morado, naranja, azul y blanco): todos los robots son la misma clase.

### 2.2 Cómo usan las etiquetas los notebooks

Estos detalles del código condicionan las reglas:

| Hecho del código | Consecuencia para la anotación |
|---|---|
| `read_label` (`train.ipynb`) convierte **toda** caja en la clase 1 e ignora tanto el `name` como el `difficult` | Toda caja que dibujemos se entrena como robot. Si dudamos, es mejor no poner caja que poner una mala (R10). El `difficult` sirve para nuestros análisis (sección 5), no para el entrenamiento |
| Un robot que esté en la imagen **sin caja** se aprende como «fondo» | Se penaliza a la red por detectarlo. Por eso hay que anotar todo lo que sea reconocible (R4–R7), y los fotogramas con robots no anotables se revisan en la depuración (T13) |
| `parse_annotations` solo carga las imágenes **que tienen `.xml`** | Una imagen sin robots y sin `.xml` se pierde, y con ella el ejemplo negativo. De ahí la R9 |
| Las coordenadas se leen con `int()` y torchvision **falla con cajas de ancho o alto 0** | Un clic sin arrastrar puede romper el entrenamiento entero. El script de validación lo detecta |
| `data_aug.ipynb` usa `min_visibility=0.3` y `min_area=100` | Tras un recorte, las cajas con menos del 30 % visible o menos de 100 px² se descartan. Nuestro umbral del 30 % (R4/R5) y el mínimo de 10 px (R6) coinciden con esos valores, así que los datos aumentados siguen el mismo criterio que los originales |
| Faster R-CNN (`faster_rcnn_v1`) reescala las imágenes de 720p con un factor de ~1,04, y su *anchor* más pequeño es de 32 px | Los robots de menos de ~30 px quedan por debajo del *anchor* mínimo y se detectan peor. Por eso conviene marcarlos (R6) para medirlos aparte |

---

## 3. Reglas con su justificación

### R1. Qué es un `robot`

**Regla.** Cualquier RoboMaster físico (EP o S1) visible en la escena, sea cual sea el color de sus LED, su orientación (de frente, de espaldas, de lado o en tres cuartos), la posición del gimbal o su equipo. Hay una única clase, que se escribe `robot` en minúsculas y sin espacios.

**Por qué.**
- El enunciado pide una sola clase, y en el Bloque 3 hay que detectar a cualquier rival.
- Si más adelante hace falta distinguir aliados de rivales, se puede hacer **después** de detectar, por ejemplo con el color de los LED dentro de la caja. No hace falta una segunda clase ahora, que además dividiría por dos los ejemplos de cada una.
- Escribir el nombre siempre igual evita problemas en el EDA y en `data_aug`, que sí leen el `name`. labelImg en *Single Class Mode* lo hace automáticamente.

### R2. Qué no se anota

**Regla.** No se pone caja a:
- **nuestro propio robot**: la punta naranja del cañón y cualquier parte de nuestro chasis;
- **reflejos** de robots en el suelo o en cristales;
- robots que aparecen en **pantallas** (móviles con la app), carteles o fotos;
- **sombras**;
- otros objetos: motos expuestas (`V01`, `V07`), sillas, mandos, zapatos.

**Por qué.**
- Nuestro cañón está en el 100 % de las imágenes y siempre en el mismo sitio. Si se anotara, aunque fuera por error en unas pocas, la red aprendería un falso positivo permanente que en el Bloque 3 la haría «dispararse a sí misma».
- Los reflejos son muy frecuentes en V01, V06, V07 y V08. Si se anotaran, la red aprendería a detectar robots invertidos en el suelo.

### R3. Hasta dónde llega la caja

**Regla.** La caja encierra la **silueta visible** del robot: chasis, ruedas, gimbal y lanzador, incluido el cañón aunque sobresalga. Cada borde va al último píxel del robot, con ±2 px de tolerancia. Quedan **fuera**:
- las **dos antenas**;
- la sombra;
- el reflejo en el suelo (la caja acaba donde las ruedas tocan el suelo);
- el halo de luz que proyectan los LED.

**Por qué.**
- **Antenas fuera:** son líneas finas que solo se ven de cerca (`V05 ~0:24`) y desaparecen con la distancia (`V05 ~0:01`). Si se incluyeran, el borde superior de la caja dependería de la distancia y no del robot, y añadirían mucho fondo. Además desplazarían el centro de la caja hacia arriba, y en el Bloque 3 ese centro es el punto al que apuntaremos.
- **Cañón dentro:** es grueso, se ve a cualquier distancia y forma parte de la silueta. Cortarlo obligaría a decidir «a ojo» dónde termina el robot, que es justo lo que genera inconsistencias.
- **Reflejo y halo fuera:** en suelos pulidos el reflejo prolonga el robot hacia abajo. Incluirlo agrandaría las cajas solo en algunos escenarios y sesgaría la distribución de tamaños del EDA.
- **±2 px:** la red aprende a dibujar las cajas exactamente como las dibujamos nosotros. En un robot lejano de 30x25 px, un desfase de 3 px en horizontal y otros 3 en vertical deja el IoU en torno a 0,66.

### R4. Oclusión: robots tapados

**Regla.**
- La caja cubre **solo la parte visible** del robot, sin imaginar la parte tapada.
- Si un obstáculo **fino** cruza el robot por delante (la pata de una silla o una pierna), la caja abarca el robot entero de un lado a otro del obstáculo.
- Se anota si el robot **se reconoce** y se ve aproximadamente un **30 %** o más.
- Si se ve menos de la mitad, se marca `difficult`.
- Si está tapado por otro robot, cada uno lleva su caja. La del robot de detrás cubre solo lo que se le ve.

**Por qué.**
- La red solo puede aprender lo que ve, y en el Bloque 3 solo se puede acertar a la parte visible del robot. Imaginar la parte tapada da resultados distintos según quién anote.
- El 30 % coincide con el `min_visibility=0.3` de `data_aug.ipynb` (sección 2.2).
- En el Bloque 3 los robots estarán detrás de obstáculos fijos, así que nos interesa que la red los detecte aunque estén medio tapados (`V02 ~0:24`, `V09 ~0:44`).

### R5. Robots cortados por el borde de la imagen

**Regla.**
- Se aplica el mismo umbral que en R4 (reconocible y un 30 % visible o más), y la caja llega **hasta el borde** (`xmin = 0`, `xmax = 1280`, etc.). labelImg marca automáticamente el campo `truncated`.
- Los robots **muy cercanos** que llenan media imagen se anotan siempre que se reconozcan (`V04 ~0:52`, `V09 ~0:23`), aunque solo se vea el gimbal con el cañón (`V09 ~0:34`).

**Por qué.**
- Un rival a medio metro es justo el caso más importante en una partida, y si no se anota la red aprende a ignorarlo.
- Al borde de la imagen entran y salen robots continuamente: es una situación normal, no un error.

### R6. Robots lejanos y pequeños

**Regla.**
- Se anotan todos los robots **reconocibles** cuyo lado menor mida **10 px o más**. Para dibujarlos con precisión hay que usar el zoom de labelImg (Ctrl + rueda del ratón).
- Si el ancho de la caja es **menor de 30 px**, se marca `difficult`.
- Por debajo de 10 px no se anota, y si es seguro que hay un robot, se apunta en casos dudosos.

**Por qué.**
- **Dejar un robot pequeño sin caja enseña a la red que eso es fondo.** Es mejor anotarlo y dejar que aprenda.
- Los 10 px coinciden con el `min_area=100` de `data_aug.ipynb`. Por debajo no se distingue un robot de una mancha, y anotarlo sería adivinar.
- Los 30 px corresponden al *anchor* más pequeño de Faster R-CNN (sección 2.2). Marcarlos permite medir en el EDA y en la evaluación cuánto empeora la red con los robots lejanos, que es un análisis que encaja muy bien en la memoria.
- En el pasillo (`V05`) y en el aula (`V10`) hay muchos robots de 20 a 40 px: es uno de los rasgos de nuestro dataset.

### R7. Desenfoque de movimiento

**Regla.**
- Si el robot se reconoce, la caja cubre el **cuerpo** del robot y no la estela. Cuando el borde esté borroso, se coloca a mitad de la transición entre el robot y el fondo.
- Si el desenfoque es fuerte pero el robot se sigue reconociendo, se marca `difficult` (`V01 ~0:52`, `V03 ~0:48`, `V06 ~0:01`).
- Si **no se reconoce** (`V05 ~0:36`, una mancha en la que se adivina el robot solo porque se sabe que estaba ahí), no se pone caja y el fotograma se apunta en casos dudosos.

**Por qué.**
- El robot y la cámara se mueven en el Bloque 3, así que un desenfoque moderado es realista y conviene que la red lo vea.
- Un fotograma en el que el robot no se reconoce no aporta nada en ninguno de los dos casos. Con caja, es una caja que nadie sabe dibujar igual. Sin caja, enseña a la red que eso es fondo. Lo mejor es decidir en la depuración (T13) si se elimina, y es probable que sí.

### R8. Varios robots juntos

**Regla.** Cada robot lleva su propia caja, también cuando se solapan (`V03 ~0:24`, `V03 ~0:59`, `V05 ~0:47`). Nunca se dibuja una caja que agrupe varios robots.

**Por qué.**
- La red tiene que contar robots y apuntar a uno concreto.
- Las cajas de grupo enseñan a detectar «montones», que no existen como objeto.
- El solapamiento entre cajas es normal y Faster R-CNN lo gestiona.

### R9. Imágenes sin robots

**Regla.** Las imágenes que no tienen ningún robot se **guardan igualmente** con Ctrl+S, para que tengan un `.xml` sin objetos. Después hay que comprobar que el `.xml` existe (el script de validación lo comprueba).

**Por qué.**
- `parse_annotations` ignora las imágenes que no tienen `.xml`, así que sin él se pierden los ejemplos negativos.
- Esas imágenes enseñan a la red a **no** detectar robots en el fondo: sillas, piernas, motos o nuestro cañón.
- Un 5–10 % de imágenes negativas es razonable. Saldrán solas de los vídeos, no hay que buscarlas.

### R10. Regla de oro para los casos dudosos

**Regla.** Antes de dibujar una caja, hay que preguntarse: «Si viera **solo este fotograma**, sin el vídeo, ¿diría sin dudar que ahí hay un robot?».
- Si la respuesta es **sí**, se pone la caja, aplicando R3–R7.
- Si es **no**, no se pone caja y el fotograma se apunta en [`casos_dudosos.md`](casos_dudosos.md).

No se usa el contexto de los fotogramas anteriores o posteriores para adivinar.

**Por qué.**
- La red ve los fotogramas de uno en uno, sin contexto temporal. Si nosotros usáramos el contexto, anotaríamos cosas que la red no tiene forma de aprender.
- Resume todas las reglas anteriores en una sola pregunta, fácil de aplicar de forma consistente entre cinco personas.

---

## 4. Configuración de labelImg

Antes de empezar cada lote:

1. **Open Dir** → `data_train/ROBOMASTER_VIDEO_XX/images`.
2. **Change Save Dir** → `data_train/ROBOMASTER_VIDEO_XX/labels`. Hay que comprobarlo **en cada vídeo**: es el error más frecuente.
3. **View → Single Class Mode**. La primera caja pide el nombre: `robot`.
4. **View → Auto Save Mode**, para no perder trabajo al pasar de imagen.
5. Bajo el botón *Save* debe poner **PascalVOC**. Si pone otro formato, hay que pulsarlo hasta que lo ponga.

Atajos útiles:

| Atajo | Acción |
|---|---|
| `w` | Nueva caja |
| `d` / `a` | Imagen siguiente / anterior |
| `Ctrl+S` | Guardar (también en las imágenes sin robots) |
| `Ctrl` + rueda del ratón | Zoom (imprescindible para los robots lejanos) |
| Casilla *difficult* | Está en el panel derecho, después de seleccionar la caja |

---

## 5. Proceso para que las anotaciones sean consistentes

1. **Ronda de calibración** (cierra la tarea T01, unos 30 minutos por persona):
   - Se eligen 20 fotogramas comunes, dos por vídeo, incluidos los casos difíciles citados en la sección 2.1.
   - Cada persona los anota **por su cuenta** en su propia carpeta (`calibracion/<nombre>/`).
   - Se calcula el acuerdo entre todos:
     ```bash
     python herramientas/revisar_anotaciones.py acuerdo calibracion/javier calibracion/alejandro calibracion/monica calibracion/pedro calibracion/daniel
     ```
   - **Objetivo:** un IoU medio de 0,80 o más entre parejas, y casi ningún robot anotado por una persona pero no por otra.
   - Las imágenes que el script marca se comentan en grupo, y si alguna regla se interpreta de forma distinta, se aclara en este documento.
   - Este dato (el acuerdo entre anotadores antes y después de la calibración) es una justificación muy sólida para la memoria.
2. **Anotación por lotes** (T04–T08), siguiendo la chuleta de la sección 1.
3. **Validación automática** antes de dar un lote por terminado:
   ```bash
   python herramientas/revisar_anotaciones.py validar ../data_train
   ```
   Comprueba lo siguiente:
   - que no haya imágenes sin `.xml` ni `.xml` sin imagen;
   - que la clase se llame exactamente `robot`;
   - que no haya cajas degeneradas ni que se salgan de la imagen;
   - que no haya cajas de menos de 10 px, robots de menos de 30 px sin `difficult` ni cajas duplicadas;
   - qué porcentaje de imágenes no tiene robots.

   El lote no se da por terminado mientras queden **errores**.
4. **Revisión cruzada** (T10): cada uno revisa visualmente el lote de otra persona. Los errores los corrige quien anotó el lote.
5. **Casos dudosos:** todo lo que no encaje en las reglas se apunta en [`casos_dudosos.md`](casos_dudosos.md) con el vídeo, el fotograma, el problema y la decisión tomada. Sirve para la depuración (T13) y para la memoria.

---

## 6. Qué contar en la memoria

- La **tabla de reglas** de la sección 1 y la justificación de las que no son obvias: las antenas fuera, el umbral del 30 % y por qué coincide con `data_aug`, el mínimo de 10 px, `difficult` por debajo de 30 px, y por qué es mejor no poner caja que poner una dudosa.
- El **acuerdo entre anotadores** medido en la calibración.
- Las cifras del validador: robots por imagen, porcentaje de `difficult`, porcentaje de imágenes negativas y robots cortados por el borde. Enlazan directamente con el EDA (T11–T12).
- Los casos dudosos más representativos y qué se decidió con ellos.

---

## 7. Decisiones que tiene que tomar el grupo

La opción recomendada va en negrita. Cualquier cambio hay que trasladarlo a la chuleta y al script (las constantes `LADO_MINIMO` y `LADO_DIFICIL`).

| Decisión | Recomendación | Alternativa | Qué cambia |
|---|---|---|---|
| Antenas | **Fuera** | Dentro | Con las antenas dentro, el tamaño de la caja depende de la distancia y el centro sube |
| Cañón | **Dentro** | Fuera | Dejarlo fuera obliga a recortar el robot por la mitad, de forma poco consistente |
| Visibilidad mínima | **~30 % y reconocible** | 50 % | Con un 50 % hay más robots sin anotar que la red aprende como fondo |
| Tamaño mínimo | **10 px** | 15–20 px | Si se sube, se pierden robots lejanos del pasillo y del aula |
| `difficult` | **Ancho < 30 px, menos del 50 % visible o muy movido** | No usarlo | Sin `difficult` no se puede analizar por separado dónde falla la red |
| Fotogramas con un robot irreconocible | **Apuntarlos y decidir en T13 (probablemente eliminarlos)** | Anotarlos igualmente | Anotarlos introduce cajas que nadie dibuja igual |
