> **Borrador del Bloque 3** para la memoria de la entrega 3 (T23), empezado el 06/11/2026.
> Es la fuente del texto: `herramientas/generar_entrega3.py` lo añade, con el formato de la
> plantilla, a una copia de la memoria de la entrega 2 (`docs/informes/informe_entrega3.docx`).
> Lo marcado como [PENDIENTE] falta por medir en el laboratorio o por decidir. Las líneas que
> empiezan por `>` no pasan a la memoria. El texto evita nombres de variables y funciones,
> como pidió la revisión de la entrega 1.

# 13. Integración del detector en el robot

El Bloque 3 lleva el detector del Bloque 2 al RoboMaster EP. El robot recorre un circuito, busca a los robots rivales con la cámara de la torreta, apunta y les dispara con el emisor de infrarrojos. El modelo es el elegido en el apartado 11.6: Faster R-CNN v2 con tasa de aprendizaje 0,001 y umbral de confianza 0,95.

El programa se ejecuta en un portátil unido al robot por wifi, con el SDK oficial en Python 3.8. Esa versión de Python no admite la GPU del portátil, así que la inferencia se hace en CPU y tarda unos 2 s por imagen. Esa latencia condiciona casi todas las decisiones de este bloque: el robot no puede mirar y moverse a la vez como lo haría con 10 imágenes por segundo, y hay que repartir el tiempo entre girar, mirar y disparar.

La configuración del circuito (velocidades, paradas, ángulos de la torreta, umbral y audios) está separada del programa, para ajustarla en el laboratorio sin tocar la lógica. Un robot simulado sustituye al SDK y permite ejecutar la demo completa sin el RoboMaster, con imágenes del conjunto de test.

## 13.1. Límites del enunciado y seguridad

El enunciado limita la velocidad del chasis a 0,5 m/s y 30 º/s y la de la torreta a 30 º/s. El programa recorta cualquier velocidad pedida a esos topes. Cada orden de movimiento lleva un tiempo máximo: si el robot no la confirma a tiempo, la demo se detiene en lugar de quedarse esperando. Las órdenes de velocidad del chasis caducan a los 0,5 s, así que si el programa se bloquea el robot se para solo. Una interrupción, un error o el final de la demo detienen el chasis, centran la torreta, apagan los LED y guardan las evidencias.

# 14. El circuito

El recorrido se define sobre un plano con el origen en la salida de nuestro robot, en metros. Cada tramo es un desplazamiento del chasis sin girarlo: las ruedas mecanum permiten moverse hacia los lados y hacia atrás. Se ha preparado y medido movimiento a movimiento en el laboratorio, y no se pasa al siguiente hasta comprobar el anterior en el robot real. La Figura B3.1 muestra el recorrido completo y la Tabla B3.1, cada movimiento.

![Figura B3.1. Recorrido de la demo con la longitud y la velocidad de cada tramo. Azul: desplazamientos; naranja: ataques en marcha; granate: rivales y movimiento del rival 2; rojo discontinuo: distancia de tiro. Las posiciones de los rivales son las previstas para el montaje y aún no se han comprobado en el laboratorio.](informes/figuras/circuito_demo.png)

| Tramo | Movimiento | Velocidad | Tiempo | Acción |
|---|---|---|---|---|
| P1 | 2,85 m adelante | 0,5 m/s | unos 6 s (medido) | Suena un coche de Fórmula 1 ajustado a la recta |
| P1 | Parada | — | — | Torreta a la derecha (90º): rival 1. Torreta a la izquierda (−90º): robot camuflado |
| R1 | 1,9 m adelante | 0,4 m/s | unos 5 s | — |
| R1 | 1 m a la izquierda | 0,5 m/s | unos 2,5 s | — |
| R1 | 1,25 m atrás | 0,1 m/s | unos 12,5 s | Torreta a la izquierda: rival 2, que avanza en paralelo a 0,05 m/s, sin parar |
| R1 | 1 m a la derecha | 0,5 m/s | unos 2,5 s | — |
| R2 | 2,5 m adelante | 0,5 m/s | unos 5,5 s | — |
| R2 | 0,7 m a la izquierda | 0,5 m/s | unos 2 s | — |
| R2 | 2 m adelante | 0,1 m/s | unos 20 s | Torreta hacia atrás (180º) e inclinada: rival 3, en alto, sin parar |
| Final | Baile | — | lo que dure la canción | Música, torreta y chasis bailando y LED de colores |

*Tabla B3.1. Movimientos del circuito. Solo P1 está medido en el laboratorio; R1 y R2 son supuestos hasta montar el circuito. Los tiempos incluyen la frenada al final de cada tramo.*

[PENDIENTE: medidas reales de R1 y R2, posiciones de los rivales y foto del circuito montado.]

## 14.1. Avance a la velocidad pedida

En la primera prueba del laboratorio, el robot tenía que recorrer 2,85 m en línea recta y se quedó a mitad de camino. La orden de movimiento por distancia del SDK no recibe la velocidad en m/s reales: cualquier valor por debajo de 0,5 se sube a ese mínimo interno y el robot avanzaba a unos 0,06 m/s. Se sustituyó por órdenes de velocidad repetidas 20 veces por segundo, medidas con la odometría del propio robot. El robot avanza a la velocidad pedida, frena en los últimos 17 cm, se para a 1 cm del destino y corrige la deriva lateral. Con 0,5 m/s, los 2,85 m se recorren en unos 6 s, como se comprobó en el laboratorio el 05/11.

# 15. Detección, puntería y disparo

En cada parada, la torreta gira hacia los ángulos previstos y analiza una imagen en cada uno. Las detecciones que superan el umbral se convierten en un ángulo: la torreta conoce su propia orientación y el desplazamiento horizontal de la caja respecto al centro de la imagen da cuánto falta girar, con la geometría de la cámara. Lo mismo se hace en vertical para inclinar la torreta.

## 15.1. Puntería por pasos

En el laboratorio el robot detectaba al rival con confianzas de 0,96 a 1,00, pero no llegaba a disparar: la torreta daba saltos y las imágenes de confirmación salían sin detecciones o con franjas verticales. La causa estaba en el vídeo. El SDK guarda las imágenes en una cola de 64 y, mientras el modelo analiza una imagen o la torreta gira, nadie la lee. La cola se llena, el decodificador se bloquea y las imágenes siguientes llegan viejas o corruptas, así que la puntería se corregía con una foto de antes del último giro. Ahora un hilo lee el vídeo todo el tiempo y guarda solo la última imagen, y cada análisis espera a una imagen tomada después del último giro, con la torreta quieta.

Con imágenes fiables, la puntería se hace por pasos: con cada imagen se gira lo que falta para centrar al rival, hasta cuatro correcciones, y se dispara cuando el error es menor de 3º o del 30 % del ancho de la caja. Los giros grandes se dividen en tramos de 45º como máximo, porque el SDK solo garantiza unos 55º por orden.

[PENDIENTE: comprobar en el laboratorio que dispara con la cámara corregida; número de correcciones y error final medido.]

## 15.2. Ataque en marcha

En dos tramos el robot dispara sin pararse. Se reparten tres tareas que se ejecutan a la vez: el chasis avanza con su control de velocidad, la torreta gira y analiza imágenes, y la ráfaga (audio y disparos) se lanza aparte para no detener el análisis. El chasis no puede esperar a la inferencia, porque sus órdenes caducan a los 0,5 s y cada imagen tarda unos 2 s.

La velocidad del tramo sale de sumar los tiempos: girar la torreta 90º (3 s), ver al rival (una o dos imágenes de 2 s), el aviso de voz (1,4 s) y la ráfaga (6,2 s). A 0,1 m/s, el retroceso de 1,25 m dura unos 12,5 s, lo justo para todo ello. Mientras dura la ráfaga, la torreta sigue al rival: su velocidad angular se estima entre imágenes y se le suma una corrección proporcional al error. Como la torreta sigue girando mientras se analiza la imagen siguiente, la corrección se limita al 80 % del error por imagen.

El rival 2 también se mueve. Es un segundo robot, 1,2 m a la izquierda del tramo de retroceso, que avanza 0,75 m a 0,05 m/s en el mismo sentido que el nuestro. Lo mueve un compañero desde otro portátil con un script propio. La demo le manda un aviso por la red del laboratorio al empezar el tramo, y si el aviso no llega se arranca a mano. Para un blanco que se mueve se han añadido tres cosas.

**Imagen nítida.** Con el robot en marcha algunas imágenes salen movidas. De las que llegan en los últimos 0,2 s se analiza la más nítida, medida con la varianza del laplaciano. Se usa el ángulo que tenía la torreta cuando se tomó esa imagen.

**Velocidad prevista.** Desde la primera detección se prevé cuánto se desplaza el rival en la imagen. La torreta no espera a una segunda imagen para seguirlo. Con la distancia del plano y las velocidades de los dos robots, el rival 2 se queda atrás unos 2,4 º/s. Tras la voz de aviso, la torreta apunta a donde estará el rival y empieza a girar a esa velocidad. Después la corrige con cada imagen.

**Parada de nuestro robot.** Cuando nuestro robot se para, el rival sigue avanzando y cambia de sentido en la imagen. La torreta le quita a la velocidad estimada la parte que venía de nuestro movimiento sin esperar a la siguiente imagen.

El rival del último tramo está sobre una plataforma de 20 a 40 cm. Un robot 30 cm más alto que el cañón queda a unos 17º de inclinación a 1 m y a unos 9º a 2 m, dentro de los 30º que admite la torreta. La torreta lo busca inclinada 10º y, al verlo, corrige la inclinación con la caja detectada.

[PENDIENTE: probar el ataque en marcha en el laboratorio con el rival 2 en movimiento y medir cuántos impactos registra cada rival.]

## 15.3. Disparo, sonido y luces

Cada ráfaga son 20 disparos de infrarrojos, cada 0,3 s. El enunciado pide 12 impactos, y los 8 de más cubren los que el rival no registre.

El sonido de la SCAR no se oía en la primera prueba. El clip original dura 0,19 s, el altavoz del robot se come el principio de cada audio y el SDK lo subía por FTP en cada disparo. Se subió el volumen unos 9 dB con saturación suave, se añadió 0,3 s de silencio delante y la ráfaga se convirtió en un solo audio de 20 disparos, de 6,2 s. Cada disparo se lanza en su instante del audio, así que se oye a la vez que el robot dispara.

Al detectar un rival suena una voz de "enemy spotted" de 1,4 s, y la ráfaga espera a que termine. En la primera recta suena un coche de Fórmula 1 recortado a la duración del tramo (6,4 s): el coche pasa a mitad de la recta y el sonido se apaga cuando el robot frena. Al terminar, el robot baila con Super Estrella mientras los LED cambian de color diez veces por segundo, hasta que acaba la canción. Los LED indican también el estado: ámbar buscando, rojo parpadeando al disparar y verde tras eliminar a un rival.

# 16. Robot camuflado y robots aliados

Para la demo se buscó un señuelo: algo con aspecto de robot al que nuestro RoboMaster no disparase. Se generaron con una IA de imágenes un RoboMaster disfrazado de detective y cuatro robots aliados marcados en verde, y se pasaron por el detector tal cual y dentro de un fotograma de la cámara, ocupando del 80 al 20 % del alto (Tabla B3.2).

| Imagen | Confianza máxima | Veces que dispararía (de 5) | Verde dentro de la caja |
|---|---|---|---|
| RoboMaster disfrazado de detective | 98,8 a 99,9 % | 5 | 0,0 % |
| Aliado: RoboMaster S1 con bandera verde | 99,8 a 99,9 % | 5 | 5,7 % |
| Aliado: robot con orugas y cabeza redonda | 99,8 a 99,9 % | 5 | 11,0 % |
| Aliado: robot en dibujo | 92,7 a 97,9 % | 3 | 7,6 % |
| Aliado: robot blanco | 95,4 a 98,9 % | 5 | 12,5 % |

*Tabla B3.2. Respuesta del detector a imágenes de robots que no son RoboMasters reales. Dispara con una confianza de 0,95 o más.*

![Figura B3.2. Robot camuflado de la demo (izquierda) y uno de los aliados probados (derecha). El detector los ve a los dos como robots con más del 99 % de confianza.](informes/figuras/senuelo/detective.jpg|informes/figuras/senuelo/aliado_s1.jpg)

El disfraz no engaña al detector, y tampoco una forma de robot distinta. Tapando partes del detective, la confianza apenas baja si se tapa una sola (ruedas, cañón o chasis); solo baja al 52 % si se tapan todas a la vez. El modelo ha aprendido el concepto de robot a partir del conjunto, no por una pieza concreta. En cambio, un círculo, una caja o una caja con ruedas dibujados no dan ninguna detección. La demo aprovecha este resultado: en P1, el robot elimina al rival de la derecha y después al robot camuflado de la izquierda.

Para no disparar a un aliado hace falta una marca, no una forma. Los aliados tienen entre un 5,7 y un 12,5 % de verde intenso dentro de su caja y el detective un 0 %, así que una regla de "más de un 2 % de verde: aliado" los separa con margen. Es como en las competiciones de RoboMaster, donde los equipos se distinguen por el color de las luces. Se ha dejado como trabajo futuro, porque la luz del laboratorio y un fondo verde detrás de un enemigo podrían confundirla. El estudio completo está en el repositorio [21].

# 17. Pruebas y estado

Cada ejecución guarda todas las imágenes analizadas con sus cajas y confianzas, un registro con el ángulo de la torreta, el tiempo de inferencia y los disparos de cada imagen, y un resumen con los rivales atacados y la duración de cada tramo. Es el material de los resultados de este bloque.

La demo completa se ha ejecutado con el robot simulado: recorre P1, R1 y R2, ataca a los cuatro objetivos con sus 20 disparos y termina con el baile. En el laboratorio, el 05/11, se comprobaron la conexión, la recta de 2,85 m en unos 6 s y la detección del rival de P1; el fallo de la cámara descrito en el apartado 15.1 impidió disparar.

El grupo preparó también mejoras para rivales que se mueven: seguimiento continuo con la torreta, barrido sin pararse, memoria de los robots ya atacados para no repetir ráfagas y vigilancia del camino durante el recorrido. Están probadas en simulación, pero se activan una a una en el laboratorio, porque dependen de calibraciones como la altura aparente de un robot.

[PENDIENTE: resultados del laboratorio con el circuito montado (aciertos, falsos positivos, robots no vistos, impactos registrados por cada rival y tiempos), conclusiones del proyecto completo, columna del Bloque 3 en el reparto del trabajo, respuesta a la revisión de la entrega 2, numeración final de tablas y figuras, índice y límite de páginas.]
