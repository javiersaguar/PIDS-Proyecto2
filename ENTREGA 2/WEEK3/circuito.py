"""Configuración del circuito y de la estrategia de la demo (Bloque 3).

Todo lo que se ajusta en el laboratorio está aquí, para no tocar demo.py.

Ejes del chasis (SDK RoboMaster): x > 0 avanza, y > 0 va a la derecha,
z > 0 gira a la izquierda (grados). Gimbal: yaw > 0 mira a la derecha.
Los movimientos de cada parada son relativos a donde acaba la anterior.

Los valores de PARADAS son un ejemplo: hay que medirlos sobre el circuito real
y probarlos primero con `python demo.py --sin-disparar`, con un compañero al
lado del robot y Ctrl+C a mano.
"""

from recorrido import paradas_desde_plano

# --- Modelo -------------------------------------------------------------------
# Modelo final del Bloque 2 (Faster R-CNN v2, umbral fijado en validación).
MODELO = 'faster_rcnn_v2'
RUTA_MODELO = 'models/faster_rcnn_v2_aug_robusto_v1_lr001/model_demo.pt'  # solo los pesos de model_best.pt (ver README)
UMBRAL = 0.95
RESIZE = None            # (alto, ancho) si la inferencia en el portátil es demasiado lenta
USAR_GPU = True          # si no hay GPU se usa la CPU

# --- Estrategia de detección ----------------------------------------------------
DISPAROS_POR_ROBOT = 20  # el enunciado pide 12 impactos; 20 por si el rival no registra alguno
DISPARAR_A_TODOS = True  # True: a todas las detecciones nuevas >= UMBRAL; False: solo a la mejor de cada imagen
BARRIDO_COMPLETO = False # False: se deja de girar en cuanto se han atacado los `objetivos` de la parada
CONFIRMAR = True         # volver a detectar ya apuntado antes de disparar y corregir el error de puntería
TOLERANCIA_YAW = 15      # grados: dos detecciones más cercanas se tratan como el mismo robot
SIGNO_YAW = 1            # poner -1 si en la prueba el gimbal gira hacia el lado contrario del robot
ESPERA_CAMARA = 1.0      # s de espera tras mover el gimbal antes de capturar (el vídeo llega con retraso por wifi)
CORRECCIONES_PUNTERIA = 4  # giros de corrección como mucho hasta centrar el robot antes de disparar
TOLERANCIA_PUNTERIA = 3  # grados: centrado si el error es menor (o menor que el 30 % del ancho del robot)

# --- Mejoras de la PR 36: todas desactivadas por defecto ------------------------------
# Con SEGUIMIENTO, BARRIDO_CONTINUO, MEMORIA, VIGILANCIA y LEER_ANGULO_GIMBAL a False la demo
# hace lo mismo que la de main (confirmación única y ráfaga de 12 con la SCAR en cada disparo).
# Se activan en el laboratorio de una en una, en este orden, comprobando cada una con el
# robot (pasos en el README): LEER_ANGULO_GIMBAL, SEGUIMIENTO, BARRIDO_CONTINUO,
# MEMORIA (tras calibrar ALTURA_ROBOT) y VIGILANCIA.

# --- Seguimiento del objetivo (los rivales se mueven) ------------------------------
# Con SEGUIMIENTO, al fijar un robot la torreta lo sigue imagen a imagen (gimbal.drive_speed)
# y solo dispara cuando está centrado, hasta DISPAROS_POR_ROBOT. La ganancia se adapta al
# tiempo medido por imagen (CORRECCION_POR_IMAGEN), así que funciona con CPU (~1,1 s por
# imagen, 12 disparos en unos 15 s) y con GPU (~0,1 s, unos 4 s).
# False: confirmación única y ráfaga sin mirar (como en main).
SEGUIMIENTO = False
UMBRAL_SEGUIMIENTO = 0.8 # ya fijado el robot, confianza mínima para no perderlo (para fijarlo hace falta UMBRAL)
SALTO_MAX = 25           # grados: una detección más lejos de donde se espera el robot es otro robot
TOLERANCIA_DISPARO = 3   # grados de error mínimos admitidos para disparar (crece con el tamaño de la caja)
INTERVALO_DISPARO = 0.3  # s mínimos entre dos disparos (los mismos que en main)
GANANCIA_SEGUIMIENTO = 2.0  # º/s de giro por grado de error; más alto reacciona antes, pero puede oscilar
CORRECCION_POR_IMAGEN = 0.8 # la ganancia se limita a esto / (s por imagen medidos): con CPU (~1,1 s) queda en ~0,7
ANTICIPAR = True         # sumar al giro la velocidad estimada del robot, para no ir siempre detrás de él
RETARDO_CAMARA = 0.25    # s entre que la cámara ve algo y la imagen llega al ordenador (wifi); medir en el laboratorio
PERDIDAS_MAX = 5         # imágenes seguidas sin ver al robot antes de darlo por perdido
TIEMPO_MAX_OBJETIVO = 20 # s máximos persiguiendo a un mismo robot (crece si cada imagen tarda más de 0,8 s)
CORREGIR_PITCH = True    # apuntar también en vertical
ALTURA_PUNTERIA = 0.5    # punto de la caja al que se apunta: 0 borde superior, 0.5 centro, 1 borde inferior
LEER_ANGULO_GIMBAL = False # usar el ángulo real del gimbal (sub_angle), comprobado al arrancar, en lugar de sumar los giros
SONIDO_CADA_DISPARO = True  # AUDIO_DISPARO en cada disparo, como en main. False: solo al empezar la ráfaga
                            # (con SEGUIMIENTO es más rápido: el SDK sube el audio al robot en cada disparo)

# --- Barrido continuo y memoria de robots atacados -----------------------------------
# Con BARRIDO_CONTINUO, la torreta gira sin pararse entre los extremos del barrido de la
# parada y analiza una imagen cada PASO_BARRIDO grados; en cuanto ve un robot nuevo lo
# sigue y le dispara, y después continúa. False: se para en cada ángulo de `barrido`.
# Solo actúa con SEGUIMIENTO.
BARRIDO_CONTINUO = False
VEL_BARRIDO = 30         # º/s de la torreta al barrer (nunca más de 30, la del SDK)
PASO_BARRIDO = 10        # grados girados entre dos imágenes analizadas (unas 3 por segundo a 30 º/s)
CAMPO_VISION = 70        # grados del campo de visión útil (la cámara ve unos 90; los bordes cortan robots)
# Memoria de robots atacados, en metros sobre el circuito: posición del chasis por sus
# movimientos y distancia al robot por el alto de su caja. Una detección dentro de la
# tolerancia de un robot atacado se considera el mismo robot y no se le vuelve a disparar.
# La tolerancia es RADIO_MISMO_ROBOT de lado y crece con ERROR_DISTANCIA a lo largo de la
# línea de visión, porque la distancia estimada es aproximada y el ángulo no.
# Sin MEMORIA los atacados se anotan en resumen.json, pero no se usan para dejar de disparar
# (como en main, cada parada empieza de cero). Activarla tras calibrar ALTURA_ROBOT.
MEMORIA = False
ALTURA_ROBOT = 0.35      # m que mide la caja de un RoboMaster (calibrar: robot a 1,5 m y ver distancia_m)
RADIO_MISMO_ROBOT = 0.35 # m: dos RoboMasters no caben más cerca; si el atacado se aleja más, se le repite
ERROR_DISTANCIA = 0.25   # m de tolerancia extra, a lo largo de la línea de visión, por metro de distancia
TIEMPO_MEMORIA = None    # s tras los que se olvida un robot atacado (None: nunca)
TIEMPO_DESCARTE = 3.0    # s sin volver a intentar fijar una detección que no se pudo confirmar
ROBOTS_TOTALES = None    # robots rivales en el circuito; al atacarlos todos, el resto de paradas no barre

# --- Vigilancia durante el recorrido ---------------------------------------------------
# Con VIGILANCIA, cada avance entre paradas se divide en tramos de TRAMO_VIGILANCIA m y la
# torreta mira hacia donde va el robot. Con el chasis en marcha se analiza una imagen cada
# INTERVALO_RUTA s. Al acabar un tramo, si se ha visto un rival nuevo, se para y lo ataca
# (ATACAR_EN_RUTA); si hay un robot en el pasillo del siguiente tramo, espera a que se aparte.
# Solo se detectan RoboMasters: los obstáculos fijos se evitan con el diseño del recorrido.
# La distancia sale de ALTURA_ROBOT: calibrarla antes de activar la vigilancia.
VIGILANCIA = False
TRAMO_VIGILANCIA = 0.5   # m de cada tramo; los giros (z) no se dividen
INTERVALO_RUTA = 0.3     # s entre imágenes analizadas con el chasis en marcha
PITCH_RUTA = 0           # inclinación de la torreta durante el recorrido
ATACAR_EN_RUTA = True    # parar a atacar a un rival nuevo visto en el recorrido
ANCHO_PASILLO = 0.6      # m de ancho del camino vigilado (un robot mide unos 0,24 m de ancho)
DISTANCIA_SEGURIDAD = 0.4  # m libres que se exigen más allá del final del tramo
ESPERA_OBSTACULO = 15    # s esperando a que se aparte un robot del camino; después se sigue el recorrido
DETENER_SI_BLOQUEADO = False  # True: pasado ESPERA_OBSTACULO, detener la demo en lugar de seguir

# Barrido de 360º en pasos de 60º: la cámara ve unos 90º, así que cada imagen
# solapa con la siguiente. Empieza por delante, que es donde es más probable el rival.
BARRIDO_360 = [0, 60, 120, 180, -120, -60]
BARRIDO_FRONTAL = [0, -45, 45]

# --- Recorrido --------------------------------------------------------------------
# Las paradas se miden sobre el plano del circuito (ver recorrido.py): origen en la
# salida de nuestro robot (esquina de arriba a la izquierda del boceto), x en metros
# hacia la derecha, y en metros hacia abajo. Rumbos: 0 derecha, 90 abajo, 180
# izquierda, -90 arriba. Antes de probar, revisar lo calculado con
#     python recorrido.py
#
# Se rellena movimiento a movimiento con las pruebas en el circuito real
# (python probar_recorrido.py --paso N). Hasta conocer la orientación del boceto,
# x es la dirección en la que mira el robot en la salida (RUMBO_INICIAL = 0).
RUMBO_INICIAL = 0        # hacia dónde mira nuestro robot en la salida (0 = derecha del boceto)
# Ataque en marcha (movimientos con atacar=yaw): la torreta busca al rival mientras el
# chasis avanza, lo sigue y dispara la ráfaga sin parar. Con CPU cada imagen tarda ~2 s y
# la ráfaga 6 s: a 0,1 m/s, 1,25 m dan unos 12 s, lo justo para girar, verlo y disparar.
VELOCIDAD_ATAQUE_EN_MARCHA = 0.1  # m/s del chasis mientras ataca
IMAGENES_TRAS_PARAR = 3           # si al acabar el avance aún no lo ha visto, imágenes que sigue buscando parado
TIEMPO_MAX_ATAQUE_EN_MARCHA = 40  # s como mucho buscando y disparando en un mismo avance
GIRAR_EN_RUTA = True     # True: gira hacia cada punto y avanza; False: va en diagonal sin girar (mecanum)
PLANO = [
    # nombre, punto donde se para, puntos intermedios (por), rumbo al llegar (mirar),
    # rivales (puntos donde se espera un robot: el barrido mira hacia ellos)
    # paso 1: 2,85 m en línea recta (medido el 05/11). Paso 2: la torreta gira a la derecha
    # unos 90º (si no lo ve, prueba a 60º y 120º), detecta al rival y le dispara
    dict(nombre='P1', punto=(2.85, 0.0), barrido=[90, 60, 120], pitch=0, objetivos=1),
    # paso 3: la rotonda, con movimientos relativos del chasis sin girarlo (x adelante,
    # y derecha). Al retroceder, la torreta mira 90º a la izquierda y dispara al rival
    # que vea, sin parar. Al acabar no se barre (barrido=[]).
    dict(nombre='R1', movimientos=[
        dict(x=1.9, velocidad=0.4),                                       # adelante 1,9 m a 0,4 m/s
        dict(y=-1.0),                                                     # izquierda 1 m
        dict(x=-1.25, velocidad=VELOCIDAD_ATAQUE_EN_MARCHA, atacar=-90),  # atrás 1,25 m atacando a la izquierda
        dict(y=1.0),                                                      # derecha 1 m
    ], barrido=[]),
]
PARADAS = paradas_desde_plano(RUMBO_INICIAL, PLANO, girar=GIRAR_EN_RUTA, abanico=30, barrido_sin_rivales=BARRIDO_360)
# También se pueden escribir a mano, como antes: movimientos (x, y, z) relativos (x
# adelante, y derecha, z giro a la izquierda), barrido (yaws respecto al chasis), pitch
# y objetivos (robots que se espera ver; None = desconocido, barrido entero). Ejemplo:
#   PARADAS = [dict(nombre='P1', movimientos=[(1.0, 0, 0)], barrido=BARRIDO_FRONTAL, pitch=0, objetivos=1)]
VOLVER_AL_INICIO = False # deshacer el recorrido al terminar (en orden inverso)
# Velocidades del chasis. Se pueden bajar, nunca subir: demo.py las recorta a las del SDK (0,5 m/s y 30 º/s).
# Los avances van con drive_speed y la odometría, a VELOCIDAD_XY m/s reales. Con chassis.move
# el robot iba a unos 0,06 m/s: el SDK no convierte xy_speed a m/s reales.
VELOCIDAD_XY = 0.5       # m/s reales en los avances (máximo 0,5): 2,85 m en unos 6 s
AVANCE_CON_ODOMETRIA = True  # False: avances con chassis.move (mucho más lentos)
VELOCIDAD_Z = 30         # º/s

# --- Extras -------------------------------------------------------------------------
BAILE_FINAL = True
AUDIO_MOTOR = 'audio/engine_sound_corto.wav'  # 6 s al arrancar; None para no usarlo
# Audios propios (WAV mono 48 kHz, ver audio/convertir_audio.py). Van en audio/propios/,
# que no se sube a GitHub por los derechos de autor. Si no existen, se usan los sonidos del SDK.
# El SDK no sube el volumen del altavoz: se sube en el audio con audio/preparar_disparo.py, que
# crea scar_fuerte.wav (un disparo) y scar_rafaga.wav (los 12, cada INTERVALO_DISPARO s).
AUDIO_RAFAGA = 'audio/propios/scar_rafaga.wav'    # sin SEGUIMIENTO: suena una vez y se dispara a su ritmo
AUDIO_DISPARO = 'audio/propios/scar_fuerte.wav'   # un disparo: con SEGUIMIENTO, o si no hay AUDIO_RAFAGA
SILENCIO_AUDIO_DISPARO = 0.3 # s de silencio al principio de esos audios (--silencio de preparar_disparo.py)
AUDIO_FINAL = 'audio/propios/superestrella.wav'   # canción del baile final
ESPERA_AUDIO_DISPARO = 2.0   # s máximos que se espera al audio de cada disparo (sin SEGUIMIENTO ni AUDIO_RAFAGA)
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
