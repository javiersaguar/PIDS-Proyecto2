# Cómo funciona el código del Bloque 3

Explicación bloque a bloque de la demo autónoma del circuito y de la interfaz del mando,
con la lógica de cada decisión. Estado del 11/11/2026. Todo está en `ENTREGA 2/WEEK3`.

## Mapa

```
circuito.py ──► recorrido.py ──► PARADAS (movimientos + barridos)
     │                                  │
     └──────────────► demo.py ◄─────────┘
                        │  usa
                        ▼
                  demo_utils.py   (cámara, detector, puntería, avance, LED y sonido)
                        ▲
demo_gpu.py ────────────┘  (misma demo; cambia detectar() por el detector en la GPU)

rival/rival_movil.py      (otro portátil: mueve el rival 2 al recibir un aviso)

mando/servidor.py ─► mando/conductor.py ─► robot
        │                  ▲
        │            mando/deteccion.py ─► mando/detector_gpu.py
        ▼
 mando/web/ (index.html, mando.js, app.js, escena3d.js)
```

Idea general:

- `circuito.py` dice **qué** hacer (dónde parar, a quién buscar, umbrales).
- `recorrido.py` lo pasa a movimientos del chasis.
- `demo.py` decide **cuándo** hacer cada cosa.
- `demo_utils.py` sabe **cómo** se hace cada acción con el robot.

---

# Parte 1. La demo del circuito

## 1. `circuito.py`: la configuración

Todo lo que se ajusta en el laboratorio está aquí, para no tocar la lógica.

### Bloque «Modelo»
- `MODELO` y `RUTA_MODELO`: el Faster R-CNN v2 del Bloque 2.
- `UMBRAL = 0.95`: confianza mínima para que una caja cuente como robot. Es alto a propósito: preferimos no disparar a disparar a algo que no es un robot.

### Bloque «Estrategia de detección»
- `DISPAROS_POR_ROBOT = 20`. El enunciado pide 12 impactos; los 8 de más cubren los que el rival no registre.
- `CONFIRMAR = True`: antes de disparar se vuelve a mirar con la torreta ya girada y se corrige la puntería.
- `TOLERANCIA_YAW = 15`: dos detecciones a menos de 15º se tratan como el mismo robot, para no atacarlo dos veces en la misma parada.
- `ESPERA_CAMARA = 1.0`: tras girar la torreta se espera 1 s antes de hacer la foto. El vídeo llega con retraso por wifi y, sin la espera, la foto sería de antes del giro.
- `CORRECCIONES_PUNTERIA = 4` y `TOLERANCIA_PUNTERIA = 3`: hasta 4 correcciones; se considera centrado con menos de 3º de error (o del 30 % del ancho del robot).
- **Robot camuflado (11/11):** el detective impreso daba entre 0,72 y 0,97, casi siempre por debajo de 0,95.
  - `UMBRAL_CAMUFLADO = 0.7` solo se aplica en un lado de una parada.
  - `ALTO_MAX_ZONA = 0.5` evita que con ese umbral bajo entren sillas cercanas, que dan cajas enormes.
- **Sillas (11/11):** `ALTO_MAX_ROBOT = 0.5`. Ninguna caja más alta que media imagen es un robot, aunque tenga 0,99. Un robot de ese tamaño estaría a menos de 0,5 m.

### Bloque «Mejoras de la PR 36» (desactivadas)
`SEGUIMIENTO`, `BARRIDO_CONTINUO`, `MEMORIA`, `VIGILANCIA` y `LEER_ANGULO_GIMBAL` están a `False`.

Son mejoras programadas, pero no validadas en el laboratorio. Con todas apagadas, la demo hace lo probado: confirmación por pasos y ráfaga. Siguen en el código porque se activan de una en una.

Del bloque se usan algunas constantes en el ataque en marcha:
- `RETARDO_CAMARA = 0.25`: s entre que la cámara ve algo y llega al ordenador;
- `GANANCIA_SEGUIMIENTO`, `CORRECCION_POR_IMAGEN`, `SALTO_MAX`, `UMBRAL_SEGUIMIENTO`;
- `INTERVALO_DISPARO = 0.3`.

### Bloque «Recorrido»
- `VELOCIDAD_ATAQUE_EN_MARCHA = 0.1`: en los ataques en marcha el chasis va despacio. Así da tiempo a girar la torreta, ver al rival, la voz y la ráfaga de 6 s.
- `GIRAR_TORRETA_ANTES = True` (11/11): la torreta empieza a girar hacia el ataque durante los tramos anteriores. No se puede subir de 30 º/s, así que se gana tiempo empezando antes.
- `VENTANA_NITIDEZ = 0.2`: en marcha se analiza la foto más nítida de los últimos 0,2 s.
- `PITCH_RIVAL_ALTO = 10`: la torreta busca inclinada al rival que está en una plataforma.
- `RIVALES`: dónde está cada rival en el plano. La demo los busca con la cámara, pero en los ataques en marcha usa su posición y velocidad para **prever** cómo se moverán en la imagen. El rival 2 tiene `hasta` y `velocidad` porque se mueve.
- `PLANO`: las tres partes del circuito.
  - **P1:** parada en (2,85; 0). Barre los yaws `[90, -90, 60, -60, 120, -120]` y espera 2 objetivos. Tiene:
    - `umbral_zona`: hacia la izquierda (de −150º a −30º) basta 0,7, para el camuflado;
    - `distancia_max=2.0`: no cuentan robots a más de 2 m, como el del fondo.
  - **R1, rotonda:** cuatro movimientos relativos. El tercero, `x=-1.44` con `atacar=-90` y `rival='rival 2'`, retrocede atacando a la izquierda. `barrido=[]` porque no barre al acabar.
  - **R2, recta final:**
    - `x=2.88`;
    - `y=-0.7`;
    - `x=2.3` con `atacar=180` y `pitch=10`: avanza disparando hacia atrás y hacia arriba al rival 3.
- `PARADAS = paradas_desde_plano(...)`: convierte el plano en la lista que recorre la demo.

### Bloque de velocidades
- `VELOCIDAD_XY = 0.5` y `VELOCIDAD_Z = 30`: los máximos del enunciado. Se pueden bajar, nunca subir; `demo_utils.limitar` lo garantiza.
- `AVANCE_CON_ODOMETRIA = True`. `chassis.move` iba a unos 0,06 m/s porque el SDK no convierte la velocidad a m/s reales. `drive_speed` sí lo hace.
- `CORREGIR_RUMBO = True`: mantener las rectas con la IMU (ver demo_utils).

### Bloque «Extras»
Audios (motor de F1, ráfaga del SCAR, «enemy spotted», Super Estrella), sonidos del SDK, luces de fiesta y umbrales de batería: con menos del 20 % avisa y con menos del 10 % no arranca.

---

## 2. `recorrido.py`: del plano a los movimientos

Convención del plano: origen en la salida, x hacia delante, y hacia la derecha. Los rumbos crecen en el sentido de las agujas del reloj, como el yaw de la torreta.

| Función | Qué hace y por qué |
|---|---|
| `movimiento(m)` | Un movimiento puede ser una tupla `(x, y, z)` o un dict con opciones (`velocidad`, `atacar`, `pitch`, `rival`). Devuelve siempre `(x, y, z, opciones)` para tratarlos igual. |
| `aplicar(punto, rumbo, x, y, z)` | Dónde queda el robot tras un movimiento relativo. Gira el vector (x adelante, y derecha) con el rumbo actual y lo suma al punto. Así la demo sabe en todo momento dónde está en el plano. |
| `rival_relativo(rival, punto, rumbo)` | Pasa la posición y la velocidad de un rival del plano a ejes del chasis. Da el yaw al que queda, la distancia y su velocidad (adelante, derecha). Con eso se prevé su movimiento en la imagen. |
| `tramo`, `girar_hacia`, `barrido_hacia` | Calculan giros y avances para ir a un punto, y los ángulos de barrido hacia los rivales (±30º por si se ha movido). Sirven para paradas descritas con `punto`/`rivales`; R1 y R2 usan `movimientos` directos. |
| `paradas_desde_plano(...)` | Recorre el plano acumulando posición y rumbo. Para cada parada devuelve movimientos, barrido, pitch, objetivos, punto y rumbo. Copia también `umbral_zona` y `distancia_max`, que son de la parada. |
| `describir` / `__main__` | `python recorrido.py` imprime lo calculado, para revisarlo antes de ir al robot. |

---

## 3. `demo_utils.py`: las piezas que usan la demo y el mando

### Conexión y modelo
- `connect(...)`: conecta con el robot por wifi directo o por la red (networking).
- `cargar_modelo` crea el Faster R-CNN y carga los pesos.
- `detectar(model, image)` aplica el modelo a una imagen ya capturada y devuelve cajas, confianzas y milisegundos. Está separado de la captura para poder tener la cámara abierta todo el recorrido.
- `calentar` hace una primera inferencia en vacío, porque la primera siempre es mucho más lenta.

### De píxeles a grados
- `auto_aim(image, box)`: cuántos grados hay que girar para centrar la caja.
  - Toma la distancia horizontal del centro de la caja al centro de la imagen.
  - Usa un modelo de cámara con focal `ancho / (2·tan 60º)`.
  - La fórmula es `ángulo = atan(desvío / focal)`, escalado por 90/120 porque el campo de visión medido es de unos 90º.
- `auto_pitch(image, box, altura)`: lo mismo en vertical. `altura` elige el punto de la caja al que se apunta (0 arriba, 0,5 centro).
- `tamano_angular`: ancho y alto de la caja en grados. Se usa para la tolerancia: un robot cercano, más grande, admite más error.
- `distancia_estimada`: `distancia = ALTURA_ROBOT / (2·tan(alto_angular/2))`. Si un robot mide 0,35 m y su caja ocupa X grados, está a esa distancia. Es aproximada, pero basta para separar 1,3 m de 2,6 m.

### Límites y colores
- `VEL_XY_MAX = 0.5`, `VEL_Z_MAX = 30` y `VEL_GIMBAL_MAX = 30`.
- `limitar(valor, máximo)` recorta cualquier velocidad antes de mandarla al robot.
- `COLORES_LED`: el color de cada fase.

### `Camara`
- **Problema:** el SDK deja los fotogramas en una cola de 64. Si nadie la vacía mientras se analiza una imagen, se llena, el decodificador se bloquea y llegan imágenes viejas o con franjas.
- **Solución:** un hilo propio vacía la cola sin parar y guarda el último fotograma, cuándo llegó y los de los últimos 0,4 s.
- `capturar(espera)` espera un rato y devuelve un fotograma llegado *después* de la espera, es decir, con la torreta ya quieta.
- `capturar_nitida(ventana)`: de los fotogramas de los últimos 0,2 s, el más nítido. `nitidez` es la varianza del laplaciano: más bordes definidos, más nítida. Devuelve también cuándo llegó, para saber hacia dónde miraba la torreta en ese momento.

### Elegir detecciones
- `seleccionar(prediction, umbral)`: las cajas que pasan el umbral, de mayor a menor confianza.
- `mas_centrada`: la más cercana al centro, es decir, la que menos hay que girar.
- `es_nuevo`: True si no hay otro ya atacado a menos de la tolerancia.
- `velocidad_angular(yaw, distancia, v_rel)`: a cuántos º/s se desplaza un robot en la imagen si se mueve a `v_rel` respecto a nosotros. Es el producto vectorial posición × velocidad entre la distancia al cuadrado. Por ejemplo, el rival 2 a 1,2 m, que se queda atrás a 0,05 m/s, se desplaza unos 2,4 º/s.

### `Registro`: las evidencias
- Cada imagen analizada se guarda dos veces: la original, en `originales/`, y otra con las cajas dibujadas. Además se escribe una fila en `registro.csv` con parada, fase, ángulos, confianzas, cajas, objetivo, distancia, disparos y nitidez.
- Los JPEG se escriben en otro hilo para no frenar la demo.
- Al cerrar se escribe `resumen.json`.
- De aquí salen las fotos que hemos usado para diagnosticar las sillas y el robot del fondo.

### Robustez del SDK
- `ejecutar_accion` lanza una acción y espera como mucho N segundos. `wait_for_completed()` sin límite espera para siempre si el robot no responde; así se convierte en un error que para la demo de forma segura.
- `liberar_cerrojo_sdk` corrige un fallo del SDK: tras rechazar una acción no suelta su cerrojo y el robot deja de responder.

### Avanzar recto: odometría + IMU
- `Odometria` se suscribe a `chassis.sub_position`: cuánto ha avanzado el chasis según las ruedas.
- **Bloque de rumbo (11/11).** Las ruedas decían «recto», pero el chasis se giraba un poco y acababa desviado. La IMU (`chassis.sub_attitude`) mide el giro real, sin depender de las ruedas.
  - `Actitud` lee el yaw de la IMU. Espera a la segunda lectura, porque la primera puede ser vieja.
  - `medir_signo_rumbo` hace un giro de prueba de 0,3 s a 20 º/s y mira hacia dónde cambia la IMU. El sentido de la corrección se mide, no se supone: la primera versión lo supuso, el robot se fue a la derecha y hubo que cambiarlo. Si la IMU no nota el giro, signo 0 y no se corrige.
  - `CorrectorRumbo.giro()` calcula `z = signo · 1,5 · desvío`, como mucho 15 º/s. Si el desvío pasa de 15º, algo va mal y deja de corregir para no empujar más.
  - `enderezar`: antes de cada avance, si el robot se ha torcido más de 1,5º, gira parado hasta volver.
  - **Deriva en las paradas:** con el robot parado, la IMU marcó 8º en 60 s sin moverse. Por eso, si han pasado más de 3 s quieto (`PAUSA_DERIVA`), lo que ha cambiado la IMU se toma como deriva y se mueve la referencia en lugar de «corregir» un giro que no existió. Esto quitó el giro a la izquierda en las paradas.
  - `reiniciar_rumbo`: tras un giro buscado del chasis (z), el rumbo nuevo pasa a ser el recto.
- `avanzar(x, y, velocidad)` prepara la IMU, ajusta la referencia, calibra el signo una vez y llama a `_avanzar`.
- `_avanzar` es el bucle de control, cada 0,05 s:
  1. lee la odometría y calcula cuánto falta a lo largo de la dirección pedida;
  2. si falta 1 cm o menos, termina;
  3. **rampa de frenada:** `v = min(velocidad, max(0,08; 3·falta))`, que a 0,5 m/s empieza a frenar a 17 cm;
  4. corrige la **deriva lateral** respecto a la línea recta, con ganancia 1,5;
  5. corrige el **rumbo** con la IMU (`z`);
  6. manda `drive_speed(..., timeout=0.5)`. Si el programa se cuelga, el robot se para solo en 0,5 s.
- `mover_chasis` usa `avanzar` para los avances sin giro y `chassis.move` para los giros.

### `Senales`: LED y sonido
- `estado(nombre, parpadeo)` pone el color de la fase.
- `sonido` reproduce un sonido del SDK y `audio` un WAV propio.
- El SDK solo admite un sonido a la vez: si hay otro sonando, el nuevo se omite (`ocupado`) en lugar de bloquear.
- Un fallo de LED o sonido nunca detiene la demo.

---

## 4. `demo.py`: el director

### `argumentos`
Opciones de prueba:
- `--sin-disparar`, `--sin-mover` y `--sin-rumbo`;
- `--paradas P1` para hacer solo una parada;
- `--simulacion`, sin robot;
- `--aviso-rival IP`, para avisar al portátil del rival 2.

### `robots(image, prediction, umbral)` (11/11)
Es `seleccionar` sin las cajas más altas que `ALTO_MAX_ROBOT`. Todas las búsquedas de la demo pasan por aquí, así que ninguna silla cercana puede llegar a ser un objetivo.

### Clase `Torreta`
Guarda el ángulo de la torreta respecto al chasis.
- `ir(yaw, pitch)` gira hasta un ángulo con `gimbal.move`. Los giros grandes se dividen en tramos de 45º, porque el SDK solo documenta ±55º por orden. Se usa en los barridos.
- `velocidad(yaw_speed, pitch_speed)` gira a velocidad constante con `gimbal.drive_speed`; sirve para seguir a un rival que se mueve.
  - Respeta los topes: ±240º de yaw y −20º/+30º de pitch.
  - No reenvía la misma orden más de una vez cada 0,2 s, para no saturar la conexión.
- `leer()` estima el ángulo sumando los giros y la velocidad mandada por el tiempo transcurrido, y guarda un historial.
- `angulo_en(t)`: **la pieza clave de la puntería.** La foto que llega es de hace `RETARDO_CAMARA` s. Para saber dónde está un robot hay que sumar su desvío en la imagen al ángulo que tenía la torreta *cuando se hizo la foto*, no al de ahora. `angulo_en` lo interpola en el historial.
- `centrar()` vuelve a 0º.

### `Demo.__init__`
Crea la torreta, las señales y el registro de evidencias, y deja a `None` la zona del camuflado y la distancia máxima. Esos dos valores solo valen durante su parada.

### `mover(x, y, z)`
Manda el movimiento con `mover_chasis`, imprime lo que midió la odometría y el rumbo, y actualiza `self.pose`.

### Parada con barrido (P1)
Las funciones van una dentro de otra:

```
atacar_parada(p)
 └─ barrer_por_pasos: para cada yaw del barrido
     ├─ torreta.ir(yaw)
     ├─ mirar(): espera 1 s, foto y detector
     └─ analizar_barrido: robots nuevos en esa foto
         └─ apuntar_y_disparar a cada uno
```

- **`atacar_parada(p)`:**
  - luz ámbar, sonido de escaneo y torreta centrada;
  - activa `self.zona` y `self.distancia_max` de la parada;
  - barre hasta haber atacado a los `objetivos` esperados (`completa()`);
  - al acabar, desactiva la zona y la distancia, centra la torreta y apunta un resumen de la parada.
- **`seleccionar_parada(image, prediction, yaw_c)`:** qué cuenta como robot en *esta* parada.
  - Siempre lo que pasa `UMBRAL` y no es demasiado alto (`robots`).
  - Si hay `distancia_max`, quita lo que está más lejos (el robot del fondo).
  - Si hay `umbral_zona`, acepta además lo que pasa el umbral bajo, pero solo si su ángulo está en el rango de la zona y su caja no pasa de media imagen.
- **`analizar_barrido`:**
  - para cada caja aceptada, calcula su ángulo absoluto: el yaw de la foto más `auto_aim`;
  - descarta las que están a menos de 15º de una ya revisada;
  - guarda la foto en el registro;
  - llama a `apuntar_y_disparar` para cada robot nuevo.
- **`apuntar_y_disparar` (puntería por pasos):**
  1. luz naranja y voz «enemy spotted»;
  2. gira hacia el ángulo estimado;
  3. hasta 4 veces: foto, robot más centrado (con los mismos filtros de la parada) y error `residuo`;
     - si ya está centrado (menos de 3º o del 30 % del ancho), sale del bucle;
     - si no, gira lo que falta. Solo se usan giros *relativos*, así que un error acumulado en el ángulo de la torreta no importa;
  4. si al confirmar no ve nada, o lo que ve es un robot ya atacado, **no dispara** y lo anota como `sin_confirmar`;
  5. luz roja parpadeando y `rafaga()`;
  6. si el blaster no confirma los 20 disparos, error (no se da por bueno un ataque incompleto);
  7. `celebrar()`: luz verde, sonido y cabeceo de 10º.

### Ataque en marcha (R1 y R2)

```
mover_atacando(...)
 ├─ hilo 1: avanzar()             el chasis se mueve con odometría + IMU
 └─ hilo 2: torreta.ir(yaw, pitch)
            disparar_en_marcha()  busca, sigue y dispara mientras se mueve
```

- **`preparar_torreta(movimientos)` (11/11):** si en la parada hay un ataque en marcha después de otros movimientos sin giros del chasis, lanza un hilo que va girando la torreta hacia ese ángulo mientras el chasis hace los tramos anteriores.
  - En R2 son 180º, que a 30 º/s tardan 6 s: se hacen durante la recta de 2,88 m y el lateral de 0,7 m.
  - En R1 gira a −90º durante los dos primeros tramos.
  - Antes del ataque, `ejecutar` espera a que este hilo acabe.
- **`mover_atacando(...)`:**
  - si el rival es móvil, lo avisa (`avisar_rival`);
  - arranca el chasis en otro hilo con `avanzar` a 0,1 m/s;
  - en este hilo pone la torreta en el ángulo de ataque y llama a `disparar_en_marcha`;
  - al acabar espera al chasis, comprueba errores y centra la torreta.
- **`avisar_rival`:** manda por UDP el aviso al portátil de Alejandro. Si no hay red o falta la IP, imprime «ARRANCAR RIVAL 2 AHORA» para arrancarlo a mano con Enter.
- **`disparar_en_marcha` (el bucle más complejo).** En cada vuelta:
  1. si el chasis acaba de pararse, el rival ya solo se mueve por sí mismo: a la velocidad estimada se le quita la parte que venía de nuestro movimiento;
  2. toma la foto más nítida de los últimos 0,2 s y el ángulo de la torreta en el instante de esa foto (`angulo_en`);
  3. detector y `robots(...)`:
     - **sin objetivo fijado**, toma el robot más centrado que pase 0,95;
     - **con objetivo**, calcula dónde *debería* estar (último ángulo + velocidad × tiempo) y se queda con la caja más cercana a esa previsión, si está a menos de `SALTO_MAX`; para no perderlo basta 0,8;
  4. **primera vez que lo ve:**
     - prevé su velocidad angular con la geometría: nuestra velocidad, la del rival y la distancia del plano (`velocidad_angular`);
     - suena la voz;
     - apunta a donde estará al acabar la voz;
     - deja la torreta girando a esa velocidad y lanza la ráfaga en otro hilo;
  5. **siguientes imágenes:**
     - actualiza la velocidad estimada, mitad la anterior y mitad la medida;
     - manda a la torreta `velocidad + ganancia · error`;
     - la ganancia se limita según lo que tarda cada imagen, para no oscilar;
     - corrige también el pitch, que importa en R2 porque el rival está en alto;
  6. si no lo ve en una imagen, la torreta sigue con su último movimiento;
  7. si el chasis llega al final sin haberlo visto, mira 3 imágenes más ya parado.

  Al acabar comprueba los 20 disparos y luz verde.

### Disparos
- `rafaga()`: si existe el audio de la ráfaga (`scar_rafaga.wav`), lo reproduce y llama a `disparar_al_ritmo`. Si no, dispara uno a uno con su sonido.
- `disparar_al_ritmo()`: cada disparo va en su instante exacto, `silencio inicial + i · 0,3 s` desde que empieza el audio. Así lo que tarda `fire()` no retrasa los siguientes y cada disparo coincide con un tiro del audio.

### Final
- `baile()`: suena Super Estrella. Un hilo cambia los LED 10 veces por segundo (`luces_fiesta`). Mientras suena la canción, la torreta va a (20º, 10º) y (−20º, −5º), y el chasis gira +20º, −40º, +20º, para acabar mirando igual.

### `ejecutar()`: el guion completo
1. Modo libre (torreta y chasis independientes).
2. Batería: con menos del 10 % no arranca.
3. Abre la cámara y centra la torreta.
4. Luz azul, cuenta atrás y audio del motor de F1.
5. Para cada parada de `PARADAS`:
   - `preparar_torreta` si hay un ataque en marcha después de otros movimientos;
   - para cada movimiento: si tiene `atacar`, busca los datos del rival en `RIVALES`, los pasa a ejes del chasis con `rival_relativo` y llama a `mover_atacando`; si no, `recorrer`, que llama a `mover`;
   - actualiza la posición en el plano con `aplicar`;
   - si la parada tiene barrido, `atacar_parada`.
6. Baile final.
7. **Siempre**, también con error o Ctrl+C, `cerrar()`: para el chasis, centra la torreta, cierra la cámara, apaga los LED y guarda `resumen.json`.

### `main()`
- Lee las opciones.
- Activa o no la corrección de rumbo.
- Deja hilos de CPU libres para el decodificador de vídeo del SDK.
- Carga y calienta el modelo, conecta y ejecuta.
- Ctrl+C o un error de la demo terminan de forma limpia.

---

## 5. `demo_gpu.py`: la misma demo con la GPU

- **Problema:** el SDK del robot solo funciona con Python 3.8, y el PyTorch de Python 3.8 no admite la RTX 5070. En CPU cada imagen tardaba unos 2,3 s.
- **Solución:** el detector corre en otro proceso, `mando/detector_gpu.py` con `.venv-gpu` (Python 3.11 y CUDA). Se le manda cada imagen en JPEG por `127.0.0.1:8767` y tarda unos 0,1 s.

Bloques:
- `DetectorGPU`:
  - si el puerto ya está ocupado, pregunta por `/info` qué modelo tiene ese detector y, si es el mismo, lo reutiliza (11/11: antes salía «puerto ocupado»);
  - si no, lo arranca y espera hasta 60 s a que cargue;
  - `detectar(image)` lo llama por HTTP.
- `cerrar_arbol`: en Windows, el `python.exe` del entorno es un lanzador que arranca el Python real como hijo. Hay que cerrar todo el árbol (`taskkill /T`); si no, el hijo quedaba vivo ocupando el puerto.
- `Detectar`: sustituye a `demo.detectar`. Usa la GPU y, si falla, esa imagen va en CPU. Tras 3 fallos seguidos, el resto de la demo va en CPU, sin pararla.
- `main`: crea el detector, cambia `demo.detectar` por el sustituto y llama a `demo.main`. Al acabar apunta en `resumen.json` cuántas imágenes fueron por GPU y cuántas por CPU.

## 6. `rival/rival_movil.py`: el rival 2

Lo lanza Alejandro en su portátil, conectado al robot rival.
- `esperar_salida`: espera el aviso UDP de nuestra demo o que se pulse Enter.
- `avanzar`: recta de 0,86 m a 0,05 m/s con `drive_speed` y odometría.
- **Seguridad:**
  - nunca pasa de 0,1 m/s;
  - cada orden caduca en 0,5 s;
  - Ctrl+C lo para;
  - en networking exige el número de serie del rival para no conectarse a nuestro robot por error.

---

# Parte 2. La interfaz del mando

## Cómo se reparte el trabajo

| Pieza | Hilo o proceso | Trabajo |
|---|---|---|
| `servidor.py` | bucle asíncrono (aiohttp) | página web, vídeo y WebSocket de control |
| `conductor.py` | hilo `Conductor` | **el único que habla con el SDK** |
| `deteccion.py` | hilo `Detector` | analiza la última imagen, sin cola |
| `detector_gpu.py` | proceso aparte (`.venv-gpu`) | inferencia en GPU, puerto 8766 |
| `web/*.js` | navegador | lee teclado y mando, dibuja la pantalla y manda órdenes |

Solo un hilo habla con el robot para que dos órdenes no se pisen en el SDK. El servidor y el detector solo dejan datos y el conductor decide.

## 7. `mando/servidor.py`

- `crear_app(conductor)` define las rutas:
  - `/` es la interfaz nueva y `/clasico` la anterior, de reserva;
  - `/salud` dice si el robot está listo y qué detector se usa;
  - `/video` emite **MJPEG**: cada 50 ms, si hay foto nueva, la reduce a 960×540, la comprime a JPEG y la envía como un fotograma más de un `multipart/x-mixed-replace`; el navegador lo muestra como vídeo en un `<img>`;
  - `/ws` es el **control**:
    - rechaza páginas de otro origen, para que otra web no pueda mover el robot;
    - **una sola sesión de control:** la última pestaña que se conecta se queda el control y la anterior se cierra con el código 4001. Antes devolvía error 409 y el robot no respondía en la pestaña que se usaba (11/11);
    - cada vez que cambia el propietario, el robot se para;
    - envía el estado 5 veces por segundo (`estado()`) y los eventos: disparo, emote, desarmado y avisos;
    - pasa cada mensaje del navegador a `conductor.recibir`; un mensaje mal formado para el robot;
    - al cerrar, solo para el robot si esta pestaña seguía siendo la propietaria;
  - `/audio/...` sirve los audios de los emotes.
- `main`:
  - arranca el detector GPU si puede (`proceso_detector.iniciar`);
  - crea el `Conductor` con la conexión al robot y el `Detector` con la imagen del conductor;
  - escucha solo en `127.0.0.1:8765`.

## 8. `mando/conductor.py`

Constantes:
- `CADUCIDAD = 0.3`: s sin órdenes del navegador antes de parar y desarmar;
- `EDAD_AUTO = 0.5` y `GIRO_AUTO = 2`: condiciones del disparo automático;
- `GIRO_CHASIS = 30`;
- `EDAD_APUNTAR`, `GANANCIA_APUNTAR` y `MIRA_MANUAL`: del asistente de puntería.

Funciones del módulo:
- `control(datos)`: valida la orden del navegador (mover, mirar, disparo, girar).
  - Recorta cada valor a [−1, 1].
  - **Normaliza la diagonal:** W+D no va más rápido que W sola.
- `configuracion(datos)`: valida los ajustes con límites. Por ejemplo, el umbral nunca baja de 0,95 y la velocidad nunca pasa de 0,5.
- `hacia_camara(mover, yaw)`: gira el vector de movimiento con el yaw de la torreta. Con «moverse hacia donde mira la cámara», W lleva el robot hacia donde apunta la torreta aunque esté girada.

Clase `Conductor`:
- **`recibir(datos)`**, desde el servidor, según el tipo de mensaje:
  - `control`: guarda la orden y la hora;
  - `parar`: para de inmediato;
  - `emote`: lo encola si los controles están activos;
  - `config` / `activar`: aplica los ajustes y los guarda en `config_mando.json`. `activar` además arma los controles. Cualquier cambio de ajustes para el robot y exige órdenes nuevas.
- **`parar()`:** emergencia activada, AUTO apagado, orden en reposo y cola de emotes vacía.
- **`velocidades(mover, mirar, girar, torreta)`:** convierte la orden en velocidades reales:
  - chasis con `drive_speed(timeout=0.5)`;
  - torreta con `Torreta.velocidad`;
  - todo limitado a 0,5 m/s y 30 º/s.
- **`blanco()`, para AUTO:** dispara solo si
  - hay una caja de 0,95 o más bajo la mira (`regla_auto`);
  - la detección tiene menos de 0,5 s;
  - la torreta no se ha movido más de 2º desde la foto (con `angulo_en`, como la demo).
- **`apuntar()`, el asistente (11/11):**
  - toma la detección más centrada que pasa el umbral y no es demasiado alta;
  - calcula su ángulo absoluto con el ángulo que tenía la torreta al hacer la foto;
  - devuelve la velocidad de la torreta (2 º/s por grado de error) y si ya está centrada.
- **`disparar()`:** dispara una vez. Si el robot no lo confirma, avisa pero no corta la sesión. Con AUTO guarda la imagen en `evidencias/mando/`.
- **`paso()`, el corazón, cada 25 ms:**
  1. si no llegan órdenes en 0,3 s, desarma (pestaña cerrada, wifi caído o navegador colgado);
  2. si hay un emote en cola y ningún baile en curso, lo empieza;
  3. con baile en curso, solo ejecuta el baile (`paso_baile`);
  4. si el asistente está activo y no se toca el joystick derecho, la torreta la mueve `apuntar()`; si se toca, manda el usuario;
  5. dispara si se pulsa disparo, o si AUTO está activo y hay blanco, respetando el intervalo entre disparos.
- **`empezar_baile` y `paso_baile`:**
  - el baile es una función del tiempo (`coreografias.muestra`);
  - en cada paso se pide la consigna del instante y se manda: velocidad del chasis, ángulo objetivo de la torreta (seguido a como mucho 30 º/s) y color de los LED;
  - así se puede cortar en cualquier momento, porque no hay esperas bloqueantes.
- **`run()`:**
  - conecta, comprueba la batería y centra la torreta;
  - comprueba si la lectura del ángulo del gimbal es fiable;
  - sube los audios de los emotes al robot y abre la cámara;
  - luego, cada 25 ms: `paso()`, coger la última foto para el vídeo y el detector, y leer los ángulos;
  - al salir, siempre: para, centra, apaga y cierra.

## 9. `mando/deteccion.py`, `detector_gpu.py` y `proceso_detector.py`

- **`es_robot` (11/11):** descarta cajas más altas que media imagen, igual que la demo.
- **`regla_auto`:** devuelve la caja que contiene el centro de la imagen, la mira. Antes la encoge un 20 %, para no disparar si la mira está solo en el borde de la caja.
- **`Detector`, hilo:**
  - coge la última foto y, si es nueva, la analiza;
  - prefiere la GPU; si falla, pasa a CPU y vuelve a probar la GPU a los 5 s;
  - publica el resultado con la imagen y su instante.
  - Analiza siempre la última foto, nunca acumula una cola, para no ir con retraso.
- **`detector_gpu.py`:** servidor HTTP con el modelo cargado en la GPU.
  - `POST /detectar` recibe un JPEG y devuelve cajas y confianzas.
  - `GET /info` dice qué modelo tiene; así la demo lo reutiliza.
- **`proceso_detector.py`:** arranca el detector GPU si hay CUDA y lo cierra con todo su árbol de procesos.

## 10. `mando/coreografias.py`: los gestos

Cada baile es una **función del tiempo** que devuelve, para cada instante: velocidad del chasis (`vx`, `vy`, `z`), ángulo de la torreta (`yaw`, `pitch`) y color de los LED.

| Gesto | Duración | Lógica |
|---|---|---|
| **Moonwalk** (Billie Jean, 117 BPM) | 48 tiempos (24,6 s) | Por compases: baja la torreta, pasos hacia atrás al ritmo con un cabeceo en triángulo, gira la torreta 180º con luces blancas parpadeando, pasos hacia el otro lado, vuelve la torreta y levanta el cañón al final. |
| **Waka Waka** (127 BPM) | 11,7 s | Contoneo lateral (`vy` en seno) con la torreta acompañando. Bandera de España: torreta y chasis alternan rojo y amarillo en cada tiempo, cada uno en el color contrario. Los 3 últimos segundos, giro de ida y vuelta. |
| **Super Estrella** | 27,1 s | Los mismos gestos que el baile de la demo, en 5 ciclos que acaban en el rumbo inicial: torreta (20º, 10º) → (−20º, −5º) y chasis +30/−30/+30 º/s. Luces de fiesta. |
| **Risa** | 3,15 s | La torreta tiembla 1,5º a 3 Hz con un giro corto del chasis, luz amarilla parpadeando y, al final, la torreta baja y vuelve. |

`validar(nombre)` simula cada baile antes de usarlo: integra el movimiento y comprueba que nunca pasa de 0,5 m/s ni 30 º/s, que cabe en 1 × 1 m y que **vuelve al punto de partida**. Si no, no se usa.

`audio_robot.py` sube los audios de los emotes al robot al conectar y los reproduce o para en el altavoz del robot.

## 11. La página web (`mando/web/`)

### `mando.js`: la entrada
- **Teclas por defecto:** WASD, flechas, Z/X, Q/E/F/C para los emotes, espacio o Esc para parar y Tab para los ajustes.
- **Botones del DualShock**, con el mapeo estándar: R2 = 7, L1/R1 = 4/5, □ △ ○ ✕ = 2/3/1/0, SHARE = 8 y OPTIONS = 9.
- `curva(valor, zona)` aplica a los joysticks una zona muerta y una curva cuadrática. Los movimientos pequeños no hacen nada y los medianos son finos.
- `combinar(teclado, mando)`: por cada eje gana la entrada mayor, así teclado y mando funcionan a la vez.
- `Entrada.tecla`:
  - Esc siempre para, aunque los controles estén desactivados;
  - los emotes se lanzan al pulsar, no al mantener;
  - se ignoran las teclas escritas en un campo de texto.
- `Entrada.leerMando`, en cada fotograma de pantalla:
  - lee el mando con la Gamepad API;
  - detecta pulsaciones nuevas (emotes, parar, ajustes) comparando con el fotograma anterior;
  - calcula los joysticks;
  - también sirve para reasignar botones en Ajustes.
- `leer()` devuelve la orden combinada: mover, mirar, disparo y girar.

### `app.js`: la pantalla y la conexión
- `conectar()` abre el WebSocket.
  - Si se pierde la conexión, reintenta cada 2 s.
  - Con el código 4001 (otra pestaña tiene el control) **no** reintenta, para no pelearse con la otra.
- Cada 50 ms, si los controles están activos y la pestaña está delante, manda `{tipo: "control", ...entrada.leer()}`. Este envío continuo hace de **señal de vida**: si deja de llegar, el conductor para el robot en 0,3 s.
- **Pausas por seguridad:** ocultar la pestaña, salir de la ventana, abrir ajustes o desconectar el mando pausan los controles, y hay que volver a pulsar «Activar controles».
- `recibir(estado)` actualiza la batería, los ángulos, la velocidad, los disparos, las cajas del detector y los avisos.
- `recargarVideo()`: si el vídeo falla porque el servidor aún no estaba listo, lo vuelve a pedir cada 2 s (11/11: antes se quedaba en negro).
- Ajustes: controles, disparo (AUTO y asistente), detector, telemetría y reasignación de teclas.

### `escena3d.js`: los dibujos en 3D
Usa Three.js, copiado en `web/vendor/` porque en la wifi del robot no hay internet.
- El mando y el teclado se dibujan en 3D con lo que se pulsa en cada momento.
- Un robot en miniatura muestra el yaw y el pitch reales de la torreta, su campo de visión y los colores de los LED.
- Sin WebGL, la página funciona igual, sin los dibujos.

---

# Seguridad: cómo se evita que el robot se descontrole

| Riesgo | Protección |
|---|---|
| El programa se cuelga | Toda orden `drive_speed` caduca en 0,5 s. |
| Se cierra la pestaña o se cae el wifi | Sin órdenes en 0,3 s, el conductor para y desarma. |
| Velocidades mayores de las permitidas | `limitar` en todas las órdenes; los bailes se validan antes. |
| Error o Ctrl+C en la demo | `cerrar()` en `finally`: para, centra y apaga siempre. |
| Disparar a lo que no es un robot | Umbral 0,95, filtro de cajas altas, distancia máxima en P1 y confirmación antes de la ráfaga. |
| Dos pestañas a la vez | Una sola sesión de control; al cambiar de propietario, el robot se para. |
| Batería baja | Con menos del 10 % no arranca; con menos del 20 % avisa. |
