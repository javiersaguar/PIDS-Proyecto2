# Mando del RoboMaster

Interfaz local del Bloque 3 para conducir, apuntar, disparar infrarrojos y lanzar cuatro
emotes. El circuito autónomo se ejecuta desde demo.py. El mando arranca en modo libre,
con controles desarmados y AUTO apagado.

## Arranque sin robot

Desde ENTREGA 2/WEEK3, con una carpeta de imágenes propias o sintéticas:

    .venv\Scripts\python.exe mando\servidor.py --simulacion CARPETA --sin-mover

Abre http://127.0.0.1:8765 y pulsa Activar controles. La interfaz anterior sigue en
http://127.0.0.1:8765/clasico, por si la nueva falla. La simulación muestra imágenes,
batería simulada y ejecuta las órdenes con simulacion.py. Su detector devuelve cajas
vacías para distinguirla de una inferencia real. Las pruebas usan imágenes sintéticas.

## Entorno del robot

Python 3.8.20, el mismo .venv que la demo, con sus dependencias existentes.
Instala el servidor con:

    uv pip install --python .venv\Scripts\python.exe -r mando\requirements.txt

La versión de aiohttp fijada es 3.10.11. Con el robot disponible, usa la conexión de
demo_utils.connect, sin modificar la red ni connect.py:

    .venv\Scripts\python.exe mando\servidor.py --sin-mover
    .venv\Scripts\python.exe mando\servidor.py --conexion wifi

El servidor escucha solo en 127.0.0.1. Se permite una sesión de control. La vista de
conexión muestra el error y el modo intentado si connect falla. Carga la batería antes de
usar el robot. Por debajo del 10 % se rechaza el arranque y bajo el 20 % hay aviso.

### Si Windows bloquea .venv\Scripts\python.exe

En Windows 11 con Smart App Control activo puede aparecer «Una directiva de Control de
aplicaciones bloqueó este archivo» al ejecutar `.venv\Scripts\python.exe` o
`.venv-gpu\Scripts\python.exe`. uv crea los entornos con un lanzador propio sin firma
digital, y Windows decide por su reputación en la nube, por eso unos días funciona y
otros no. El intérprete de base y el lanzador estándar de CPython sí se ejecutan.

    mando\reparar_lanzador.cmd

El script sustituye `python.exe` y `pythonw.exe` de los dos entornos por el lanzador
de CPython del mismo intérprete y guarda los originales como `*.uv-original`. Los
paquetes instalados no cambian. No modifica ninguna directiva de seguridad. Hay que
repetirlo si se vuelve a crear el entorno con `uv venv`. `arrancar.cmd` comprueba el
lanzador antes de empezar y remite a este script si está bloqueado.

## Detector independiente

Entorno previsto .venv-gpu, Python 3.11, torch 2.7.1 y torchvision 0.22.1 con CUDA 12.8:

    uv venv --python 3.11 .venv-gpu
    uv pip install --python .venv-gpu\Scripts\python.exe torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
    uv pip install --python .venv-gpu\Scripts\python.exe -r mando\requirements-gpu.txt
    .venv-gpu\Scripts\python.exe mando\detector_gpu.py
    .venv-gpu\Scripts\python.exe mando\detector_gpu.py --medir 10

El proceso escucha en 127.0.0.1:8766. Reutiliza cargar_modelo y detectar, con una imagen
pendiente. La primera instalación quedó bloqueada por Control de aplicaciones. El 08/11/2026
el intérprete volvió a poder ejecutarse y se completó el entorno sin cambiar
directivas. torch 2.7.1+cu128 reconoce la RTX 5070 Laptop. Tras calentamiento y diez
imágenes sintéticas por modelo: v2 93,98 ms e v3 31,65 ms de media.

La alternativa CPU necesita models/faster_rcnn_v3/mando_pesos.pt, un checkpoint con
la clave model. El fichero facilitado por Javier se leyó con weights_only y clases
numéricas permitidas, y se exportaron solo sus 284 tensores. Se conservó el original.
En CPU, cuatro hilos y tres imágenes sintéticas tras calentamiento dieron
116,2, 117,3 y 119,6 ms. Esto mide inferencia, no precisión ni latencia del vídeo.
Los modelos siguen excluidos de Git.

AUTO exige confianza >=0,95, mira dentro de la caja encogida un 20 %, resultado de
menos de 0,3 s y controles recientes. Guarda cada imagen de disparo con Registro en
evidencias/mando/. Un resultado CPU lento se rechaza por antigüedad. El detector puede
disparar a fotografías de robots. Se activa con vigilancia y se desarma al parar.

Asistente de puntería (Ajustes → Disparo, desde el 11/11/2026): la torreta gira sola hacia
la detección más centrada que supera el umbral, a 2 º/s por grado de error y como mucho
30 º/s. Calcula el ángulo con el que tenía la torreta al tomar la imagen
(`RETARDO_CAMARA` de circuito.py), así que una detección de hace 0,1-0,2 s sigue sirviendo.
Mover el joystick derecho o las flechas le quita el control mientras se usan. Con el
asistente y el disparo automático, dispara cuando el robot queda centrado (error menor que
`TOLERANCIA_DISPARO` o que el 30 % del tamaño de la caja). Una detección de más de 1 s no
mueve la torreta.

## Controles

| Acción | Teclado / ratón | DualShock 4 |
|---|---|---|
| Desplazamiento | WASD | Joystick izquierdo |
| Girar el chasis | Z / X | L1 / R1 |
| Torreta | Flechas | Joystick derecho |
| Infrarrojos | Clic izquierdo mantenido | R2 >0,5 |
| Moonwalk | Q | □ |
| Waka Waka | E | △ |
| Super Estrella | F | ○ |
| Risa | C | ✕ |
| Parada | Esc / espacio | SHARE |
| Ajustes | Tab / engranaje | OPTIONS |

Los controles se reasignan en ajustes. La configuración se guarda en el navegador y en
config_mando.json, que es local y está en .gitignore; si no existe, se parte de
config_mando.ejemplo.json. Activar controles permite el audio mediante un gesto del usuario.
Se requiere rearmar tras una parada, perder foco o desconectar el mando. Si el servidor
desarma los controles por su cuenta (no le llegan órdenes en 0,3 s), avisa a la página y
esta vuelve a mostrar «Activar controles». Al acabar un baile los controles siguen activos.

Con «Moverse hacia donde mira la cámara» (activado por defecto), W lleva el robot en la
dirección de la torreta aunque esté girada respecto al chasis. Usa el ángulo que lee el
gimbal: al arrancar, el servidor comprueba esa lectura con un giro corto de 20º y 10º, como
la demo, y si falla lo estima con las órdenes enviadas. Z/X y L1/R1 giran el chasis a 30 º/s.

Un disparo que el robot no confirma no corta la sesión: la página avisa y se cuenta en
sin_confirmar. El disparo automático solo usa una detección de menos de 0,5 s y si la
torreta se ha movido como mucho 2º desde que se tomó la imagen (ángulo en el instante de
la imagen, con RETARDO_CAMARA). El detector CPU tarda unos 140 ms por imagen en este portátil.
Los LED solo se cambian cuando cambia su estado o su color.

Chasis limitado vectorialmente a 0,5 m/s y 30 º/s. Torreta a 30 º/s.
Cada orden del chasis caduca en 0,5 s. Sin mensajes durante 0,3 s, el Conductor para,
cancela el baile y desactiva AUTO. El centrado posterior usa velocidades cancelables.
Ctrl+C intenta parar, centrar, apagar LED, cerrar cámara y guardar evidencias.
Los tiempos efectivos de respuesta del SDK deben medirse en laboratorio.

FPS/GIMBAL_LEAD queda visible y deshabilitado hasta comprobar el giro inducido del
chasis. Los cuatro emotes suenan en el robot. Se precargan por FTP antes de habilitar
los controles y se reproducen con ProtoPlaySound, con confirmación de como mucho
0,1 s por orden. La parada envía _play_ctrl=0. Este adaptador usa el protocolo del
SDK 0.1.1.68 y requiere validar reproducción y parada en el altavoz físico.
Motor y SCAR se mantienen en el ordenador.

## Audios y bailes

    .venv\Scripts\python.exe -I audio\preparar_emotes.py

Los originales locales son billie_jean.mp3, waka.mp3, risa.mp3, f1.mp3,
scar_fuerte.wav y superestrella.wav. El script crea mando_NOMBRE.wav mono PCM16
48 kHz y mando_NOMBRE.ogg, elimina silencios, normaliza y funde los finales musicales.
El motor usa un tramo estable con fundido cruzado. Todos quedan en audio/propios/,
ignorado por Git.

Las cuatro coreografías son líneas de tiempo sin esperas bloqueantes. Usan modo libre,
caben geométricamente en 1 × 1 m y regresan al origen en integración numérica.
La Risa tiene amplitud reducida a 1,5º para respetar 30 º/s. Waka reserva tres segundos
para el giro final. Super Estrella conserva los gestos del baile de la demo.
La intro de Billie Jean tiene 48 tiempos a 117 BPM, 24,615 s. La alineación real del
primer golpe, la mezcla del bucle y el ajuste retardo_ms necesitan escucha y medición.
Los WAV para el robot terminan en _robot.wav y añaden 0,3 s de silencio inicial,
como los sonidos de disparo de la demo. La coreografía respeta ese margen de arranque.
La sincronía física y el ajuste fino todavía requieren medición.

## Mando físico y laboratorio

Abre http://127.0.0.1:8765/prueba_mando.html en Chrome o Edge, conecta el DualShock
por USB con cable de datos, cierra Steam y pulsa un botón. Apunta su identificador,
mapping, ejes 0–3 y botones. Verifica R2, botón 7, entre 0 y 1.
El botón PS puede estar reservado al sistema. El mapeo estándar se prueba físicamente.
Si no aparece, diagnosticar cable y Steam antes de implementar el plan B pygame.

Pendientes de laboratorio:

- Latencia real y estabilidad de vídeo durante 15 minutos.
- Cortar wifi, cerrar pestaña y desconectar mando en marcha, primero con ruedas en alto.
- FPS y velocidad inducida del chasis.
- Movimiento hacia la cámara: con la torreta girada 90º, W debe ir hacia donde mira.
  Comprobar también qué hace la torreta al girar el chasis con Z/X en modo libre.
- Cada baile con --sin-mover, sobre caja y tres veces en el suelo con 1 × 1 m libre.
- Desviación final ±10 cm, alineación musical y sincronía de disparos.
- Rendimiento GPU con vídeo del robot, incluidos transporte y latencia.
- Captura y vídeo de conducción real para la presentación y la memoria.

## Verificación

    .venv\Scripts\python.exe -m unittest discover -s mando\tests
    node mando\tests\test_entrada.js

Incluye simulacion.py, límites y diagonales, caducidad, selección AUTO, inferencia sin
cola de imágenes, coreografías, rutas HTTP, origen de WebSocket y sesión única.
Las pruebas antiguas de tests/ conservan sus expectativas de 12 disparos y se dejan
pendientes de actualización acordada.

Texto propuesto para el apartado de extras de la memoria, pendiente de captura real:

Se desarrolló una interfaz local para controlar el RoboMaster con teclado y ratón o
un mando USB mediante la Gamepad API. El navegador muestra vídeo MJPEG y superpone
las detecciones, mientras un Conductor procesa las órdenes con límites de velocidad
y vigilancia de caducidad. La inferencia GPU se separa del SDK Python 3.8 y dispone de
alternativa CPU. Se añadieron cuatro coreografías cancelables y audio local. La
latencia wifi, los falsos positivos sobre imágenes de robots y la sincronía física
requieren comprobación experimental.

### Interfaz a pantalla completa con controles en 3D · 10/11/2026

La cámara ocupa toda la ventana y lo demás va encima, semitransparente:

- **Tira superior:** conexión, batería y vídeo. La batería pasa a ámbar por debajo del 20 % y a
  rojo por debajo del 10 %; el vídeo, por debajo de 10 y de 4 imágenes por segundo. La edad de la
  detección solo aparece si pasa de 1 s. El resto de la telemetría está en Ajustes → Telemetría.
- **Mando o teclado en 3D** (abajo a la izquierda). Con el mando, los joysticks se inclinan en
  tiempo real y los botones se hunden y se iluminan; R2 y L2 bajan según cuánto se aprietan. Con
  el teclado se dibujan las teclas asignadas, colocadas como en el mando (mover a la izquierda,
  mirar en el centro, emotes en rombo) y el ratón, que dispara con el botón izquierdo.
- **Qué se dibuja:** cambia solo según lo último que se use, y hay un botón en Ajustes →
  Controles. Solo cambia el dibujo: teclado y mando funcionan siempre los dos.
- **Carteles:** al lanzar un emote sale su botón o tecla, su nombre y el progreso; a los 2,6 s se
  encoge arriba hasta que termina. Al disparar aparece «R2 DISPARO ×n» bajo el punto de mira, y la
  parada muestra su propio cartel. Los emotes ya no se lanzan con el ratón.
- **Robot en 3D** (abajo a la derecha): la torreta gira con el yaw y el pitch reales, se ve el
  campo de visión de la cámara y una flecha con el movimiento del chasis. Sus LED siguen al robot:
  verdes con los controles activos, rojos al disparar y la bandera en el Waka Waka.
- **Extras:** el mando vibra al disparar, al terminar un emote y en la parada; los dibujos se
  atenúan a los 4 s sin tocar nada. Los dos se desactivan en Ajustes → Controles.
- **Waka Waka con la bandera de España:** la torreta y el chasis alternan rojo y amarillo en cada
  tiempo de la canción (LED de arriba y de abajo por separado).

Ficheros: `web/index.html`, `web/hud.css`, `web/app.js` y `web/escena3d.js`. Three.js 0.160.1 va
copiado en `web/vendor/` con su licencia MIT, porque con el portátil en la wifi del robot no hay
internet. Sin WebGL la página funciona igual, sin los dibujos. La interfaz anterior queda en
`web/clasico.html` y `web/clasico.js`. El servidor manda el estado 5 veces por segundo (antes 2)
para que el robot 3D y las cajas no vayan a saltos.

Comprobado en simulación con Chrome: mando simulado (ejes, botones y gatillos), los cuatro emotes
con su cartel, disparos, parada, ajustes desde OPTIONS, teclado y versión clásica, sin errores en
la consola. Falta probarlo con el DualShock y el robot reales, y medir si la vibración se nota.

### Rediseño y diagnóstico Bluetooth · 08/11/2026

La interfaz adopta la paleta negro verdoso y verde #5ce483, los bordes rectos y
las fuentes Silkscreen, Geist y JetBrains Mono del Portfolio de Javier.
Las fuentes se sirven desde web/fonts/, con sus licencias. El vídeo ocupa un
visor independiente y la telemetría y los controles quedan fuera de la imagen.

La página /prueba_mando.html admite USB o Bluetooth según lo que exponga el navegador.
Registra botones observados, valores mínimo y máximo de R2 y recorrido de los ejes.
Con más de un mando se prefiere el que tenga mapeo estándar. El HUD muestra el
identificador del dispositivo al situar el puntero sobre su estado.

Comprobaciones realizadas en esta revisión: 16 pruebas Python, prueba JavaScript
de entradas, sintaxis de cuatro scripts, referencias DOM e HTTP de páginas y fuentes.
El navegador integrado no mostró entradas del mando durante la observación.
El control de Chrome se detuvo porque la automatización no pudo verificar su URL.
La revisión visual final y los botones físicos por Bluetooth quedan pendientes.
Para completarlos, abrir /prueba_mando.html en Chrome, dejar la página delante,
pulsar los botones indicados y recorrer ambos joysticks y R2.


## Preparación para llegar al laboratorio

Ejecuta desde WEEK3:

    .venv\Scripts\python.exe -I mando\preparar.py

Comprueba Python 3.8, SDK y protocolo de audio, configuración, cuatro WAV del robot,
límites y retorno de las coreografías, checkpoint CPU y disponibilidad opcional de CUDA.
Esta comprobación no conecta al robot. Los errores obligatorios detienen el lanzador.

Para arrancar después de conectar el portátil a la red del robot:

    mando\arrancar.cmd

El lanzador ejecuta la comprobación y el servidor. En modo detector auto, el servidor
reutiliza un detector GPU existente o intenta arrancarlo con .venv-gpu. Espera su
disponibilidad y recurre a CPU si no arranca. El proceso GPU creado se cierra al salir.
Los registros de ese arranque van a evidencias/detector/, ignorado por Git.
Los emotes se transfieren una sola vez por conexión. Espera a que el servidor indique
listo antes de activar los controles. El modo de conexión sigue siendo auto.

Para probar el detector real sobre una imagen sintética sin tener el robot:

    .venv\Scripts\python.exe mando\servidor.py --simulacion CARPETA --sin-mover --detector-real

La simulación registra órdenes de reproducción y parada del altavoz sin reproducir
los emotes en el ordenador. /salud expone preparación, errores y detector activo.
La prueba de estabilidad ejecuta 18.000 pasos y representa 15 minutos de reloj
simulado, con pérdidas de control y cuatro coreografías. No mide estabilidad wifi.

Mando observado en el navegador el 08/11/2026:
Wireless Controller, Vendor 054c Product 09cc, mapping standard, cuatro ejes con
recorrido -1 a 1, R2 de 0 a 1, los cuatro botones de emotes, SHARE y OPTIONS registrados.
Javier confirma la conexión Bluetooth y que la prueba de control funciona.

Pruebas cortas que quedan al disponer del robot:

1. Encender, conectar la red y arrancar con mando/arrancar.cmd --sin-mover.
2. Confirmar los cuatro emotes y cortar uno con Esc y otro con SHARE.
3. Comprobar mirada y disparo IR con un rival, con el robot inmovilizado.
4. En caja, verificar sentidos y parada al perder control o desconectar el mando.
5. En suelo, probar cada baile y medir deriva, sincronía y latencia de vídeo.
6. Ejecutar una sesión real prolongada. FPS sigue pendiente de comprobar su giro inducido.

Las comprobaciones de altavoz, ruedas, impactos, wifi y deriva requieren hardware.


### Resultado actual de las pruebas locales

34 pruebas Python y dos pruebas JavaScript correctas (siete nuevas en test_correcciones.py:
rearme tras el baile, aviso de desarme, disparo sin confirmar, puntería automática, LED,
movimiento hacia la cámara con giro del chasis y plantilla de ajustes). Se comprueban reproducción y
parada con el formato binario real del SDK, rechazo de órdenes y falta de ACK,
precarga FTP, cortes de control durante un emote y 15 minutos de reloj simulado.
La petición WebSocket de Risa completó inicio y fin con controles periódicos.
Esto valida integración de software y protocolo, con el transporte de robot simulado.
La audición, confirmación del firmware y corte físico del altavoz siguen pendientes.


El arranque automático se comprobó con el robot simulado y el detector real:
el servicio pasó a listo, sin errores, y publicó detector=gpu. También se verificó
una petición JPEG Python 3.8 → servicio GPU y el cierre del proceso creado.
Una parada queda enclavada en el servidor; los mensajes de control tardíos no la
levantan. Es necesario pulsar Activar controles.
