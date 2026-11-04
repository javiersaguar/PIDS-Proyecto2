"""Configuración del circuito y de la estrategia de la demo (Bloque 3).

Todo lo que se ajusta en el laboratorio está aquí, para no tocar demo.py.

Ejes del chasis (SDK RoboMaster): x > 0 avanza, y > 0 va a la derecha,
z > 0 gira a la izquierda (grados). Gimbal: yaw > 0 mira a la derecha.
Los movimientos de cada parada son relativos a donde acaba la anterior.

Los valores de PARADAS son un ejemplo: hay que medirlos sobre el circuito real
y probarlos primero con `python demo.py --sin-disparar`, con un compañero al
lado del robot y Ctrl+C a mano.
"""

# --- Modelo -------------------------------------------------------------------
# Modelo final del Bloque 2 (Faster R-CNN v2, umbral fijado en validación).
MODELO = 'faster_rcnn_v2'
RUTA_MODELO = 'models/faster_rcnn_v2_aug_robusto_v1_lr001/model_demo.pt'  # solo los pesos de model_best.pt (ver README)
UMBRAL = 0.95
RESIZE = None            # (alto, ancho) si la inferencia en el portátil es demasiado lenta
USAR_GPU = True          # si no hay GPU se usa la CPU

# --- Estrategia de detección ----------------------------------------------------
DISPAROS_POR_ROBOT = 12  # el enunciado pide 12 impactos para inutilizar un robot
DISPARAR_A_TODOS = True  # True: a todas las detecciones nuevas >= UMBRAL; False: solo a la mejor de cada imagen
BARRIDO_COMPLETO = False # False: se deja de girar en cuanto se han atacado los `objetivos` de la parada
CONFIRMAR = True         # volver a detectar ya apuntado antes de disparar y corregir el error de puntería
TOLERANCIA_YAW = 15      # grados: dos detecciones más cercanas se tratan como el mismo robot
SIGNO_YAW = 1            # poner -1 si en la prueba el gimbal gira hacia el lado contrario del robot
ESPERA_CAMARA = 0.5      # s de espera tras mover el gimbal antes de capturar (imagen sin movimiento)

# Barrido de 360º en pasos de 60º: la cámara ve unos 90º, así que cada imagen
# solapa con la siguiente. Empieza por delante, que es donde es más probable el rival.
BARRIDO_360 = [0, 60, 120, 180, -120, -60]
BARRIDO_FRONTAL = [0, -45, 45]

# --- Recorrido --------------------------------------------------------------------
# nombre: aparece en las evidencias. movimientos: lista de (x, y, z) que se
# ejecutan en orden para llegar a la parada. barrido: yaw del gimbal (grados,
# respecto al frente del chasis) donde se captura. pitch: inclinación del gimbal.
# objetivos: robots que se espera ver desde ahí (None = desconocido, barrido entero).
PARADAS = [
    dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=BARRIDO_FRONTAL, pitch=0, objetivos=1),
    dict(nombre='P2', movimientos=[(0, 0, 90), (1.0, 0, 0)], barrido=BARRIDO_360, pitch=0, objetivos=1),
    dict(nombre='P3', movimientos=[(0, 0, -90), (0.8, 0, 0)], barrido=BARRIDO_360, pitch=0, objetivos=None),
]
VOLVER_AL_INICIO = False # deshacer el recorrido al terminar (en orden inverso)
# Velocidades del chasis. Se pueden bajar, nunca subir: demo.py las recorta a las del SDK (0,5 m/s y 30 º/s).
VELOCIDAD_XY = 0.3       # m/s
VELOCIDAD_Z = 30         # º/s

# --- Extras -------------------------------------------------------------------------
BAILE_FINAL = True
AUDIO_MOTOR = 'audio/engine_sound.wav'  # se reproduce al arrancar; None para no usarlo
# Sonidos predefinidos del SDK (robot.SOUND_ID_*); se pueden escuchar con audio/predefined_sounds.py
SONIDOS = {
    'inicio': 0x106,       # cuenta atrás
    'buscando': 0x103,     # escaneo
    'detectado': 0x104,    # objetivo reconocido
    'disparo': 0x102,      # disparo
    'hecho': 0x101,        # ataque completado
}
BATERIA_MINIMA = 20      # % por debajo del cual se avisa antes de arrancar
