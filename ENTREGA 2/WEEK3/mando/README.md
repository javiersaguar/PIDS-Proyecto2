# Mando del RoboMaster

Interfaz local del Bloque 3 para conducir, apuntar, disparar infrarrojos y lanzar cuatro
emotes. El circuito autónomo se ejecuta desde demo.py. El mando arranca en modo libre,
con controles desarmados y AUTO apagado.

## Arranque sin robot

Desde ENTREGA 2/WEEK3, con una carpeta de imágenes propias o sintéticas:

    .venv\Scripts\python.exe mando\servidor.py --simulacion CARPETA --sin-mover

Abre http://127.0.0.1:8765 y pulsa Activar controles. La simulación muestra imágenes,
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

## Detector independiente

Entorno previsto .venv-gpu, Python 3.11, torch 2.7.1 y torchvision 0.22.1 con CUDA 12.8:

    uv venv --python 3.11 .venv-gpu
    uv pip install --python .venv-gpu\Scripts\python.exe torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
    uv pip install --python .venv-gpu\Scripts\python.exe -r mando\requirements-gpu.txt
    .venv-gpu\Scripts\python.exe mando\detector_gpu.py
    .venv-gpu\Scripts\python.exe mando\detector_gpu.py --medir 10

El proceso escucha en 127.0.0.1:8766. Reutiliza cargar_modelo y detectar, con una imagen
pendiente. En este portátil Windows bloqueó Python 3.11 con Control de aplicaciones.
La instalación GPU y sus tiempos quedan pendientes, sin cambiar directivas del sistema.

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
El asistente de puntería opcional queda deshabilitado hasta calibrarlo.

## Controles

| Acción | Teclado / ratón | DualShock 4 |
|---|---|---|
| Desplazamiento | WASD | Joystick izquierdo |
| Torreta | Flechas | Joystick derecho |
| Infrarrojos | Clic izquierdo mantenido | R2 >0,5 |
| Moonwalk | Q | □ |
| Waka Waka | E | △ |
| Super Estrella | F | ○ |
| Risa | C | ✕ |
| Parada | Esc / espacio | SHARE |
| Ajustes | Tab / engranaje | OPTIONS |

Los controles se reasignan en ajustes. La configuración se guarda en el navegador y en
config_mando.json. Activar controles permite el audio mediante un gesto del usuario.
Se requiere rearmar tras una parada, perder foco o desconectar el mando.

Chasis limitado vectorialmente a 0,5 m/s y 30 º/s. Torreta a 30 º/s.
Cada orden del chasis caduca en 0,5 s. Sin mensajes durante 0,3 s, el Conductor para,
cancela el baile y desactiva AUTO. El centrado posterior usa velocidades cancelables.
Ctrl+C intenta parar, centrar, apagar LED, cerrar cámara y guardar evidencias.
Los tiempos efectivos de respuesta del SDK deben medirse en laboratorio.

FPS/GIMBAL_LEAD queda visible y deshabilitado hasta comprobar el giro inducido del
chasis. Solo se ofrece audio por ordenador. El SDK no tiene cancelación pública de
audio y subir WAV por FTP bloquearía el Conductor. La salida robot/ambos queda pendiente
de una solución con tiempos acotados y cancelación.

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
El sonido del navegador se inicia al recibir el evento del servidor. La sincronía
física y el adelanto de movimientos todavía requieren medición.

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
- Cada baile con --sin-mover, sobre caja y tres veces en el suelo con 1 × 1 m libre.
- Desviación final ±10 cm, alineación musical y sincronía de disparos.
- GPU en un Python 3.11 autorizado por Windows.
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
