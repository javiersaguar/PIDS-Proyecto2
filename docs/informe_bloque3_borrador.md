> **Borrador del Bloque 3** para la memoria de la entrega 3 (T23), empezado el 06/11/2026.
> Es la fuente del texto: `herramientas/generar_entrega3.py` lo añade, con el formato de la
> plantilla, a una copia de la memoria de la entrega 2 (`docs/informes/informe_entrega3.docx`).
> Lo marcado como [PENDIENTE] falta por medir en el laboratorio o por decidir. Las líneas que
> empiezan por `>` no pasan a la memoria. El texto evita nombres de variables y funciones,
> como pidió la revisión de la entrega 1.

# 13. Integración del detector en el robot

El Bloque 3 lleva el detector del Bloque 2 al RoboMaster EP. El robot recorre un circuito, busca a los robots rivales con la cámara de la torreta, apunta y les dispara con el emisor de infrarrojos. El modelo es el elegido en el apartado 11.6: Faster R-CNN v2 con tasa de aprendizaje 10^−3^ y umbral de confianza 0,95.

El programa se ejecuta en un portátil unido al robot por wifi, con el SDK oficial [28] en Python 3.8. Esa versión de Python no admite la GPU del portátil, así que la inferencia se hace en CPU: en el portátil del laboratorio tardó entre 2,2 y 2,4 s por imagen, y 1,1 s en uno de 32 hilos. Esa latencia condiciona casi todas las decisiones de este bloque: el robot no puede mirar y moverse a la vez como lo haría con 10 imágenes por segundo, y hay que repartir el tiempo entre girar, mirar y disparar.

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

En el laboratorio el robot detectaba al rival con confianzas de 0,96 a 1,00, pero no llegaba a disparar: la torreta daba saltos y las imágenes de confirmación salían sin detecciones o con franjas verticales. La causa estaba en el vídeo. El SDK guarda las imágenes en una cola de 64 y, mientras el modelo analiza una imagen o la torreta gira, nadie la lee. La cola se llena, el decodificador se bloquea y las imágenes siguientes llegan viejas o corruptas, así que la puntería se corregía con una foto de antes del último giro (Figura B3.2). Ahora un hilo lee el vídeo todo el tiempo y guarda solo la última imagen, y cada análisis espera a una imagen tomada después del último giro, con la torreta quieta.

![Figura B3.2. Imágenes de la cámara del robot en el laboratorio el 4 y el 5 de noviembre: a) rival detectado y centrado con confianza 1,00; b) la foto de un RoboMaster en su caja también se detecta como robot; c) imagen corrupta por la cola de vídeo llena.](informes/figuras/bloque3/laboratorio.jpg)

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

![Figura B3.3. Robot camuflado de la demo (izquierda) y uno de los aliados probados (derecha). El detector los ve a los dos como robots con más del 99 % de confianza.](informes/figuras/senuelo/detective.jpg|informes/figuras/senuelo/aliado_s1.jpg)

El disfraz no engaña al detector, y tampoco una forma de robot distinta. Tapando partes del detective, la confianza apenas baja si se tapa una sola (ruedas, cañón o chasis); solo baja al 52 % si se tapan todas a la vez. El modelo ha aprendido el concepto de robot a partir del conjunto, no por una pieza concreta. En cambio, un círculo, una caja o una caja con ruedas dibujados no dan ninguna detección. La demo aprovecha este resultado: en P1, el robot elimina al rival de la derecha y después al robot camuflado de la izquierda.

Para no disparar a un aliado hace falta una marca, no una forma. Los aliados tienen entre un 5,7 y un 12,5 % de verde intenso dentro de su caja y el detective un 0 %, así que una regla de "más de un 2 % de verde: aliado" los separa con margen. Es como en las competiciones de RoboMaster, donde los equipos se distinguen por el color de las luces. Se ha dejado como trabajo futuro, porque la luz del laboratorio y un fondo verde detrás de un enemigo podrían confundirla. El estudio completo está en el repositorio [21].

## 16.1. Prueba con el robot camuflado impreso

El robot camuflado se imprimió en papel para colocarlo en P1. Antes de llevarlo al laboratorio se comprobó con la webcam de un portátil y el mismo modelo de la demo: 20 imágenes, una por segundo, moviendo la hoja a distintas distancias. Se repitió con la misma imagen en la pantalla de una tableta (Tabla B3.3).

| Soporte | Tamaño del robot en la imagen | Confianza máxima | ¿Dispararía? |
|---|---|---|---|
| Papel | De un tercio a la mitad del alto | 0,96 a 0,99 | Sí |
| Papel | Un cuarto del alto | 0,87 a 0,92 | No |
| Papel | Lejos | 0,53 | No |
| Tableta | De un tercio a la mitad del alto | 0,29 a 0,63 | No |
| Tableta | Casi toda la imagen | 0,55 a 0,95 | Solo pegada a la cámara |

*Tabla B3.3. Robot camuflado impreso y en pantalla delante de la webcam de un portátil, con el detector de la demo. Dispara con una confianza de 0,95 o más.*

En papel, el detector lo reconoce como robot cuando ocupa una buena parte de la imagen y nunca dio falsos positivos sobre el fondo (como mucho, 0,32). En la pantalla funciona mucho peor: el brillo hace que la cámara oscurezca la escena y los reflejos y el marco confunden los bordes del robot. Para la demo se usará el papel mate, en A3 para que se vea grande desde P1.

[PENDIENTE: comprobarlo con la cámara del robot desde P1.]

# 17. Control manual del robot

Además del circuito autónomo, se ha preparado una interfaz para manejar el robot desde el navegador del portátil, con teclado y ratón o con un mando de PS4. Sirve para colocar el robot, probar la cámara y el detector en el laboratorio y hacer una demostración libre (Figura B3.4).

![Figura B3.4. Interfaz del mando con el detector en la GPU del portátil sobre una imagen de nuestra cámara en el laboratorio (robot simulado): vídeo con la caja detectada, estado del robot y del detector, emotes y parada.](informes/figuras/bloque3/mando.jpg)

Un servidor local habla con el robot mediante el SDK, envía a la página el vídeo de la cámara con las cajas del detector y recibe las órdenes 20 veces por segundo. Un único hilo da las órdenes al robot. Si dejan de llegar durante 0,3 s, porque se cierra la página o se corta la red, el robot se para y hay que volver a activar los controles. Las velocidades tienen los mismos topes que en la demo: 0,5 m/s y 30 º/s.

El joystick izquierdo mueve el robot hacia donde mira la cámara: con la torreta girada, «adelante» es la dirección de la torreta y no la del chasis. Los botones L1 y R1 giran el chasis, el joystick derecho mueve la torreta y R2 dispara los infrarrojos. Cuatro botones lanzan bailes con música en el altavoz del robot; antes de ejecutar cada uno se comprueba que sus velocidades están dentro de los topes, que no se sale de un cuadrado de 1 × 1 m y que vuelve al punto de partida.

El detector corre en un proceso aparte, con una versión de Python que sí usa la GPU del portátil: Faster R-CNN v2 tarda unos 94 ms por imagen y Faster R-CNN MobileNet unos 32 ms, frente a 1 o 2 s en CPU. Con él, el disparo automático es opcional y solo actúa si el centro de la imagen cae dentro de una caja de confianza 0,95 o más, la detección tiene menos de 0,5 s y la torreta no se ha movido más de 2º desde que se tomó. Cada disparo automático guarda su imagen. Esta separación muestra cómo podría la demo analizar unas 10 imágenes por segundo en lugar de una cada 1 o 2 s.

El servidor tiene 31 pruebas automáticas (parada por falta de órdenes, rearme tras un baile, 15 minutos de funcionamiento con reloj simulado, disparo automático, movimiento hacia la cámara) y se ha probado con el robot simulado y con un mando de PS4 por Bluetooth.

[PENDIENTE: probarlo con el robot real, primero sobre una caja y después en el suelo, y medir el retardo del vídeo.]

# 18. Pruebas y estado

Cada ejecución guarda todas las imágenes analizadas con sus cajas y confianzas, un registro con el ángulo de la torreta, el tiempo de inferencia y los disparos de cada imagen, y un resumen con los rivales atacados y la duración de cada tramo. Es el material de los resultados de este bloque.

En el laboratorio, el 05/11, se comprobaron la conexión, la recta de 2,85 m en unos 6 s y la detección del rival de P1, con confianzas de 0,96 a 1,00; el fallo de la cámara descrito en el apartado 15.1 impidió disparar. Después de corregirlo, la demo completa se ha ejecutado con el robot simulado y fotos del conjunto de test: en P1 ataca a los dos objetivos con 20 disparos cada uno, sigue al rival 2 durante el retroceso de R1 y al rival 3 en R2, y termina con el baile.

El grupo preparó también mejoras para rivales que se mueven: seguimiento continuo con la torreta, barrido sin pararse, memoria de los robots ya atacados para no repetir ráfagas y vigilancia del camino durante el recorrido. Están probadas en simulación, pero se activan una a una en el laboratorio, porque dependen de calibraciones como la altura aparente de un robot.

[PENDIENTE: resultados del laboratorio con el circuito montado (aciertos, falsos positivos, robots no vistos, impactos registrados por cada rival y tiempos), reparto del Bloque 3 de Mónica, Pedro José y Daniel, numeración final de tablas y figuras, índice y límite de páginas.]

# 19. Conclusiones

[PENDIENTE: revisar con los resultados del laboratorio.]

**Datos.** Con 808 imágenes anotadas con criterios comunes, lo que más ha mejorado al detector ha sido el aumento de datos, sobre todo en los robots difficult. Marcar los difficult también en validación y test ha permitido ver dónde falla el modelo: en los robots movidos, tapados, cortados o lejanos.

**Modelo.** La arquitectura importa más que la tasa de aprendizaje o el perfil de aumento. Faster R-CNN v2 es el modelo final, con un AP@0,5 de 0,95 en test que confirma el de validación, pero los difficult siguen muy por debajo. Todos los modelos sobreajustan pronto, así que el checkpoint se elige con validación.

**Robot.** La latencia ha condicionado todo el Bloque 3: con una imagen cada 1 o 2 s, el robot se para a mirar, reparte el tiempo de cada tramo entre girar, ver y disparar, y necesita imágenes recientes y nítidas. El detector ha aprendido el concepto de robot: dispara al robot camuflado y a la foto de una caja, así que distinguir aliados requiere una marca, no una forma.

**Trabajo futuro.** Llevar a la demo el detector en GPU del mando para analizar unas 10 imágenes por segundo, añadir la regla de color para los aliados y grabar más robots difficult y lejanos.
