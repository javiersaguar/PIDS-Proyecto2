# Semana 3 · Integración del detector en el robot (Bloque 3)

Material de la asignatura para el Bloque 3 (`WEEK3.1`, subido por Alejandro el
14/10/2026). Los ficheros están tal como los da la asignatura; lo que hay que hacer
está en la [sección 3](#3-qué-hay-que-hacer).

**Objetivo del bloque:** que el RoboMaster recorra el circuito, detecte a los robots
rivales con nuestro modelo, apunte el gimbal hacia ellos y dispare.

## 1. Contenido

| Fichero | Qué hace |
|---|---|
| `pyproject.toml`, `pixi.lock` | Entorno de la asignatura (pixi, Python 3.8): SDK `robomaster`, PyTorch, albumentations, torchmetrics, pycocotools |
| `connect.py` | Une el robot a la wifi: genera un QR que el robot escanea y guarda su número de serie en `serial_number.txt` |
| `demo_utils.py` | Funciones listas para usar: `connect`, `get_model` (carga el modelo entrenado), `predict` (captura un fotograma y detecta), `auto_aim` (ángulo de giro hacia una caja) y `plot_predictions` (guarda lo detectado) |
| **`demo.py`** | **La demo: es lo que hay que completar** |
| `camera/stream.py`, `camera/record.py` | Ver la cámara en directo y grabar 200 fotogramas en `recording.mp4` |
| `chassis/chassis_distance.py`, `chassis/chassis_speed.py` | Mover el chasis una distancia o a una velocidad |
| `gimbal/gimbal_degrees.py`, `gimbal/gimbal_speed.py` | Mover el gimbal a un ángulo o a una velocidad |
| `others/blaster.py`, `others/led.py`, `others/battery.py` | Disparar (agua o infrarrojo), cambiar los LED y leer la batería |

Los ejemplos de `camera/`, `chassis/`, `gimbal/` y `others/` son independientes: cada
uno se conecta, hace una cosa y se desconecta. Sirven para aprender el SDK antes de
tocar la demo.

## 2. Puesta en marcha

1. **Entorno.** El SDK `robomaster` solo funciona con Python 3.6–3.8, así que se usa
   el entorno de la asignatura: `pixi install` en esta carpeta y `pixi shell` para
   activarlo. Se ejecuta en un portátil conectado a la misma wifi que el robot, no en
   JupyterHub.
2. **Conectar el robot**, una sola vez por red:
   - En `connect.py`, rellenar `WIFI_SSID`, `WIFI_PASSWD` y `SERIAL_NUMBER` **solo en
     local**. **No hacer commit de esos valores.**
   - `python connect.py` y enseñar el QR a la cámara del robot.
   - Se crean `serial_number.txt` y `qrcode.png`. El QR contiene la contraseña del
     wifi; los dos ficheros están en el `.gitignore` de esta carpeta.
3. **Probar el SDK** con los ejemplos, por ejemplo `python camera/stream.py` y
   `python gimbal/gimbal_degrees.py`.
4. **Copiar el modelo entrenado.** `demo.py` lo busca en
   `../models/faster_rcnn_v1/model_best.pt`, pero `train.ipynb` lo guarda en
   `models/<experimento>/model_best.pt`, en la raíz del repositorio. Por ejemplo,
   `models/faster_rcnn_v1_aug/model_best.pt`. Hay que descargarlo de JupyterHub y
   ajustar `model_path` en `demo.py`. El modelo no se sube a GitHub (pesa unos 160 MB).

## 3. Qué hay que hacer

En `demo.py`:

1. **`detect_and_shoot`**, pasos 2 a 4:
   - quedarse con las detecciones con `score >= score_threshold`; si no hay ninguna,
     devolver la imagen y la predicción sin disparar;
   - elegir la caja con mayor confianza;
   - girar el gimbal el ángulo que devuelve `auto_aim(image, best_box)`;
   - disparar con `blaster.INFRARED_FIRE`.
2. **El recorrido**, en el `__main__`: para cada objetivo, mover el chasis hasta su
   posición, orientar el gimbal hacia él, llamar a `detect_and_shoot` y guardar la
   imagen con `plot_predictions`. Después, repetirlo para los demás objetivos.

## 4. Antes de la demo

- **Umbral de confianza.** `score_threshold = 0.5` es el valor por defecto. Conviene
  usar el umbral que mejor resultado dé en `test.ipynb` (la curva de precisión y
  exhaustividad según el umbral).
- **Tiempo de inferencia.** `test.ipynb` mide cuánto tarda el modelo por imagen.
  En el portátil, sin GPU, será bastante más lento que en JupyterHub; si no es
  suficiente, se puede probar `resize_shape` o un modelo más ligero
  (`faster_rcnn_v3`, `ssd_v2`).
- **Versión de PyTorch.** `demo_utils.torch_load_cpu` usa `torch.load` sin
  `weights_only=False`. Con PyTorch 2.6 o posterior fallaría al cargar nuestro
  checkpoint; con el entorno de la asignatura (PyTorch 2.4) funciona.
- **Grabar el circuito real.** `camera/record.py` permite grabar el circuito y sus
  obstáculos para anotarlos y reentrenar si el modelo falla allí, como dejó previsto T02.
