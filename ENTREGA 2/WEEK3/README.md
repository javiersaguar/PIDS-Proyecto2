# Semana 3 · Integración del detector en el robot (Bloque 3)

El RoboMaster recorre el circuito, se para en puntos elegidos, busca a los robots
rivales con el detector del Bloque 2 y les dispara 12 veces con el infrarrojo.

El material de la asignatura (`connect.py`, los ejemplos de `audio/`, `camera/`,
`chassis/`, `gimbal/`, `others/` y la plantilla de `demo.py` y `demo_utils.py`) se
completó el 04/11/2026 con nuestra demo.

## 1. Contenido

| Fichero | Qué hace |
|---|---|
| **`circuito.py`** | **Configuración: modelo, umbral, estrategia y paradas del circuito. Es lo que se ajusta en el laboratorio** |
| **`demo.py`** | La demo: recorrido, barrido, puntería, disparo, evidencias, LED, sonido y baile. También `detect_and_shoot` completado según la plantilla |
| `demo_utils.py` | Funciones de la asignatura y las nuestras (sección «Añadidos del grupo 2»): carga comprobada del modelo, cámara abierta toda la demo, evidencias, LED y sonido |
| `simulacion.py` | Robot simulado para probar la demo sin el RoboMaster |
| **`guia_pruebas.pdf`** | **Guía paso a paso de las pruebas con el robot antes de la demo final** |
| `tests/test_demo.py` | Pruebas con el robot simulado y un detector falso, y comprobación de sintaxis de Python 3.8 |
| `connect.py` | Une el robot a la wifi del laboratorio con un QR y guarda su número de serie en `serial_number.txt` |
| `audio/`, `camera/`, `chassis/`, `gimbal/`, `others/` | Ejemplos de cada módulo del SDK |
| `pyproject.toml`, `pixi.lock` | Entorno de la asignatura (pixi, Python 3.8) |

## 2. Cómo funciona la demo

Para cada parada de `circuito.PARADAS`:

1. **Desplazamiento.** El chasis hace los movimientos `(x, y, z)` de la parada, uno
   tras otro: `x` adelante, `y` a la derecha y `z` giro a la izquierda en grados.
   La velocidad es la de `circuito.py` (0,3 m/s y 30 º/s), recortada siempre a la
   del SDK (0,5 m/s y 30 º/s): el enunciado prohíbe aumentarla.
2. **Barrido continuo** (`BARRIDO_CONTINUO = True`). El gimbal se centra y gira sin
   pararse, a `VEL_BARRIDO` (30 º/s), entre los extremos de `barrido`. Analiza una imagen
   cada `PASO_BARRIDO` grados (10º, unas 3 por segundo), no todas: con un campo de visión
   útil de `CAMPO_VISION` (70º), cada robot sale en varias. Si `barrido` cubre 360º, los
   extremos son ±145º (0 → +145 → −145), que basta para verlo todo. Va primero al extremo
   más cercano o, si están igual de lejos, al que aparece antes en la lista. Cada imagen se
   sitúa con el ángulo que tenía la torreta al tomarla (`RETARDO_CAMARA`). En cuanto
   aparece un robot nuevo, lo ataca (paso 4) y sigue barriendo desde donde ha quedado.
   Con `BARRIDO_CONTINUO = False`, se para en cada ángulo de `barrido`, espera
   `ESPERA_CAMARA` (0,5 s) y analiza una imagen.
3. **Selección.** Se quedan las detecciones con confianza `>= UMBRAL` y se calcula el
   ángulo de cada una (el yaw del gimbal más `auto_aim`) y su distancia (por el alto de la
   caja y `ALTURA_ROBOT`). No se repite:
   - una detección a menos de `TOLERANCIA_YAW` (15º) de otra ya revisada en la parada (el
     mismo robot en dos imágenes);
   - un robot de la **memoria del circuito** (sección 2.1): ya atacado en esta parada o en
     otra, o que no se pudo fijar hace menos de `TIEMPO_DESCARTE` s.
4. **Seguimiento y disparo** (`SEGUIMIENTO = True`, para rivales que se mueven). Para cada
   robot nuevo, el gimbal gira hacia él y a partir de ahí analiza cada fotograma en cuanto
   llega, sin esperas (unas 10 imágenes por segundo con GPU):
   - **Fija el objetivo:** toma la detección más cercana a donde se espera el robot, contando
     con lo que se ha movido. Para fijarlo hace falta confianza `>= UMBRAL`, que no sea un
     robot ya atacado y que esté a menos de `SALTO_MAX` (25º) de donde se vio. Ya fijado,
     basta `UMBRAL_SEGUIMIENTO` (0,8) para no perderlo con el desenfoque del movimiento.
   - **Lo sigue:** gira la torreta con `gimbal.drive_speed` a una velocidad proporcional al
     error (`GANANCIA_SEGUIMIENTO`) más la velocidad estimada del robot (`ANTICIPAR`), en
     yaw y en pitch (`CORREGIR_PITCH`), siempre con el tope de 30 º/s.
   - **Dispara solo con el robot centrado:** error menor que `TOLERANCIA_DISPARO` (3º) o que
     el 40 % del tamaño de la caja, si es mayor, y al menos `INTERVALO_DISPARO` (0,25 s)
     desde el disparo anterior, hasta llegar a 12.
   - **Compensa el retardo del vídeo:** la imagen llega `RETARDO_CAMARA` s tarde (unos
     0,25 s por wifi). El ángulo del robot se calcula con el que tenía la torreta al tomar la
     imagen, que se guarda en un historial, y no con el de ahora.
   - **Lo da por perdido** si no lo ve en `PERDIDAS_MAX` imágenes seguidas o pasan
     `TIEMPO_MAX_OBJETIVO` s. No cuenta como atacado y el barrido sigue.

   Tras los 12 disparos, el gimbal cabecea y el LED se pone verde. Con `SEGUIMIENTO = False`
   se usa la versión anterior: confirma una vez (`CONFIRMAR`), corrige y dispara la ráfaga sin
   volver a mirar. Solo sirve para robots quietos.
5. **Fin de la parada.** Si se han atacado los `objetivos` esperados en la parada, se
   deja de barrer (salvo `BARRIDO_COMPLETO = True`). El gimbal vuelve al centro. Si se fija
   `ROBOTS_TOTALES` y ya se han atacado todos, el resto de paradas se recorre sin barrer.

### 2.1. Memoria de robots atacados

Los rivales son todos iguales y se mueven, así que la demo lleva una memoria aproximada de
los robots atacados, en metros sobre el circuito:

- **Posición del chasis** (X adelante desde la salida, Y a la izquierda, rumbo): se calcula
  con los movimientos `(x, y, z)` ya hechos. El chasis se traslada y después gira, así que
  conviene no mezclar giro y avance en un mismo movimiento.
- **Posición del robot:** la dirección del gimbal y la distancia estimada por el alto de la
  caja: `distancia = ALTURA_ROBOT / (2 · tan(alto / 2))`.
- **Mismo robot:** una detección está dentro de la tolerancia de uno atacado.
  - **De lado** (el ángulo es preciso): `RADIO_MISMO_ROBOT` (0,35 m), lo mínimo entre dos
    RoboMasters.
  - **A lo largo de la línea de visión** (la distancia es aproximada): ese radio más
    `ERROR_DISTANCIA` (0,25 m) por cada metro de distancia.

Un robot atacado que se ha alejado más de la tolerancia se toma por uno nuevo y se le vuelve
a atacar (unos 4 s). Se prefiere así a dejar sin disparar a un robot nuevo que pase cerca. Lo
que no se pudo fijar (falsos positivos del barrido) se anota como descarte y se vuelve a
intentar pasados `TIEMPO_DESCARTE` s. `TIEMPO_MEMORIA` hace que se olviden los atacados
(por defecto, nunca).

**Calibrar `ALTURA_ROBOT`:** colocar un robot a 1,5 m medidos, lanzar
`--sin-mover --sin-disparar` y comparar con la columna `distancia_m` de `registro.csv`:
`ALTURA_ROBOT` nueva = actual × 1,5 / distancia medida. Depende de cómo se anotaron las
cajas (con o sin antenas).

Al terminar: vuelta al inicio (opcional) y baile final con LED, sonido, gimbal y chasis.

**Estrategia elegida** (se puede cambiar en `circuito.py`):

- Se dispara a **todas** las detecciones nuevas que superan el umbral
  (`DISPARAR_A_TODOS`), porque hay que inutilizar a todos los robots.
- Se barre **hasta encontrar los robots esperados** en esa parada, no siempre 360º. Si
  no se sabe cuántos hay (`objetivos=None`), se completa el barrido.
- Se sigue al robot mientras se le dispara, porque los rivales también exploran y se
  mueven. Una ráfaga a ciegas falla en cuanto el robot sale de la línea de tiro, y con GPU
  analizar cada fotograma durante la ráfaga cuesta poco. Así se cumple «mirar donde y cuando
  conviene»: se detecta sin parar solo mientras se ataca a un robot.
- El sonido de disparo suena una vez por ráfaga (`SONIDO_CADA_DISPARO = False`). El SDK sube
  el audio al robot en cada llamada y no admite dos sonidos a la vez: con un sonido por
  disparo, la ráfaga pasaba de unos 3 s a más de 20.

**Módulos usados**, como pide el enunciado:

| Módulo | Uso |
|---|---|
| Chasis | Recorrido entre paradas y baile |
| Gimbal (torreta) | Barrido continuo, seguimiento del objetivo (`drive_speed`), lectura de su ángulo (`sub_angle`), cabeceo tras inutilizar un robot y baile |
| Cámara | Vídeo abierto toda la demo; se lee siempre el fotograma más reciente, situado con el ángulo de la torreta al tomarlo |
| Blaster | 12 disparos de infrarrojo por robot, de uno en uno |
| LED | Color según el estado: azul en marcha, ámbar buscando, naranja apuntando, rojo parpadeando al disparar, verde tras inutilizar un robot, morado sin hallazgos |
| Audio | Sonidos del SDK al empezar, buscar, detectar, disparar y terminar, y `engine_sound.wav` al arrancar |
| Batería | Se lee al empezar y se avisa por debajo del 20 % |

**Seguridad.** Ctrl+C, un error o el final de la demo detienen el chasis, centran el
gimbal, cierran la cámara, apagan los LED, guardan el resumen y cierran la conexión.

- **Batería:** la demo no arranca por debajo del 10 % (`BATERIA_CRITICA`), porque el robot
  deja de responder, y avisa por debajo del 20 %.
- **Tiempo máximo:** cada movimiento del chasis y del gimbal tiene uno, calculado con la
  distancia y la velocidad. Si el robot no lo confirma a tiempo, la demo se detiene en
  lugar de quedarse esperando.
- **Sonidos:** nunca se solapan. El SDK rechaza un sonido si hay otro sonando y, al
  hacerlo, deja bloqueado un cerrojo interno (`robomaster/action.py`, `send_action`).
  Con ese cerrojo bloqueado, la siguiente orden se queda esperando para siempre y el
  robot no se mueve. `liberar_cerrojo_sdk` lo suelta si ocurre.

### Audios propios

El robot solo reproduce WAV mono de 16 bits a 48 kHz. `audio/convertir_audio.py` convierte
cualquier audio (mp3, m4a, wav…), lo recorta y normaliza el volumen:

```
python audio/convertir_audio.py ENTRADA audio/propios/scar.wav --duracion 1
python audio/convertir_audio.py ENTRADA audio/propios/superestrella.wav --inicio 50 --duracion 25
```

| Audio (`circuito.py`) | Cuándo suena |
|---|---|
| `AUDIO_MOTOR` (`audio/engine_sound_corto.wav`) | Al arrancar: los 6 primeros segundos de `engine_sound.wav`, para que no tape los demás sonidos |
| `AUDIO_DISPARO` (`audio/propios/scar.wav`) | Al empezar cada ráfaga, sin esperar a que acabe. Con `SONIDO_CADA_DISPARO = True`, en cada disparo: si hay otro sonido en curso se omite (con seguimiento) o se espera (sin seguimiento), porque el SDK no admite dos sonidos a la vez |
| `AUDIO_FINAL` (`audio/propios/superestrella.wav`) | En el baile final. Los LED cambian de color `LED_FIESTA_HZ` veces por segundo mientras suena |

`audio/propios/` no se sube a GitHub, porque las canciones y los sonidos de juegos tienen
derechos de autor. Si un audio no existe, la demo usa los sonidos del SDK. Hace falta
`pip install imageio-ffmpeg`, que trae ffmpeg.

## 3. Evidencias

Cada ejecución crea `evidencias/<fecha_hora>/` (no se sube a GitHub):

- Una imagen por cada inferencia, con nombre `NNN_parada_fase_yawXX.jpg`. Lleva las
  cajas y la confianza dibujadas: verde si se acepta, naranja si se queda entre 0,3 y
  el umbral. El objetivo tiene una cruz roja y el título indica la parada, el yaw, el
  umbral y el tiempo de inferencia. Las fases son `barrido`, `seguimiento` (cada
  fotograma mientras se sigue a un robot; la columna `disparos` acumula los de ese robot),
  `sin_confirmar` y, sin seguimiento, `confirmado`. Los JPEG se escriben en un hilo aparte
  para no frenar el seguimiento.
- `originales/`: las mismas imágenes sin dibujar, para analizarlas o anotarlas después.
- `registro.csv`: una fila por imagen con yaw, tiempo de inferencia, confianzas, cajas,
  ángulo y distancia estimada del objetivo (`distancia_m`, para analizar el efecto de la
  distancia) y disparos.
- `resumen.json`: configuración, robots atacados por parada, disparos totales, tiempo
  medio de inferencia y duración. Cada ataque indica si se completó, cuántas imágenes y
  segundos llevó, la velocidad angular estimada del robot, su distancia y su punto en el
  circuito. También guarda la memoria de robots atacados, el tiempo de cada parada y la
  posición del chasis.

Es el material de la memoria del Bloque 3: aciertos, falsos positivos, robots no
vistos y tiempos.

## 4. En el laboratorio

1. **Proyecto y entorno.** El SDK `robomaster` solo funciona con Python 3.6–3.8.
   - En los ordenadores del laboratorio: abrir en VSCode `/home/PIDS/robomaster`, copiar
     allí estos ficheros y elegir el intérprete `/home/PIDS/robomaster/.pixi/venv/bin/python`.
   - En un portátil con Windows: crear un entorno de Python 3.8 en esta carpeta, por
     ejemplo con `uv`:
     `uv venv --python 3.8 .venv` y luego
     `uv pip install --python .venv\Scripts\python.exe --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match "robomaster>=0.1.1.68,<0.2" torch==2.4.1 torchvision==0.19.1 "numpy<2" "matplotlib<3.8"`.
     Abrir esta carpeta en VSCode y elegir `.venv\Scripts\python.exe` como intérprete.
     `.venv/` está ignorado.
   - Ejecutar sin depurador (Ctrl+F5 o «Run Python File»): al relanzar con el depurador,
     VSCode da a veces `ConnectionRefusedError` sin llegar a ejecutar el script.
2. **Modelo.** Basta con los pesos de `model_best.pt`, que pesa 346 MB porque guarda
   también el optimizador. En un terminal de JupyterHub se exporta `model_demo.pt`
   (173 MB, solo `{'model': state_dict}`):
   ```
   python -c "import os,torch;d=os.path.expanduser('~/pids_main/models/faster_rcnn_v2_aug_robusto_v1_lr001/');c=torch.load(d+'model_best.pt',map_location='cpu',weights_only=False);torch.save({'model':c['model']},d+'model_demo.pt')"
   ```
   Se descarga y se deja en `models/faster_rcnn_v2_aug_robusto_v1_lr001/model_demo.pt`,
   junto a `demo.py`; es la ruta de `RUTA_MODELO`. El de la demo tiene SHA-256
   `f46a49d7c8cb2ced6061738b01a99a1c9f476a4aea9c83a6967e7909d5b63141`. El modelo no se
   sube a GitHub. `demo.py` comprueba que el checkpoint trae los 404 tensores de la
   arquitectura.
3. **Conectar.** Hay dos modos:
   - **Wifi directo** (portátil con wifi): la pestaña de conexión del robot en el icono
     de wifi directo y el portátil conectado a la red `RMEP-…` del robot (contraseña en
     su pegatina). No se usa `connect.py`.
   - **Networking** (ordenadores del laboratorio, sin wifi): rellenar en `connect.py`
     la SSID, la contraseña y el número de serie **solo en local** (no se hace commit de
     esos valores; `git update-index --skip-worktree connect.py` evita subirlos por
     error). Poner el robot en modo *networking*, lanzar `python connect.py` y enseñarle
     el QR.

   Todos los scripts eligen el modo solos: con `serial_number.txt`, networking; sin él,
   wifi directo. Al conectar muestran `Conexion: wifi` o `Conexion: networking`.
4. **Probar sin robot**, en el ordenador del laboratorio:
   `python demo.py --simulacion CARPETA`, con una carpeta de imágenes; dentro del
   repositorio basta `--simulacion`, que usa `ENTREGA 1/WEEK2/DATOS_ASIGNATURA/data_test`.
   Comprueba que el modelo carga y mide la inferencia en ese equipo.
5. **Medir el circuito** y escribir las paradas en `circuito.PARADAS`: movimientos,
   ángulos de barrido y robots esperados. Comprobar el sentido del gimbal: si apunta al
   lado contrario del robot, poner `SIGNO_YAW = -1`.
6. **Calibrar cada parada sin moverse ni disparar:**
   `python demo.py --sin-mover --sin-disparar --paradas P1`. Revisar en `evidencias/`
   que detecta a los robots y que el umbral 0,95 (fijado en validación) no es demasiado
   estricto con la luz del laboratorio. Si hay que cambiarlo, probar con `--umbral` y
   anotar el motivo para la memoria.
7. **Recorrido sin disparar:** `python demo.py --sin-disparar`, con un compañero junto
   al robot y Ctrl+C a mano. Dejar espacio en todas direcciones y no confundir x e y.
8. **Demo completa:** `python demo.py`. Agarrar el robot siempre por la base, nunca por
   la cabeza, y no apuntar a nadie con el blaster.

Opciones de `demo.py`:

| Opción | Efecto |
|---|---|
| `--sin-disparar` | No usa el blaster |
| `--sin-mover` | No mueve el chasis |
| `--paradas P1,P3` | Solo detecta en esas paradas. Hace los movimientos hasta la última elegida, salvo con `--sin-mover` |
| `--ver` | Muestra en una ventana cada imagen analizada, con sus cajas, mientras la demo sigue |
| `--umbral 0.9` | Cambia el umbral sin editar `circuito.py` |
| `--modelo RUTA`, `--arquitectura NOMBRE` | Usa otro checkpoint, por ejemplo `faster_rcnn_v3` si la inferencia es lenta |
| `--simulacion [CARPETA]` | Robot simulado que ve las imágenes de `CARPETA` (por defecto, el test de la asignatura) |
| `--evidencias CARPETA` | Carpeta de salida |

## 5. Pruebas

```
python -m unittest discover -s tests
```

Con el robot simulado y un detector falso que «ve» robots en ángulos conocidos,
comprueban lo siguiente:

- ataca a cada robot una sola vez, aunque salga en dos imágenes, con 12 disparos y
  apuntando a su ángulo;
- deja de barrer al encontrar los robots esperados;
- no dispara si al confirmar el robot no está centrado o es uno ya atacado, y corrige la puntería si lo está;
- sigue a un robot que se mueve y le dispara 12 veces, solo cuando está centrado;
- lo fija aunque se haya movido desde el barrido, pero no si aparece a más de `SALTO_MAX`;
- con la imagen 0,3 s retrasada y el robot a 12 º/s, todos los disparos caen sobre él;
- da por perdido a un robot que desaparece y no lo cuenta como atacado;
- lee el ángulo del gimbal aunque la lectura vaya al revés, y lo estima si no hay lectura;
- Ctrl+C durante el seguimiento deja la torreta parada;
- el audio de disparo suena una vez por ráfaga (o en cada disparo con `SONIDO_CADA_DISPARO`);
- el barrido continuo cubre 360º con una imagen cada `PASO_BARRIDO`, tarda menos que por pasos
  y deja de girar en cuanto ataca a los robots esperados;
- la memoria no repite un robot visto desde otra parada, distingue dos robots juntos, vuelve a
  atacar a uno que se ha alejado y olvida los descartes;
- `ROBOTS_TOTALES` salta los barridos restantes sin dejar de hacer el recorrido;
- la distancia por el alto de la caja y la posición del chasis son correctas;
- con `DISPARAR_A_TODOS = False` dispara solo a la mejor detección de cada imagen;
- guarda todas las imágenes;
- respeta `--sin-disparar`, `--sin-mover` y `--paradas`;
- usa los seis módulos;
- nunca pasa de la velocidad del SDK;
- Ctrl+C deja el robot parado y con el LED apagado;
- el código es válido en Python 3.8.

El simulador falla si alguna orden supera la velocidad máxima. Lleva un reloj simulado:
cada lectura de la cámara avanza 0,1 s (unas 10 imágenes por segundo, como con GPU), los
giros del gimbal y los movimientos del chasis consumen su tiempo, `drive_speed` hace girar
el gimbal mientras pasa el tiempo y el chasis lleva su posición. Los robots falsos pueden
darse por su ángulo o por su posición en el circuito (en metros), y entonces su caja
crece o mengua con la distancia.

Tiempo de una parada medido en simulación, contando la espera de 0,5 s del barrido por
pasos y 0,1 s de inferencia por imagen (GPU):

| Parada | Por pasos | Continuo |
|---|---:|---:|
| 360º, sin robots | 24,2 s | 20,8 s |
| 360º, robot en +100º | 15,4 s | 14,6 s |
| 360º, robot en −100º | 28,8 s | 24,8 s |
| 360º, robots en +30º y −120º | 34,0 s | 31,4 s |
| Frontal, sin robots | 8,1 s | 7,3 s |

La mejora es de un 5 a un 15 %: el límite es girar la torreta a 30 º/s, que no se puede
subir. Lo que más ahorra es no repetir ráfagas de unos 4 s contra robots ya atacados.

### Ajustar el seguimiento en el laboratorio

Al arrancar, la demo gira la torreta 20º y comprueba que `sub_angle` sigue el giro. Escribe
`Torreta: lectura del ángulo comprobada` o, si no, que estima el ángulo por software.
Después, con `--sin-mover --sin-disparar --ver` y un compañero moviendo un robot delante:

- **Oscila** (va y viene alrededor del robot): bajar `GANANCIA_SEGUIMIENTO` (por ejemplo,
  a 1,5) o subir `RETARDO_CAMARA`.
- **Va siempre detrás** de un robot que se mueve: comprobar `ANTICIPAR = True` y bajar
  `RETARDO_CAMARA` si está muy por encima del real.
- **Lo pierde** con el movimiento: bajar `UMBRAL_SEGUIMIENTO` o subir `PERDIDAS_MAX`.
- **Apunta alto o bajo:** ajustar `ALTURA_PUNTERIA` según dónde lleve el robot rival el
  receptor de infrarrojos.

El retardo real se puede estimar con `registro.csv`: en un giro a velocidad constante, la
caja de un robot quieto se desplaza en la imagen con el retraso que haya.

## 6. Notas

- **Tiempo de inferencia.** Medido en CPU con Python 3.8 y PyTorch 2.4.1 (32 hilos,
  imagen de 1280×720): Faster R-CNN v2 tarda unos 1,1 s por imagen y Faster R-CNN v3 unos
  0,3 s. Un ordenador del laboratorio con menos núcleos tardará más. Como el robot se para
  a mirar, solo alarga cada parada. `resumen.json` da la media real. Si es excesivo, se
  puede usar `RESIZE` o `--arquitectura faster_rcnn_v3` (AP@0,5 de 0,9240 en test).
- **Checkpoints de numpy 2.** El checkpoint guarda el estado de numpy. Si se guardó en
  JupyterHub con numpy 2, no se puede leer con numpy 1.x, que es el único disponible en
  Python 3.8. `torch_load_cpu` lo detecta y lo vuelve a cargar traduciendo
  `numpy._core` a `numpy.core`. Está comprobado con Python 3.8.20, PyTorch 2.4.1 y
  numpy 1.24.
- **`torch_load_cpu`** usa `weights_only=False` porque el checkpoint guarda también el
  estado de numpy y de `random`. Con PyTorch 2.6 o posterior fallaría sin ello; en el
  entorno de la asignatura (PyTorch 2.4) funciona igual.
- **Grabar el circuito.** `camera/record.py` graba el circuito y sus obstáculos, y las
  imágenes de `evidencias/*/originales/` sirven para anotar los fallos y reentrenar,
  como dejó previsto T02.
