# Roadmap: control del RoboMaster desde una interfaz

Objetivo: manejar el RoboMaster desde el ordenador con teclado y ratón o con un mando de
PS4 por cable. Lo que tiene que hacer:
- ver lo que ve el robot en pantalla, con las detecciones dibujadas;
- moverlo y apuntar el cañón;
- disparar a mano o en modo automático, cuando detecta un robot;
- lanzar bailes y sonidos con un botón;
- un panel de ajustes con los controles y el interruptor del modo automático.

Es un extra de la demo. **No sustituye al circuito autónomo** que pide el enunciado, que
sigue siendo `demo.py`. Sirve para la presentación y para calibrar en el laboratorio
(colocar rivales, ver la cámara, probar la detección y los sonidos).

Estado: 08/11/2026, implementación en curso. Tiempo estimado: unos 9 días de trabajo de una persona,
que se pueden repartir (apartado 12).

## 1. Viabilidad

| Pieza | Viable | Por qué |
|---|---|---|
| Vídeo del robot en pantalla | Sí | `Camara` ya lee el vídeo en segundo plano; solo hay que mandarlo al navegador. Retraso de unos 0,25–0,4 s por la wifi |
| Mover chasis y cañón | Sí | `drive_speed` del chasis y de la torreta, ya usados en la demo. Las órdenes del chasis caducan a los 0,5 s: si se corta la conexión, el robot se para solo |
| Disparar | Sí | La ráfaga de infrarrojos y el sonido de SCAR ya existen |
| Modo automático | Sí | El detector, la puntería y las evidencias ya existen. Con la GPU va a más de 10 imágenes por segundo |
| Bailes y sonidos | Sí | El baile de Super Estrella, los LED y los audios ya existen. Los bailes nuevos se programan igual |
| Mando de PS4 por cable | Sí, muy probable (90 %) | En Chrome y Edge para Windows el DualShock 4 por USB funciona con la Gamepad API del navegador, sin instalar nada |

**El mando de PS4 por cable.** El navegador lo lee con su «mapeo estándar»: botones,
gatillos analógicos y los dos joysticks. Lo que puede fallar:
- **Steam abierto.** Steam puede quedarse el mando para Steam Input y el navegador no lo ve
  o lo ve mal. Hay que cerrarlo o desactivar el soporte de PlayStation en Steam.
- **Activación.** El navegador no lo muestra hasta que se pulsa un botón con la página
  abierta.
- **Pestaña en segundo plano.** El navegador deja de leerlo; la página tiene que estar
  delante.
- **Cable.** Tiene que ser de datos, no solo de carga. El DualShock 4 de primera
  generación usa micro-USB.
- **Botón PS.** No llega al navegador, porque lo reserva el sistema.

Si fallara, el plan B es leerlo en Python con `pygame` (SDL2, compatible con Python 3.8) y
mandarlo al servidor.

**El límite real es la detección en el portátil.** El SDK obliga a usar Python 3.8, y con
Python 3.8 no hay torch que use la RTX 5070. Por eso el detector va en un **proceso aparte**,
con Python 3.11 y torch con CUDA. Recibe imágenes del servidor del robot por la red local y
devuelve las cajas. Si ese proceso no está, se usa `faster_rcnn_v3`, el modelo rápido del
Bloque 2, en CPU y dentro del mismo servidor.

## 2. Arquitectura

```
 Navegador (Chrome o Edge)        Servidor del robot (Python 3.8)          Detector (Python 3.11 + CUDA)
 ─────────────────────────        ───────────────────────────────          ─────────────────────────────
 vídeo + cajas en un canvas  ◄─── vídeo (MJPEG) ◄── Camara (hilo)  ──────►  Faster R-CNN v2 en la RTX 5070
 teclado, ratón, mando       ───► WebSocket ──► Conductor             ◄──────  cajas y confianzas (JSON)
 audio (Web Audio)           ◄─── estado          (único hilo con el SDK)
 HUD y ajustes                                    ├─ chasis, torreta, blaster, LED
                                                  ├─ bailes (coreografías)
                                                  └─ evidencias del modo automático
                                                           │ wifi
                                                       RoboMaster
```

- **Una sola página web** servida por el propio servidor, sin compilar nada: HTML, CSS y JS.
  Funciona en el portátil y, en la misma red, en el móvil.
- **Un solo hilo habla con el SDK** (el Conductor), y todas las órdenes pasan por una cola.
  Así se evitan los errores de «Robot is already performing» que ya tuvimos en la demo.
- **El audio suena en el ordenador por defecto.** El navegador puede mezclar el motor, los
  disparos y las canciones sin retraso. El altavoz del robot solo suena una cosa a la vez,
  tiene que subir cada audio antes de reproducirlo y suena bajo. En los ajustes se puede
  elegir robot, ordenador o ambos.

## 3. Controles

Se pueden cambiar en los ajustes; estos son los de por defecto.

| Acción | Teclado y ratón | Mando de PS4 |
|---|---|---|
| Moverse (adelante, atrás, lados) | W, S, A, D | Joystick izquierdo |
| Mirar y apuntar el cañón (girar e inclinar) | Flechas ← → ↑ ↓ | Joystick derecho |
| Disparar (mantener: un disparo cada 0,3 s) | Clic izquierdo | R2 |
| Emote 1: Moonwalk (Billie Jean) | Q | □ Cuadrado |
| Emote 2: Waka Waka | E | △ Triángulo |
| Emote 3: Super Estrella | F | ○ Círculo |
| Emote 4: Risa | C | ✕ Equis |
| Parada de emergencia (para todo y cancela el baile) | Esc o barra espaciadora | SHARE |
| Ajustes | Botón ⚙ o Tab | OPTIONS |

**Cómo se gira el robot.** Hay dos modos, a elegir en los ajustes:
- **Modo FPS (por defecto):** el chasis sigue a la torreta (modo `GIMBAL_LEAD` del SDK). Al
  mirar a un lado, todo el robot gira, como en un videojuego, y WASD mueve respecto a donde
  se mira.
- **Modo libre:** la torreta gira sola (modo `FREE`), como en la demo. WASD mueve el chasis
  sin girarlo. Sirve para disparar de lado mientras se avanza.

**Límites.** Siempre como mucho 0,5 m/s y 30 º/s en chasis y torreta: el enunciado prohíbe
subirlos. Los ajustes solo permiten bajarlos.

## 4. Fase 0: preparación (medio día)

- [x] **0.1 Carpeta.** Crear `ENTREGA 2/WEEK3/mando/` con esta estructura:
  ```
  mando/
  ├── Roadmap.md         este plan
  ├── README.md          cómo se usa (fase 8)
  ├── servidor.py        servidor del robot (Python 3.8)
  ├── conductor.py       hilo único con el SDK: movimiento, disparo, LED, bailes
  ├── coreografias.py    los bailes como líneas de tiempo
  ├── detector_gpu.py    servidor del detector (Python 3.11 + CUDA)
  ├── config_mando.json  controles y ajustes guardados (sin datos privados)
  └── web/               index.html, estilo.css, app.js, mando.js, audio.js
  ```
- [x] **0.2 Entorno del robot.** El mismo `.venv` de Python 3.8 de la demo, más un servidor web
  con WebSocket: FastAPI con uvicorn, o aiohttp. Hay que fijar versiones que aún admitan
  Python 3.8 y apuntarlas en el README.
- [ ] **0.3 Entorno del detector.** `.venv-gpu` con Python 3.11 y torch 2.7 o posterior con
  CUDA 12.8; la RTX 5070 necesita al menos esa versión. Comprobar con
  `torch.cuda.is_available()` y medir cuánto tarda una imagen con `faster_rcnn_v2` y con
  `faster_rcnn_v3`. `.venv-gpu/` va al `.gitignore`.
- [x] **0.4 Audios.** Copiar los MP3 a `audio/propios/`, que no se sube por los derechos de
  autor, y prepararlos con un script nuevo, `audio/preparar_emotes.py`, basado en
  `preparar_voz.py`. Para cada uno: quitar el silencio, igualar el volumen y guardar dos
  versiones, una para el navegador (OGG o MP3) y otra para el robot (WAV mono a 48 kHz).

  | Audio | Origen | Duración | Qué hacer |
  |---|---|---|---|
  | Billie Jean | Canción completa | 4 min 54 s | Recortar unos 25 s de la intro (bajo y batería), 12 compases, empezando y acabando en un tiempo del compás |
  | Waka Waka | Recorte | 11,7 s | Tal cual, con fundido al final |
  | Risa de gato | Recorte | 3,4 s | Tal cual |
  | Motor de F1 en bucle | `f1.mp3` | 2–3 s | El tramo de tono constante, con fundido cruzado para que el bucle no se note |
  | SCAR | `scar_fuerte.wav` | 0,5 s | Ya está |
  | Super Estrella | `superestrella.wav` | 27,2 s | Ya está |

- [ ] **0.5 Probar el mando.** Enchufarlo, cerrar Steam y abrir una página de prueba de mandos
  en Chrome. Apuntar qué número tiene cada botón y eje, y comprobar que R2 da un valor de 0 a
  1. Si no aparece, pasar al plan B con `pygame`.

**Hecho cuando:** los dos entornos están instalados, la GPU detecta con tiempos medidos, los
audios están preparados y el mando se ve en el navegador.

## 5. Fase 1: servidor y vídeo (1 día)

- [x] **1.1** `servidor.py` conecta con el robot con `connect()` de `demo_utils` y comprueba
  la batería. Arranca la `Camara` y el Conductor.
- [x] **1.2** Ruta `/video`: MJPEG con la última imagen, reducida a 960×540 con calidad JPEG 70,
  a 15–20 imágenes por segundo. Si el navegador va lento, se salta imágenes en lugar de
  acumularlas.
- [x] **1.3** Ruta `/` con la página. Ruta `/ws` con el WebSocket de control y de estado.
- [x] **1.4** Mensaje de estado cada 0,5 s: batería, modo, velocidad, ángulos de la torreta,
  imágenes por segundo, ms del detector y si el modo automático está activo.
- [x] **1.5** Al cerrar (Ctrl+C o error): parar el chasis, centrar la torreta, apagar los LED
  y cerrar la conexión, igual que la demo.

**Hecho cuando:** el navegador muestra lo que ve el robot con menos de 0,5 s de retraso
durante 10 minutos seguidos, sin congelarse.

## 6. Fase 2: movimiento y cañón (1 día)

- [x] **2.1 Mensajes de control.** El navegador manda 20 veces por segundo
  `{mover: [x, y], mirar: [yaw, pitch], disparo: bool}`, con valores de −1 a 1. Teclado y
  mando se suman: gana el valor mayor de cada eje.
- [x] **2.2 Conductor.** Convierte los valores en velocidades:
  - x e y × velocidad máxima del chasis, como mucho 0,5 m/s, con `drive_speed(timeout=0.5)`;
  - yaw y pitch × velocidad máxima de la torreta, como mucho 30 º/s, con `gimbal.drive_speed`.
- [x] **2.3 Si se pierde la conexión:** sin mensajes durante 0,3 s, el chasis y la torreta se
  paran. Lo mismo al cerrar la pestaña, desenchufar el mando o pasar la página a segundo
  plano.
- [ ] **2.4 Teclado.** WASD y flechas con `keydown` y `keyup`, ignorando la repetición
  automática de teclas. Esc o espacio, parada de emergencia.
- [ ] **2.5 Mando.**
  - Leer la Gamepad API con `requestAnimationFrame`.
  - Zona muerta de 0,15 en los joysticks.
  - Curva cuadrática, para tener precisión cerca del centro.
  - Opción de invertir el eje vertical.
- [ ] **2.6 Modos FPS y libre** (apartado 3), con el cambio de modo del SDK al pasar de uno a
  otro.
- [ ] **2.7 Primera prueba con el robot sobre una caja**, con las ruedas en el aire. Después,
  en el suelo y con alguien al lado.

**Hecho cuando:** con teclado y con mando el robot se mueve en las cuatro direcciones, la
torreta apunta, nunca pasa de los límites y se para solo al cortar la conexión.

## 7. Fase 3: disparo y sonidos (1 día)

- [x] **3.1 Disparo.** Clic o R2 (valor > 0,5) dispara un infrarrojo. Mantenido, uno cada
  0,3 s, como en la demo. Cada disparo pasa por la cola del Conductor.
- [ ] **3.2 Sonido de SCAR** en cada disparo, en el ordenador, con Web Audio, sin retraso.
  Con salida en el robot se usa el audio de un disparo, como en la demo.
- [ ] **3.3 Motor de F1 mientras se mueve:**
  - el bucle del motor sube de volumen al empezar a moverse y baja al pararse, con fundidos
    de 0,3 s;
  - la velocidad de reproducción va de 0,8 a 1,3 según la velocidad del robot, así que el
    motor sube de tono al acelerar;
  - en el altavoz del robot no se hace, porque solo suena una cosa a la vez: el motor taparía
    los disparos y los emotes.
- [ ] **3.4 Prioridad de sonidos en el robot:** emote > disparo > motor. El emote corta lo que
  esté sonando.
- [x] **3.5 LED:** azul al moverse, rojo parpadeando al disparar, verde al acertar (fase 4) y
  los de cada baile.

**Hecho cuando:** cada disparo suena a la vez que sale, el motor acompaña al movimiento sin
cortes y nada se queda sonando al parar.

## 8. Fase 4: detector en la GPU y modo automático (1,5 días)

- [ ] **4.1 `detector_gpu.py`** (Python 3.11):
  - carga `model_demo.pt` con la misma arquitectura que la demo y lo calienta con una imagen
    vacía;
  - escucha en `127.0.0.1` y responde a cada imagen JPEG con sus cajas y confianzas en JSON;
  - mide los ms de cada imagen.
- [ ] **4.2 En el servidor,** un hilo manda al detector siempre la imagen más nueva, con solo
  una pendiente a la vez. Si el detector no responde, se cambia a `faster_rcnn_v3` en CPU y
  se avisa en el HUD.
- [ ] **4.3 Cajas en pantalla.** El navegador dibuja las cajas y la confianza en un canvas
  encima del vídeo, sin volver a codificar la imagen. Verde si llegan a 0,95 y naranja si
  no, como en las evidencias.
- [ ] **4.4 Modo automático**, que se activa y desactiva en los ajustes:
  - dispara si una caja llega a 0,95 y el punto de mira cae dentro de ella (encogida un
    20 %, para no disparar al borde);
  - como mucho un disparo cada 0,3 s, solo infrarrojos;
  - indicador rojo «AUTO» en el HUD mientras está activo;
  - la parada de emergencia lo desactiva.
- [ ] **4.5 Asistente de puntería** (opcional, otro interruptor). La torreta se mueve sola
  hacia la caja más centrada, con el seguimiento de la demo (velocidad estimada más
  corrección proporcional). El jugador sigue moviendo el chasis.
- [ ] **4.6 Evidencias.** Cada imagen en la que dispara el modo automático se guarda con
  `Registro` en `evidencias/mando_<fecha_hora>/`, con sus cajas.
- [ ] **4.7 Aviso en los ajustes.** El detector también ve como robots las imágenes de robots
  (estudio del señuelo). Solo detecta robots, no personas, pero el modo automático no se
  deja activo sin vigilar.

**Hecho cuando:** con la GPU se ven las cajas a más de 10 imágenes por segundo y el modo
automático dispara a un robot solo cuando lo tiene en el punto de mira.

## 9. Fase 5: emotes y bailes (2 días)

- [ ] **5.1 Motor de coreografías** (`coreografias.py`). Cada baile es una lista de pasos con
  su instante en tiempos de compás (BPM de la canción):
  `(tiempo, chasis vx/vy/giro, torreta yaw/pitch, LED, duración)`.
  - Lo ejecuta el Conductor, con la música en el ordenador y, si se elige, en el robot.
  - Durante el baile se ignoran WASD y el cañón.
  - La parada de emergencia lo corta, y al acabar o cortarse el robot vuelve a estar quieto
    y con la torreta centrada.
  - Comprueba los límites antes de empezar: ningún paso pasa de 0,5 m/s ni de 30 º/s, y el
    recorrido total cabe en 1 × 1 m.
- [ ] **5.2 Sincronía.** La música y los movimientos empiezan a la vez. Se mide el retraso
  del robot (wifi) y se adelantan los movimientos esos ms. El retraso es un ajuste.
- [ ] **5.3 Super Estrella (F / ○).** Pasar el `baile()` actual de la demo al formato nuevo.
- [ ] **5.4 Moonwalk con Billie Jean (Q / □).** Unos 25 s de la intro, a 117 BPM: un tiempo
  cada 0,51 s y un compás cada 2,05 s.
  1. **Pose inicial (1 compás):** torreta centrada e inclinada hacia abajo (pitch −15º), como
     el sombrero. LED blancos.
  2. **Moonwalk hacia atrás (2 compases, 8 pasos):** en cada tiempo, un deslizamiento hacia
     atrás de 0,35 s, que acelera y frena suavemente (perfil seno², pico de 0,25 m/s), y una
     parada de 0,16 s. Son unos 4,5 cm por paso y unos 36 cm en total; sale fluido pero con
     la frenada marcada. La torreta cabecea con el ritmo (−15º ↔ −8º) y los LED cambian de
     color en cada paso (blanco, rosa, amarillo, azul), como las baldosas del vídeo.
  3. **Parada y giro (3 compases):** el chasis quieto y la torreta gira 180º a 30 º/s (6 s),
     con los LED parpadeando en blanco.
  4. **Moonwalk de vuelta (2 compases):** el chasis avanza con el mismo perfil. Como la
     torreta mira hacia atrás, parece que sigue caminando hacia atrás, y el robot vuelve a
     donde empezó.
  5. **Giro de vuelta (3 compases):** la torreta gira otros 180º hasta el centro.
  6. **Pose final (1 compás):** la torreta sube de golpe a +20º (el «de puntillas»), con
     todos los LED en blanco, y se apagan al final.

  Son 12 compases, unos 25 s. El robot no se aleja más de 36 cm de donde empieza.
- [ ] **5.5 Waka Waka (E / △).** 11,7 s, a unos 127 BPM (un tiempo cada 0,47 s):
  1. **Contoneo:** el chasis se desliza a los lados (±6 cm por tiempo) mientras la torreta va
     al lado contrario (yaw ±10º cada dos tiempos), como las caderas.
  2. **«Eh, eh»:** dos cabeceos rápidos (pitch +8º) en cada acento.
  3. **LED:** los colores de la bandera de Sudáfrica (verde, amarillo, rojo, azul), uno por
     tiempo.
  4. **Final:** medio giro del chasis de 45º y vuelta, con los LED en amarillo.
- [ ] **5.6 Risa (C / ✕).** 3,4 s:
  - la torreta tiembla arriba y abajo (pitch ±5º, unas 3 veces por segundo) mientras el chasis
    se balancea ±5º;
  - los LED parpadean en amarillo 10 veces por segundo;
  - al acabar, la torreta baja a −10º, como agotada, y vuelve al centro.
- [ ] **5.7 Probar cada baile** primero con `--sin-mover`, solo torreta y LED; después con el
  robot sobre la caja; y al final en el suelo, con 1 × 1 m libres.

**Hecho cuando:** los cuatro bailes van al ritmo, se pueden cortar en cualquier momento y el
robot acaba donde empezó (±10 cm).

## 10. Fase 6: interfaz y ajustes (1,5 días)

- [ ] **6.1 Pantalla principal:**
  - vídeo a pantalla completa con su canvas de cajas y un punto de mira en el centro;
  - HUD arriba: batería, retraso, imágenes por segundo, ms del detector, modo FPS o libre y
    «AUTO» si está activo;
  - abajo, los 4 emotes con su tecla y su botón del mando;
  - ⚙ arriba a la derecha.
- [ ] **6.2 Ajustes** (ventana con pestañas):
  - **Controles:** tabla de teclado y de mando con lo que hace cada tecla y botón; se pueden
    reasignar haciendo clic y pulsando la nueva tecla o botón. Botón «Restablecer».
  - **Disparo:** modo automático sí o no, asistente de puntería sí o no, umbral (0,95 por
    defecto) e intervalo entre disparos.
  - **Movimiento:** modo FPS o libre, velocidad máxima del chasis y de la torreta (solo
    hacia abajo de 0,5 m/s y 30 º/s), sensibilidad, zona muerta e invertir eje vertical.
  - **Audio:** salida (ordenador, robot o ambos), volumen general, volumen del motor y motor
    sí o no.
  - **Detector:** GPU (`faster_rcnn_v2`) o CPU (`faster_rcnn_v3`), y mostrar cajas sí o no.

  Se guardan en `config_mando.json` (servidor) y en el navegador, y se aplican al momento.
- [ ] **6.3 Mando conectado.** Icono del mando en el HUD cuando se detecta y aviso «Pulsa un
  botón del mando» si aún no ha aparecido.
- [ ] **6.4 Respuesta visual:**
  - marca de impacto en el punto de mira al disparar;
  - borde rojo suave mientras dispara el modo automático;
  - aviso breve al empezar un baile («Moonwalk 🕺») y barra de progreso de la canción;
  - botón del emote resaltado mientras dura.
- [ ] **6.5 Retoques estéticos:**
  - tema oscuro con un color de acento;
  - tipografía legible sobre el vídeo (texto con sombra);
  - iconos de los botones de PlayStation (□ △ ○ ✕) y de las teclas;
  - animaciones cortas (menos de 200 ms) al abrir los ajustes y al pulsar emotes;
  - modo pantalla completa;
  - que se vea bien en 1080p y en el portátil.
- [ ] **6.6 Pantalla de conexión:** «Conectando con el robot…» mientras arranca y error claro
  si no lo encuentra, con el modo de conexión que se ha intentado.

**Hecho cuando:** alguien que no ha visto el código maneja el robot, abre los ajustes,
entiende los controles y activa el modo automático sin ayuda.

## 11. Fase 7: pruebas y robustez (1 día)

- [ ] **7.1 Pruebas sin robot** con `simulacion.py`:
  - límites de velocidad;
  - parada sin mensajes;
  - suma de teclado y mando;
  - coreografías: ningún paso pasa de los límites y la suma de desplazamientos vuelve al
    origen;
  - regla del modo automático (dispara con 0,95 dentro del punto de mira, no fuera).
- [ ] **7.2 Pruebas con robot:**
  - cortar la wifi, cerrar la pestaña y desenchufar el mando en marcha: tiene que pararse;
  - Steam abierto con el mando;
  - batería por debajo del 20 %;
  - 15 minutos seguidos sin que se congele el vídeo;
  - medir el retraso (cronómetro en pantalla grabado por la cámara);
  - cada baile 3 veces seguidas.
- [ ] **7.3 Errores del SDK** («Robot is already performing», sin respuesta): reutilizar
  `liberar_cerrojo_sdk` y los tiempos máximos de `ejecutar_accion`.

## 12. Fase 8: documentación y reparto (medio día)

- [ ] **8.1 `mando/README.md`:** instalación de los dos entornos, cómo arrancar
  (`python mando/servidor.py` y `python mando/detector_gpu.py`), los controles, el mando de
  PS4 (Steam cerrado, pulsar un botón) y los problemas frecuentes.
- [ ] **8.2 Memoria:** un párrafo y una captura en el apartado de extras. Contar también los
  límites: retraso de la wifi, detección en GPU en un proceso aparte y falsos positivos del
  modo automático.
- [ ] **8.3 Vídeo corto** para la presentación: conducción, disparo automático y los bailes.

**Reparto posible**, en paralelo tras la fase 0:

| Persona | Fases |
|---|---|
| 1 | Servidor, vídeo y Conductor (1 y 2) |
| 2 | Página, mando y ajustes (2.4–2.5 y 6) |
| 3 | Detector en GPU y modo automático (4) |
| 4 | Audios y coreografías (0.4, 3 y 5) |
| 5 | Pruebas y documentación (7 y 8) |

## 13. Riesgos

| Riesgo | Qué hacer |
|---|---|
| Retraso del vídeo por la wifi (0,3–0,5 s) | Vídeo a 960×540, saltar imágenes viejas y mostrar el retraso en el HUD |
| Steam se queda el mando | Cerrar Steam; plan B con `pygame` |
| La GPU no funciona en el entorno 3.11 | `faster_rcnn_v3` en CPU (unas pocas imágenes por segundo) |
| El SDK se bloquea con órdenes a la vez | Todo por la cola del Conductor |
| En modo FPS el chasis gira más rápido de lo permitido | Medirlo; si pasa de 30 º/s, usar solo el modo libre |
| Subir canciones al robot tarda | Audio en el ordenador por defecto |
| El modo automático dispara a imágenes de robots | Umbral 0,95, punto de mira dentro de la caja, aviso en ajustes y parada de emergencia |
| Derechos de autor de las canciones | Siguen en `audio/propios/`, sin subir a GitHub |
## Registro de implementación

- Fase 0. Entorno del servidor con aiohttp 3.10.11 instalado en Python 3.8.
- GPU pendiente. Windows bloquea Python 3.11 con Control de aplicaciones. No se cambian directivas del sistema. Falta también el checkpoint de faster_rcnn_v3 para CPU.
- Audios locales preparados en WAV mono PCM16 48 kHz y OGG. Intro Moonwalk de 48 tiempos a 117 BPM (24,615 s). Alineación musical y bucle del motor pendientes de escucha en laboratorio.
- DualShock pendiente de prueba física. Abrir /prueba_mando.html, cerrar Steam y pulsar un botón.
- Adaptación propuesta de coreografías. Reducir amplitud del temblor de Risa y del contoneo Waka para cumplir 30 º/s. Reservar tres segundos al giro 45º y vuelta. FPS queda deshabilitado por defecto hasta medir en laboratorio el giro inducido del chasis.

- Fases 1–3. Servidor aiohttp, vídeo MJPEG y WebSocket, Conductor con vigilancia 0,3 s y timeout 0,5 s. FPS y audio en robot pendientes por seguridad. Estas marcas indican implementación; las condiciones físicas de fin siguen pendientes.
