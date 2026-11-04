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

# --- Seguimiento del objetivo (los rivales se mueven) ------------------------------
# Con SEGUIMIENTO, al fijar un robot la torreta lo sigue imagen a imagen (gimbal.drive_speed)
# y solo dispara cuando está centrado, hasta DISPAROS_POR_ROBOT. Con GPU se analizan unas
# 10 imágenes por segundo. False vuelve a la confirmación única y la ráfaga sin mirar.
SEGUIMIENTO = True
UMBRAL_SEGUIMIENTO = 0.8 # ya fijado el robot, confianza mínima para no perderlo (para fijarlo hace falta UMBRAL)
SALTO_MAX = 25           # grados: una detección más lejos de donde se espera el robot es otro robot
TOLERANCIA_DISPARO = 3   # grados de error mínimos admitidos para disparar (crece con el tamaño de la caja)
INTERVALO_DISPARO = 0.25 # s mínimos entre dos disparos
GANANCIA_SEGUIMIENTO = 2.0  # º/s de giro por grado de error; más alto reacciona antes, pero puede oscilar
ANTICIPAR = True         # sumar al giro la velocidad estimada del robot, para no ir siempre detrás de él
RETARDO_CAMARA = 0.25    # s entre que la cámara ve algo y la imagen llega al ordenador (wifi); medir en el laboratorio
PERDIDAS_MAX = 5         # imágenes seguidas sin ver al robot antes de darlo por perdido
TIEMPO_MAX_OBJETIVO = 20 # s máximos persiguiendo a un mismo robot
CORREGIR_PITCH = True    # apuntar también en vertical
ALTURA_PUNTERIA = 0.5    # punto de la caja al que se apunta: 0 borde superior, 0.5 centro, 1 borde inferior
LEER_ANGULO_GIMBAL = True  # usar el ángulo real del gimbal (sub_angle) en lugar de sumar los giros
SONIDO_CADA_DISPARO = False  # True: AUDIO_DISPARO en cada disparo (más lento: el SDK sube el audio cada vez)

# --- Barrido continuo y memoria de robots atacados -----------------------------------
# Con BARRIDO_CONTINUO, la torreta gira sin pararse entre los extremos del barrido de la
# parada y analiza una imagen cada PASO_BARRIDO grados; en cuanto ve un robot nuevo lo
# sigue y le dispara, y después continúa. False: se para en cada ángulo de `barrido`.
BARRIDO_CONTINUO = True
VEL_BARRIDO = 30         # º/s de la torreta al barrer (nunca más de 30, la del SDK)
PASO_BARRIDO = 10        # grados girados entre dos imágenes analizadas (unas 3 por segundo a 30 º/s)
CAMPO_VISION = 70        # grados del campo de visión útil (la cámara ve unos 90; los bordes cortan robots)
# Memoria de robots atacados, en metros sobre el circuito: posición del chasis por sus
# movimientos y distancia al robot por el alto de su caja. Una detección dentro de la
# tolerancia de un robot atacado se considera el mismo robot y no se le vuelve a disparar.
# La tolerancia es RADIO_MISMO_ROBOT de lado y crece con ERROR_DISTANCIA a lo largo de la
# línea de visión, porque la distancia estimada es aproximada y el ángulo no.
ALTURA_ROBOT = 0.35      # m que mide la caja de un RoboMaster (calibrar: robot a 1,5 m y ver distancia_m)
RADIO_MISMO_ROBOT = 0.35 # m: dos RoboMasters no caben más cerca; si el atacado se aleja más, se le repite
ERROR_DISTANCIA = 0.25   # m de tolerancia extra, a lo largo de la línea de visión, por metro de distancia
TIEMPO_MEMORIA = None    # s tras los que se olvida un robot atacado (None: nunca)
TIEMPO_DESCARTE = 3.0    # s sin volver a intentar fijar una detección que no se pudo confirmar
ROBOTS_TOTALES = None    # robots rivales en el circuito; al atacarlos todos, el resto de paradas no barre

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
AUDIO_MOTOR = 'audio/engine_sound_corto.wav'  # 6 s al arrancar; None para no usarlo
# Audios propios (WAV mono 48 kHz, ver audio/convertir_audio.py). Van en audio/propios/,
# que no se sube a GitHub por los derechos de autor. Si no existen, se usan los sonidos del SDK.
AUDIO_DISPARO = 'audio/propios/scar.wav'          # suena al empezar cada ráfaga (o en cada disparo, ver SONIDO_CADA_DISPARO)
AUDIO_FINAL = 'audio/propios/superestrella.wav'   # canción del baile final
ESPERA_AUDIO_DISPARO = 2.0   # s máximos que se espera al audio de cada disparo (solo sin SEGUIMIENTO y con SONIDO_CADA_DISPARO)
LED_FIESTA_HZ = 10           # cambios de color por segundo en el baile final
DURACION_FIESTA_MAX = 40     # s máximos de luces tras el baile mientras suena la canción
# Sonidos predefinidos del SDK (robot.SOUND_ID_*); se pueden escuchar con audio/predefined_sounds.py
SONIDOS = {
    'inicio': 0x106,       # cuenta atrás
    'buscando': 0x103,     # escaneo
    'detectado': 0x104,    # objetivo reconocido
    'disparo': 0x102,      # disparo
    'hecho': 0x101,        # ataque completado
}
BATERIA_MINIMA = 20      # % por debajo del cual se avisa antes de arrancar
BATERIA_CRITICA = 10     # % por debajo del cual la demo no arranca (el robot deja de responder)
