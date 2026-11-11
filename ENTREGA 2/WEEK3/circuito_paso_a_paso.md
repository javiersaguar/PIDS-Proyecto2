# Demo del Bloque 3, paso a paso

Qué hace el robot en cada momento de la demo: movimientos, tiempos, torreta, disparos,
audios y luces. Estado del 08/11/2026.

- **P1** está medido en el laboratorio.
- **R1 y R2** son supuestos hasta montar el circuito.
- **El rival 2 se mueve** en paralelo a nuestro robot durante la rotonda. Lo maneja Alejandro
  desde su portátil con el kit de [`rival/`](rival/README.md).
- **El contraataque del final** depende de la respuesta del profesor al correo sobre la
  colaboración de otro grupo.

La configuración está en [`circuito.py`](circuito.py) y el recorrido dibujado, en
[`docs/informes/figuras/circuito_demo.png`](../../docs/informes/figuras/circuito_demo.png).

## Resumen

| # | Tramo | Qué pasa | Duración aprox. |
|---|---|---|---|
| 0 | Salida | Comprobaciones, cuenta atrás y sonido de Fórmula 1 | 5 s |
| 1 | P1 | Recta de 2,85 m con el sonido de F1 | 6,4 s |
| 2 | P1 | Parada: rival 1 a la derecha y robot camuflado a la izquierda | 45 s |
| 3 | R1 | Rotonda: adelante, izquierda, atrás disparando al rival 2, que se mueve en paralelo, derecha | 28 s |
| 4 | R2 | Recta final: adelante, izquierda y adelante disparando hacia atrás al rival 3, en alto | 37 s |
| 5 | Final | Super Estrella y baile | 27 s |
| | | **Total** | **unos 2 min 26 s** |

Los tiempos de la parada dependen de cuántas correcciones de puntería haga el robot.

**Plano.** El origen está en la salida de nuestro robot (esquina de arriba a la izquierda).
x va hacia delante, como mira el robot al salir. y es positiva hacia la derecha del robot y
negativa hacia la izquierda.

## Dónde va cada robot

| Robot | Posición (x; y) en m | Respecto a nuestro robot | Notas |
|---|---|---|---|
| Nuestro robot | (0; 0) | — | Mirando hacia +x |
| Rival 1 | (2,85; 1,2) | 1,2 m a la derecha de P1 | Quieto |
| Robot camuflado | (2,85; −1,2) | 1,2 m a la izquierda de P1 | Detective impreso en A3, de pie |
| Rival 2 | De (4,86; −2,2) a (4,0; −2,2) | 1,2 m a la izquierda del retroceso de R1 | Se mueve 0,86 m a 0,05 m/s (17 s), en el mismo sentido que nuestro robot |
| Rival 3 | (5,73; −0,7), en alto | De 0,75 a 3,05 m por detrás en el último tramo | Plataforma de 20–40 cm de alto y 40 × 40 cm como mucho |

Todas las posiciones dejan al menos 0,6 m entre el centro de cada rival y el camino de
nuestro robot. Están en `RIVALES` de [`circuito.py`](circuito.py) y en la figura.

## Reglas que se cumplen siempre

- **Velocidades máximas.** Chasis a 0,5 m/s y 30 º/s, y torreta a 30 º/s, como pide el
  enunciado. Un giro de torreta de 90º tarda 3 s y uno de 180º, 6 s.
- **Detección y puntería.** Se dispara con una confianza de 0,95 o más. Cada imagen tarda
  unos 2 s en analizarse, porque el portátil no usa la GPU. Antes de cada foto parada, el
  robot espera 1 s para que la imagen salga quieta.
- **Disparos.** Cada ráfaga son 20 disparos de infrarrojos, uno cada 0,3 s. El enunciado pide
  12 impactos; los 8 de más son margen.
- **Luces.** Cada fase tiene su color:

  | Fase | Color |
  |---|---|
  | En marcha | azul |
  | Buscando | ámbar |
  | Apuntando | naranja |
  | Disparando | rojo parpadeando |
  | Rival eliminado | verde |
  | No ha encontrado nada | morado |
  | Final | verde agua |

- **Seguridad.** Ctrl+C, un error o el final paran el chasis, centran la torreta y apagan las
  luces. Si el programa se cuelga, el chasis se para solo en 0,5 s. Con menos del 10 % de
  batería la demo no arranca, y con menos del 20 % avisa.

## Audios

| Audio | Duración | Cuándo suena |
|---|---|---|
| Cuenta atrás (sonido del SDK) | unos 3 s | Al empezar |
| Fórmula 1 (`f1_recta.wav`) | 6,4 s | Durante la primera recta; el coche pasa a mitad y se apaga al frenar |
| Escaneo (sonido del SDK) | corto | Al empezar a buscar en una parada |
| «Enemy spotted» (`enemy_spotted.wav`) | 1,4 s | Al detectar cada rival, antes de la ráfaga |
| Ráfaga de SCAR (`scar_rafaga.wav`) | 6,2 s | Con los 20 disparos, cada uno en su instante del audio |
| Ataque completado (sonido del SDK) | corto | Tras eliminar a un rival en una parada |
| Super Estrella (`superestrella.wav`) | 27,2 s | Baile final |

Los audios propios están en `audio/propios/` y no se suben a GitHub. Si falta alguno, suena el
del SDK. Se preparan con `audio/preparar_disparo.py`, `audio/preparar_motor.py` y
`audio/preparar_voz.py`.

## 0. Salida (unos 5 s)

1. Lee la batería.
2. Abre la cámara (1 s) y centra la torreta.
3. Luz azul parpadeando y cuenta atrás.
4. Al acabar la cuenta atrás, empieza a sonar el coche de Fórmula 1 y el robot arranca.

## 1. Recta de salida, P1 (6,4 s, medido)

- **Movimiento:** 2,85 m hacia delante a 0,5 m/s, de (0; 0) a (2,85; 0). Medido el 05/11:
  unos 6 s.
- **Frenada:** frena en los últimos 17 cm y se para a 1 cm del punto.
- **Audio:** el sonido de F1 dura lo mismo que la recta. El coche "pasa" a los 2,5–3 s, a toda
  velocidad, y se apaga cuando el robot frena.
- **Luz:** azul.

## 2. Parada P1: rival 1 y robot camuflado (unos 45 s)

1. **Empieza a buscar.** Luz ámbar y sonido de escaneo.
2. **Mira a la derecha.** La torreta gira 90º (3 s), espera 1 s y analiza una imagen (2 s).
3. **Rival 1.** Al verlo:
   - suena «enemy spotted» y la luz se pone naranja;
   - la torreta gira hacia el rival y corrige la puntería por pasos: foto, giro de lo que
     falta y otra foto. Hace hasta 4 correcciones, de unos 3 s cada una, y para cuando el
     error es menor de 3º o del 30 % del ancho del robot;
   - luz roja parpadeando, suena la ráfaga de SCAR y dispara 20 veces en 6,2 s;
   - luz verde, sonido de ataque completado y la torreta cabecea 10º arriba y abajo.
4. **Mira a la izquierda.** La torreta gira hasta −90º (180º, 6 s), espera 1 s y analiza una
   imagen.
5. **Robot camuflado** (el detective impreso). Hace lo mismo que con el rival 1: voz,
   puntería, 20 disparos y celebración. El detector lo ve con un 99 % de confianza aunque vaya
   disfrazado.
6. **Fin de la parada.** Con los dos eliminados deja de buscar y centra la torreta (3 s).
   - Si no ve a alguno, prueba también a ±60º y ±120º.
   - Si no encuentra nada, la luz se pone morada y sigue el recorrido.

**Montaje:**
- Rival 1 a la derecha de P1, a 1–1,5 m (hacia (2,85; 1,2)).
- Detective impreso en A3 (`docs/informes/figuras/senuelo/detective_imprimir.jpg`) a la
  izquierda, a 1–1,5 m (hacia (2,85; −1,2)), de pie y bien iluminado.

## 3. Rotonda R1 (unos 28 s)

Desde aquí, después del túnel, las medidas a lo largo (x) son un 15 % más largas que las
medidas el 05/11, porque el final quedaba sin espacio (pruebas del 11/11). Las de lo ancho
(y) no cambian.

| Paso | Movimiento | Velocidad | Tiempo | Torreta y disparos |
|---|---|---|---|---|
| 3.1 | 2,19 m adelante, hasta (5,04; 0) | 0,4 m/s | 5,9 s | Gira a la izquierda (−90º) |
| 3.2 | 1 m a la izquierda, hasta (5,04; −1) | 0,5 m/s | 2,5 s | Ya mira a la izquierda |
| 3.3 | 1,44 m atrás, hasta (3,6; −1) | 0,1 m/s | 14,4 s | Gira a la izquierda (−90º) y ataca al rival 2 sin parar |
| 3.4 | Centra la torreta, parado | — | 3 s | Vuelve al centro |
| 3.5 | 1 m a la derecha, hasta (3,6; 0) | 0,5 m/s | 2,5 s | Centrada |

**Ataque en marcha a un rival que también se mueve (3.3).**

Al empezar el retroceso, la demo avisa al portátil de Alejandro y el rival 2 arranca. Va en
paralelo a nuestro robot, 1,2 m a su izquierda y en el mismo sentido, pero más despacio:
0,05 m/s frente a 0,1. A la vez:
1. luz ámbar y la torreta gira 90º a la izquierda (3 s, con el chasis ya en marcha);
2. analiza una imagen cada 2 s. De los fotogramas de los últimos 0,2 s elige el más nítido,
   porque con el robot en marcha algunos salen movidos y el detector pierde confianza;
3. al ver al rival 2:
   - calcula cuánto se va a desplazar en la imagen. Va 0,05 m/s más lento que nuestro robot y
     a 1,2 m, así que se queda atrás unos 2,4 º/s;
   - suena «enemy spotted», la torreta gira a donde estará el rival al acabar la voz y empieza
     a girar a esa velocidad;
   - empieza la ráfaga: luz roja, SCAR y 20 disparos en 6,2 s;
4. mientras dispara, corrige con cada imagen la velocidad y el ángulo de la torreta;
5. cuando nuestro robot se para, el rival sigue avanzando y cambia de sentido en la imagen:
   la torreta lo compensa en el momento, sin esperar a la siguiente imagen;
6. si al acabar el retroceso aún no lo ha visto, mira 3 imágenes más ya parado.

Va a 0,1 m/s porque necesita unos 12 s: 3 s de giro, 2–4 s para verlo, 1,4 s de voz y 6,2 s
de ráfaga. La ráfaga puede acabar 1–2 s después de que se pare nuestro robot. El rival se
mueve durante 17 s, así que sigue en marcha hasta el último disparo.

**Montaje y arranque del rival 2:**
- Rival 2 en (4,86; −2,2), mirando hacia la salida (hacia −x), para que avance en paralelo al
  retroceso de nuestro robot.
- Alejandro lanza `python rival/rival_movil.py` antes de empezar la demo. El rival espera
  quieto.
- Nuestro portátil lanza la demo con `--aviso-rival <IP del portátil de Alejandro>`. Al
  empezar el paso 3.3, la demo le avisa por la red del laboratorio y el rival arranca solo.
- Si el aviso no llega, la consola de la demo muestra «ARRANCAR RIVAL 2 AHORA» y Alejandro
  pulsa Enter. La señal visual es que nuestro robot empieza a retroceder y su torreta gira a
  la izquierda.
- Instrucciones de conexión en [`rival/README.md`](rival/README.md).

## 4. Recta final R2 (unos 37 s)

| Paso | Movimiento | Velocidad | Tiempo | Torreta y disparos |
|---|---|---|---|---|
| 4.1 | 2,88 m adelante, hasta (6,48; 0) | 0,5 m/s | 6,3 s | Empieza a girar hacia atrás (180º, inclinada 10º) |
| 4.2 | 0,7 m a la izquierda, hasta (6,48; −0,7) | 0,5 m/s | 1,9 s | Acaba de girar: ya mira hacia atrás |
| 4.3 | 2,3 m adelante, hasta (8,78; −0,7) | 0,1 m/s | 23 s | Gira 180º, inclinada 10º hacia arriba, y ataca al rival 3, en alto, sin parar |
| 4.4 | Centra la torreta, parado | — | 6 s | Vuelve al centro desde 180º |

**Ataque hacia atrás y hacia arriba (4.3).** Es como el de la rotonda, pero con la torreta
mirando hacia atrás (180º) e inclinada 10º. Girar 180º lleva 6 s a 30 º/s, que el enunciado
no deja subir: desde el 11/11 la torreta gira durante 4.1 y 4.2 (`GIRAR_TORRETA_ANTES`), así
que el ataque empieza ya mirando al rival 3. En la rotonda pasa lo mismo con los −90º. Al ver al rival 3, corrige también
la inclinación para apuntar al centro del robot y la sigue ajustando mientras se aleja.

Como referencia, un robot 30 cm más alto que el cañón queda a unos 17º a 1 m y a unos 9º a
2 m. La torreta sube como mucho 30º.

**Montaje:**
- Rival 3 sobre una plataforma de 20–40 cm de alto, en (5,73; −0,7): 0,75 m por detrás del
  punto donde empieza 4.3 y a 0,69 m del tramo 3.2 de la rotonda (x = 5,04). Antes del
  15 % estaba en (5,35; −0,7), y antes aún en (5,0; −0,7), donde nuestro robot chocaba con él.
- La plataforma no debe medir más de 40 × 40 cm, para dejar paso a los tramos 3.2 y 4.2.
- El robot se aleja de él de 0,75 a 3,05 m. Cuando lo ve por primera vez, tras girar la
  torreta, ya está a unos 1,3–1,5 m.

## 5. Final: Super Estrella y baile (27 s)

1. Suena Super Estrella.
2. Las luces cambian de color 10 veces por segundo.
3. Mientras dura la canción, el robot repite este baile:
   - la torreta va a la derecha y arriba, y luego a la izquierda y abajo;
   - el chasis gira 20º a la izquierda, 40º a la derecha y 20º a la izquierda.
4. Al acabar la canción, la torreta vuelve al centro y la luz se pone verde agua.
5. La demo guarda las evidencias: cada imagen analizada, el registro y el resumen.

## 6. Pendiente de la respuesta del profesor

En el correo a Daniel Fuertes se preguntó si otro grupo puede colaborar con su robot. El
rival que se mueve (6.2) ya está programado en la rotonda, con un segundo robot que maneja
Alejandro. El contraataque (6.1) sigue sin programar.

### 6.1. Contraataque a un rival en modo solo disparo

**Qué se vería.** Un robot de otro grupo, quieto, dispara a nuestro robot. Al recibir el
impacto, nuestro robot gira la torreta hacia ese lado, lo detecta y le responde con la ráfaga.

**Dónde.** Al final de R2, antes del baile, en (8,0; −0,7):
1. El robot se queda parado hasta 20 s esperando un impacto, con luz amarilla.
2. El rival del otro grupo está a 1,5–2 m, a un lado o detrás.
3. Si no le dan en 20 s, pasa al baile.

**Cómo funciona.**
1. El SDK avisa de cada impacto con el número de la placa de armadura y el tipo (agua o
   infrarrojo).
2. La placa da la dirección del atacante:

   | Placa | Lado | Ángulo de la torreta |
   |---|---|---|
   | 1 | Chasis atrás | 180º |
   | 2 | Chasis delante | 0º |
   | 3 | Chasis izquierda | −90º |
   | 4 | Chasis derecha | +90º |
   | 5 | Torreta izquierda | ángulo actual −90º |
   | 6 | Torreta derecha | ángulo actual +90º |

3. La torreta gira a ese ángulo y busca al rival con un barrido corto de ±30º.
4. Al verlo: voz, puntería y ráfaga, igual que en P1.

**Tiempo añadido.** Hasta 20 s de espera y unos 15 s de respuesta.

**Por comprobar en el laboratorio:**
- si un impacto de infrarrojos llega con su número de placa, o solo con el evento general de
  infrarrojos, que no dice el lado;
- la sensibilidad de las placas.

### 6.2. Rival que se mueve despacio (hecho, en la rotonda)

Se ha hecho en R1, con el rival 2, en lugar de en P1 (apartado 3):
- no usa el seguimiento de la PR #36, que sigue desactivado;
- amplía el ataque en marcha, que ya seguía al rival mientras disparaba, con lo que hace falta
  para un blanco móvil:
  - la imagen más nítida de los últimos 0,2 s;
  - la velocidad prevista del rival desde la primera imagen;
  - la compensación cuando se para nuestro robot.

**Límites.**
- Con unos 2 s por imagen, un rival que cambia de ángulo a 2–5 º/s se desplaza de 4 a 10º
  entre imagen e imagen. La torreta lo sigue con la velocidad prevista y lo corrige en cada
  imagen.
- Más de 0,1 m/s respecto a nuestro robot, a 1,2 m, serían unos 5 º/s o más, y el error entre
  imágenes crecería. Por eso `rival_movil.py` no deja pasar de 0,1 m/s.

**Por comprobar en el laboratorio:**
- que el aviso llega por la red del laboratorio;
- cuántos de los 20 disparos registra el rival 2;
- la columna `nitidez` del `registro.csv`, para ver si se descartan fotogramas movidos.
