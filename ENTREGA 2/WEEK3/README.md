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
2. **Barrido.** El gimbal se centra y gira a cada ángulo de `barrido`. En cada
   ángulo espera medio segundo, captura una imagen y aplica el detector. El barrido
   de 360º usa pasos de 60º: la cámara ve unos 90º y así cada imagen solapa con la
   siguiente.
3. **Selección.** Se quedan las detecciones con confianza `>= UMBRAL` y se calcula el
   ángulo de cada una: el yaw del gimbal más `auto_aim`. Una detección a menos de
   `TOLERANCIA_YAW` (15º) de otra ya revisada en la parada es el mismo robot visto en
   dos imágenes y no se repite.
4. **Puntería y disparo.** Para cada robot nuevo, el gimbal gira hacia él y vuelve a
   detectar ya apuntado (`CONFIRMAR`). Si la caja más centrada está a menos de
   `TOLERANCIA_YAW` del centro y no es un robot ya atacado, corrige el error y dispara
   12 veces. Si no, no dispara: era un falso positivo, el robot se ha movido o se iba a
   disparar dos veces al mismo. Tras disparar, el gimbal cabecea y el LED se pone verde.
5. **Fin de la parada.** Si se han atacado los `objetivos` esperados en la parada, se
   deja de barrer (salvo `BARRIDO_COMPLETO = True`). El gimbal vuelve al centro.

Al terminar: vuelta al inicio (opcional) y baile final con LED, sonido, gimbal y chasis.

**Estrategia elegida** (se puede cambiar en `circuito.py`):

- Se dispara a **todas** las detecciones nuevas que superan el umbral
  (`DISPARAR_A_TODOS`), porque hay que inutilizar a todos los robots.
- Se barre **hasta encontrar los robots esperados** en esa parada, no siempre 360º. Si
  no se sabe cuántos hay (`objetivos=None`), se completa el barrido.
- Se confirma antes de disparar. Cuesta una inferencia más, pero evita gastar los 12
  disparos en un falso positivo y corrige la puntería.

**Módulos usados**, como pide el enunciado:

| Módulo | Uso |
|---|---|
| Chasis | Recorrido entre paradas y baile |
| Gimbal (torreta) | Barrido, puntería, cabeceo tras inutilizar un robot y baile |
| Cámara | Vídeo abierto toda la demo; se lee el fotograma más reciente con el gimbal quieto |
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
| `AUDIO_DISPARO` (`audio/propios/scar.wav`) | Con cada uno de los 12 disparos. Se espera a que acabe antes del siguiente, porque el SDK no admite dos sonidos a la vez |
| `AUDIO_FINAL` (`audio/propios/superestrella.wav`) | En el baile final. Los LED cambian de color `LED_FIESTA_HZ` veces por segundo mientras suena |

`audio/propios/` no se sube a GitHub, porque las canciones y los sonidos de juegos tienen
derechos de autor. Si un audio no existe, la demo usa los sonidos del SDK. Hace falta
`pip install imageio-ffmpeg`, que trae ffmpeg.

## 3. Evidencias

Cada ejecución crea `evidencias/<fecha_hora>/` (no se sube a GitHub):

- Una imagen por cada inferencia, con nombre `NNN_parada_fase_yawXX.jpg`. Lleva las
  cajas y la confianza dibujadas: verde si se acepta, naranja si se queda entre 0,3 y
  el umbral. El objetivo tiene una cruz roja y el título indica la parada, el yaw, el
  umbral y el tiempo de inferencia. Las fases son `barrido`, `confirmado` y
  `sin_confirmar`.
- `originales/`: las mismas imágenes sin dibujar, para analizarlas o anotarlas después.
- `registro.csv`: una fila por imagen con yaw, tiempo de inferencia, confianzas, cajas,
  ángulo del objetivo y disparos.
- `resumen.json`: configuración, robots atacados por parada, disparos totales, tiempo
  medio de inferencia y duración.

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
2. **Modelo.** `model_demo.pt` (173 MB, solo `{'model': state_dict}`) está en la release
   [`modelo-demo-v1`](https://github.com/javiersaguar/PIDS-Proyecto2/releases/tag/modelo-demo-v1).
   Desde esta carpeta se descarga con:
   ```
   gh release download modelo-demo-v1 --repo javiersaguar/PIDS-Proyecto2 -p model_demo.pt -D models/faster_rcnn_v2_aug_robusto_v1_lr001
   ```
   Sin `gh`, se descarga desde la página de la release. Tiene que quedar en
   `models/faster_rcnn_v2_aug_robusto_v1_lr001/model_demo.pt`, junto a `demo.py`; es la
   ruta de `RUTA_MODELO`. Su SHA-256 es
   `f46a49d7c8cb2ced6061738b01a99a1c9f476a4aea9c83a6967e7909d5b63141`, que se comprueba con
   `certutil -hashfile <fichero> SHA256` en Windows o `sha256sum <fichero>` en Linux.
   Ocupa más de los 100 MB que admite git en GitHub, así que no se versiona: `models/`
   está ignorado. `demo.py` comprueba que el checkpoint trae los 404 tensores de la
   arquitectura.

   Para exportarlo de nuevo desde `model_best.pt` (346 MB, porque guarda también el
   optimizador), en un terminal de JupyterHub:
   ```
   python -c "import os,torch;d=os.path.expanduser('~/pids_main/models/faster_rcnn_v2_aug_robusto_v1_lr001/');c=torch.load(d+'model_best.pt',map_location='cpu',weights_only=False);torch.save({'model':c['model']},d+'model_demo.pt')"
   ```
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
- con `DISPARAR_A_TODOS = False` dispara solo a la mejor detección de cada imagen;
- guarda todas las imágenes;
- respeta `--sin-disparar`, `--sin-mover` y `--paradas`;
- usa los seis módulos;
- nunca pasa de la velocidad del SDK;
- Ctrl+C deja el robot parado y con el LED apagado;
- el código es válido en Python 3.8.

El simulador falla si alguna orden supera la velocidad máxima.

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
