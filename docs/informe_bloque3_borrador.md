> **Borrador del Bloque 3** para la memoria de la entrega 3 (T23), empezado el 06/11/2026.
> Es la fuente del texto: `herramientas/generar_entrega3.py` lo añade, con el formato de la
> plantilla, a una copia de la memoria de la entrega 2 (`docs/informes/informe_entrega3.docx`).
> Lo marcado como [PENDIENTE] falta por medir en el laboratorio o por decidir. Las líneas que
> empiezan por `>` no pasan a la memoria. El texto evita nombres de variables y funciones,
> como pidió la revisión de la entrega 1.

# 13. Integración del detector en el robot

El Bloque 3 lleva el detector del Bloque 2 al RoboMaster EP, y añade un circuito en el que busca a los robots rivales con la cámara de la torreta, apunta y les dispara con el emisor de infrarrojos. El modelo es el elegido en el apartado 11.6: Faster R-CNN v2 con tasa de aprendizaje 10^−3^ y umbral de confianza 0,95.

El programa se ejecuta en un portátil unido al robot por wifi, con el SDK oficial [28] en Python 3.8. Esa versión de Python no admite la GPU del portátil, así que la inferencia se hace en CPU: en el portátil del laboratorio tardó entre 2,2 y 2,4 s por imagen, y 1,1 s en uno de 32 hilos de uno de los integrantes del grupo. Esa latencia condiciona casi todas las decisiones de este bloque, pues el robot no puede mirar y moverse a la vez como lo haría con 10 imágenes por segundo, y hay que repartir el tiempo entre girar, mirar y disparar.

La configuración del circuito (velocidades, paradas, ángulos de la torreta, umbral y audios) está separada del programa, para ajustarla en el laboratorio sin tocar la lógica. Un robot simulado sustituye al SDK y permite ejecutar la demo completa sin el RoboMaster, con imágenes del conjunto de test.

## 13.1. Límites del enunciado y seguridad

El enunciado limita la velocidad del chasis a 0,5 m/s y 30 º/s y la de la torreta a 30 º/s. El programa recorta cualquier velocidad pedida a esos topes. Por otro lado, cada orden de movimiento lleva un tiempo máximo: si el robot no la confirma a tiempo, la demo se detiene.

# 14. El circuito

El recorrido se define sobre un plano con el origen en la salida de nuestro robot, en metros. Cada tramo es un desplazamiento del chasis sin girarlo, ya que las ruedas mecanum permiten moverse hacia los lados y hacia atrás. Se ha preparado en el laboratorio, donde de momento solo se ha medido P1. La Figura B3.1 muestra el recorrido completo y la Tabla B3.1, cada movimiento.

![Figura B3.1. Recorrido de la demo con la longitud y la velocidad de cada tramo. Azul: desplazamientos; naranja: ataques en marcha; granate: rivales y movimiento del rival 2; rojo discontinuo: distancia de tiro.](informes/figuras/circuito_demo.png)

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

En la primera prueba del laboratorio, el robot tenía que recorrer 2,85 m en línea recta y se quedó a mitad de camino. La orden de movimiento por distancia del SDK no recibe la velocidad en m/s reales: en las mediciones vimos que el robot avanzaba a unos 0,06 m/s al principio, por lo que se optó por sustituirla por órdenes de velocidad de 0,5 m/s, repetidas 20 veces por segundo y controladas con la odometría.

# 15. Detección, puntería y disparo

En cada parada, la torreta gira hacia los distintos ángulos establecidos y captura una imagen en cada posición para detectar posibles objetivos. Cuando identifica uno, utiliza su posición dentro de la imagen para calcular cuánto debe corregir su orientación. Para ello, tiene en cuenta tanto el ángulo en el que se encuentra la torreta como la distancia horizontal entre el centro de la imagen y el objetivo. Este mismo procedimiento se aplica en vertical para ajustar la inclinación y dirigir la torreta hacia el punto detectado.

## 15.1. Puntería por pasos

Durante las pruebas en el laboratorio, el robot conseguía detectar al rival con niveles de confianza de entre 0,96 y 1,00, pero no llegaba a disparar. La torreta realizaba movimientos bruscos y, en ocasiones, las imágenes utilizadas para confirmar la detección aparecían sin objetivos o mostraban franjas verticales.

Tras analizar el problema, vimos que el origen estaba en la gestión del vídeo. El SDK almacena las imágenes en una cola con capacidad para 64 elementos. Mientras el modelo procesa una imagen o la torreta está girando, el flujo de vídeo deja de leerse y la cola termina llenándose. Esto bloquea el decodificador y provoca que las imágenes recibidas posteriormente sean antiguas o lleguen dañadas. Como consecuencia, la torreta ajustaba su puntería utilizando imágenes que no reflejaban su posición actual (Figura B3.2).

Para solucionarlo, incorporamos un hilo independiente que lee continuamente el vídeo y conserva únicamente la imagen más reciente. Además, cada nuevo análisis espera a recibir una imagen capturada después del último giro y con la torreta ya detenida. De esta forma, nos aseguramos de que los ajustes de puntería se realizan utilizando imágenes actualizadas.

![Figura B3.2. Imágenes de la cámara del robot en el laboratorio el 4 y el 5 de noviembre: a) rival detectado y centrado con confianza 1,00; b) la foto de un RoboMaster en su caja también se detecta como robot; c) imagen corrupta por la cola de vídeo llena.](informes/figuras/bloque3/laboratorio.jpg)

Una vez garantizada la fiabilidad de las imágenes, la puntería se realiza de forma progresiva. En cada captura, la torreta comprueba la posición del rival y corrige su orientación para acercarlo al centro de la imagen. Este proceso puede repetirse hasta cuatro veces, y el disparo se realiza cuando el error de orientación es inferior a 3° o representa menos del 30 % del ancho de la caja de detección.

Cuando es necesario realizar un giro amplio, este se divide en varios movimientos de un máximo de 45°. Esta limitación responde a que el SDK solo garantiza giros de aproximadamente 55° por cada movimiento.

[PENDIENTE: comprobar en el laboratorio que dispara con la cámara corregida; número de correcciones y error final medido.]

## 15.2. Ataque en marcha

En dos de los tramos, el robot debe disparar mientras continúa avanzando, sin necesidad de detenerse para apuntar. Para conseguirlo, el funcionamiento se divide en tres tareas que se ejecutan simultáneamente: el chasis mantiene el movimiento mediante su propio control de velocidad, la torreta se encarga de localizar y seguir al rival mediante el análisis de imágenes, y una tercera tarea gestiona el aviso de voz y la secuencia de disparos. De esta forma, el lanzamiento de la ráfaga no interrumpe el análisis de imágenes. Esta separación es especialmente importante porque las órdenes de movimiento del chasis caducan a los 0,5 segundos, mientras que el procesamiento de cada imagen tarda aproximadamente 2 segundos.

La velocidad del retroceso se ha calculado teniendo en cuenta el tiempo necesario para completar todas estas operaciones. El giro inicial de 90° de la torreta requiere unos 3 segundos; la detección del rival, entre 2 y 4 segundos, dependiendo de si es necesario analizar una o dos imágenes; el aviso de voz dura 1,4 segundos y la ráfaga completa, 6,2 segundos. Con una velocidad de retroceso de 0,1 m/s, recorrer los 1,25 metros previstos lleva aproximadamente 12,5 segundos, un tiempo que permite completar todas estas acciones durante el desplazamiento.

Mientras se ejecuta la ráfaga, la torreta sigue apuntando al rival. Para ello, estima su velocidad angular a partir de las detecciones obtenidas en imágenes consecutivas y añade una corrección proporcional al error de orientación. Como la torreta continúa girando mientras se procesa la siguiente imagen, aplicar toda la corrección de golpe podría provocar movimientos excesivos. Por este motivo, cada ajuste se limita al 80 % del error detectado.

En el retroceso de R1 el objetivo también se mueve: es el rival 2. Se trata de otro robot situado a 1,2 metros a la izquierda de la trayectoria de retroceso, que recorre 0,75 metros a una velocidad de 0,05 m/s en el mismo sentido que nuestro robot. Su movimiento lo controla un compañero desde otro portátil mediante un script independiente. Al comenzar el tramo, la demostración le envía una señal a través de la red del laboratorio para iniciar su movimiento. Si esta comunicación falla, el desplazamiento puede iniciarse manualmente.

Para poder apuntar a un objetivo que también está en movimiento, se incorporaron tres mecanismos adicionales:

**Selección de la imagen más nítida.** El movimiento del chasis puede provocar que algunas capturas salgan borrosas. Para reducir este problema, se conservan las imágenes recibidas durante los últimos 0,2 segundos y se selecciona la que presenta mayor nitidez, calculada mediante la varianza del laplaciano. También se tiene en cuenta el ángulo que tenía la torreta en el momento de capturarla, para que la corrección de puntería corresponda a la posición real de la imagen.

**Predicción del movimiento del rival.** Desde la primera detección, el sistema estima cómo cambiará la posición del objetivo dentro de la imagen. Así, la torreta puede anticiparse a su movimiento sin tener que esperar a una segunda captura. A partir de la distancia entre ambos robots y de sus respectivas velocidades, se calcula que el rival 2 se desplaza hacia atrás en la imagen a una velocidad aproximada de 2,4°/s. Una vez emitido el aviso de voz, la torreta comienza a girar anticipándose a ese desplazamiento y continúa ajustando su orientación con cada nueva imagen.

**Compensación al detener el chasis.** Cuando nuestro robot termina el retroceso, el rival sigue avanzando. Esto hace que su posición aparente cambie de sentido dentro de la imagen. Para evitar que la torreta interprete ese cambio como un movimiento propio del objetivo, el sistema descuenta de la velocidad angular estimada la parte correspondiente al movimiento de nuestro robot, sin necesidad de esperar a una nueva captura.

El objetivo del último tramo se encuentra sobre una plataforma elevada entre 20 y 40 centímetros. Esta diferencia de altura obliga a trabajar con una inclinación vertical de la torreta. Por ejemplo, si el robot objetivo está 30 centímetros por encima del cañón, el ángulo necesario es de aproximadamente 17° a una distancia de 1 metro y de 9° a 2 metros. Ambos valores están dentro del margen de inclinación de 30° que admite la torreta. Por ello, comienza buscando con una inclinación inicial de 10° y, una vez detectado el objetivo, ajusta la orientación vertical utilizando su posición dentro de la imagen.

[PENDIENTE: probar el ataque en marcha en el laboratorio con el rival 2 en movimiento y medir cuántos impactos registra cada rival.]

## 15.3. Disparo, sonido y luces

Cada ráfaga son 20 disparos de infrarrojos, cada 0,3 s. El enunciado pide 12 impactos, y los 8 de más cubren los que el rival no registre.

En las primeras pruebas, el sonido de disparo de la SCAR apenas se escuchaba. El clip original tenía una duración de 0,19 segundos, pero el altavoz del robot cortaba el inicio de cada reproducción. Además, el SDK transfería el archivo por FTP en cada disparo, lo que añadía tiempo y dificultaba sincronizar el sonido con la acción.

Para solucionarlo, aumentamos el volumen aproximadamente 9 dB, aplicando una saturación suave para evitar que el audio distorsionara en exceso. También añadimos 0,3 segundos de silencio al principio, de modo que el altavoz no cortase el sonido original. Por último, en lugar de enviar un archivo por cada disparo, preparamos una única pista de 6,2 segundos que contiene los 20 disparos de la ráfaga. Cada disparo se ejecuta en el momento correspondiente de la reproducción, consiguiendo que el sonido coincida con los disparos del robot.

El sistema también incorpora diferentes efectos de sonido para acompañar la demostración. Cuando detecta un rival, reproduce el aviso de voz «Enemy spotted», con una duración de 1,4 segundos. La ráfaga no comienza hasta que termina este aviso.

Durante la primera recta se reproduce el sonido de un Fórmula 1, ajustado a los 6,4 segundos que dura el tramo. El paso del coche se sitúa aproximadamente a mitad del recorrido y el sonido termina cuando el robot frena.

Al finalizar la demostración, el robot realiza un baile acompañado de la canción de Super Estrella, mientras los LED cambian de color diez veces por segundo hasta que termina la música.

Además de los efectos visuales, los LED sirven para indicar el estado del sistema: el color ámbar señala que está buscando objetivos, el rojo parpadeante indica que está disparando y el verde confirma que ha eliminado a un rival.

# 16. Robot camuflado y robots aliados

Para la demo se buscó un señuelo, algo con aspecto de robot al que nuestro RoboMaster no disparase. Se generaron con una IA de imágenes un RoboMaster disfrazado de detective y cuatro robots aliados marcados en verde, y se pasaron por el detector tal cual y dentro de la cámara (Tabla B3.2).

| Imagen | Confianza máxima | Veces que dispararía (de 5) | Verde dentro de la caja |
|---|---|---|---|
| RoboMaster disfrazado de detective | 98,8 a 99,9 % | 5 | 0,0 % |
| Aliado: RoboMaster S1 con bandera verde | 99,8 a 99,9 % | 5 | 5,7 % |
| Aliado: robot con orugas y cabeza redonda | 99,8 a 99,9 % | 5 | 11,0 % |
| Aliado: robot en dibujo | 92,7 a 97,9 % | 3 | 7,6 % |
| Aliado: robot blanco | 95,4 a 98,9 % | 5 | 12,5 % |

*Tabla B3.2. Respuesta del detector a imágenes de robots que no son RoboMasters reales.*

![Figura B3.3. Robot camuflado de la demo (izquierda) y uno de los aliados probados (derecha).](informes/figuras/senuelo/detective.jpg|informes/figuras/senuelo/aliado_s1.jpg)

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

*Tabla B3.3. Robot camuflado impreso y en pantalla delante de la webcam del portátil, con el detector de la demo.*

En las pruebas realizadas el detector reconoce correctamente al robot cuando este ocupa una parte considerable de la imagen. Además, no se han observado falsos positivos sobre el fondo, donde la confianza máxima registrada fue de 0,32.

Sin embargo, los resultados empeoran considerablemente cuando se utiliza una pantalla. Su brillo provoca que la cámara reduzca la exposición y oscurezca el resto de la escena. A esto se suman los reflejos y los bordes del propio marco, que dificultan la identificación del contorno del robot.

Por este motivo, para la demostración se utilizará una imagen impresa sobre papel mate en formato A3. Este soporte evita los problemas de iluminación de la pantalla y permite que el robot aparezca con un tamaño suficiente para ser detectado desde P1.

[PENDIENTE: comprobarlo con la cámara del robot desde P1.]

# 17. Control manual del robot

Además del circuito autónomo, se ha preparado una interfaz para manejar el robot desde el navegador del portátil, con teclado y ratón o con un mando de PS4. Sirve para colocar el robot, probar la cámara y el detector en el laboratorio y hacer una demostración libre (Figura B3.4).

![Figura B3.4. Interfaz del mando con una imagen de nuestra cámara en el laboratorio (robot simulado).](informes/figuras/bloque3/mando.jpg)

Un servidor local conecta el robot con una interfaz web que permite visualizar el vídeo con las detecciones y controlarlo en tiempo real. Si deja de recibir órdenes durante 0,3 segundos, el robot se detiene automáticamente.

La interfaz permite controlar el movimiento del chasis y la torreta, disparar infrarrojos y ejecutar bailes. También incorpora límites de velocidad y seguridad, y los bailes están pensados para no salir de un área de 1 × 1 m.

El detector funciona en un proceso independiente y aprovecha la GPU del portátil, reduciendo el análisis de imágenes a 32-94 ms. Esto permite habilitar el disparo automático bajo condiciones estrictas de confianza y antigüedad de la detección.

El servidor cuenta con 31 pruebas automáticas, y se ha probado tanto con el robot simulado como con un mando de PS4.

[PENDIENTE: probarlo con el robot real, primero sobre una caja y después en el suelo, y medir el retardo del vídeo.]

# 18. Pruebas y estado

Cada ejecución genera un registro con las imágenes analizadas, las detecciones y sus confianzas, los movimientos de la torreta, los tiempos de inferencia y los disparos realizados. También se guarda un resumen de los objetivos atacados y la duración de cada tramo.

En las pruebas de laboratorio se verificaron la conexión, el recorrido de 2,85 m en unos 6 segundos y la detección del rival de P1, con confianzas de entre 0,96 y 1,00. Sin embargo, un problema en la cámara impidió completar los disparos. Tras corregirlo, la demostración completa se ejecutó en simulación, atacando los dos objetivos de P1 con 20 disparos cada uno, siguiendo a los rivales de R1 y R2 y finalizando con el baile.

También se desarrollaron mejoras para seguir objetivos móviles, evitar ataques repetidos y vigilar el recorrido. Aunque están probadas en simulación, su activación en el laboratorio se realiza progresivamente, ya que requieren calibraciones adicionales.

[PENDIENTE: resultados del laboratorio con el circuito montado (aciertos, falsos positivos, robots no vistos, impactos registrados por cada rival y tiempos), reparto del Bloque 3 de Mónica, Pedro José y Daniel, numeración final de tablas y figuras, índice y límite de páginas.]

# 19. Conclusiones

[PENDIENTE: revisar con los resultados del laboratorio.]

**Datos.** El aumento de datos ha sido la mejora más importante, especialmente para los robots difficult. Su anotación también en validación y test ha permitido identificar los principales fallos del detector.

**Modelo.** La arquitectura tiene más impacto que los ajustes de entrenamiento. Faster R-CNN v2 es el modelo final, con un AP@0,5 de 0,95 en test. Sin embargo, sigue teniendo dificultades con los objetivos más complejos y todos los modelos presentan sobreajuste temprano.

**Robot.** La latencia del detector condiciona el funcionamiento: el robot debe repartir el tiempo entre movimiento, detección y disparo, utilizando imágenes recientes y nítidas. Además, el modelo reconoce qué es un robot, pero no distingue aliados de rivales, por lo que necesita una marca adicional para diferenciarlos.
