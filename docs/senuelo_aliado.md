# Robot camuflado y robot aliado: ¿a qué dispara el detector?

Estudio del 06/11/2026 para la demo del Bloque 3, la presentación y la memoria.

## 1. Pregunta

Para la demo se buscó un **señuelo**: algo con aspecto de robot al que nuestro RoboMaster
no disparase, para enseñar que no ataca a todo lo que ve. Se probaron dos ideas:

1. **Un RoboMaster disfrazado** (gabardina, sombrero y bigote), que se reconociese como
   RoboMaster pero que el detector no viera.
2. **Un robot aliado** marcado en verde (bandera, brazalete y luces), al que el robot no
   debería disparar.

Todas las imágenes se generaron con una IA de imágenes y están en
[`informes/figuras/senuelo/`](informes/figuras/senuelo/).

## 2. Método

`ENTREGA 2/WEEK3/probar_senuelo.py` pasa cada imagen por el detector de la demo (Faster
R-CNN v2, umbral 0,95). La prueba se hace con la imagen tal cual y dentro de un fotograma de
la cámara (1280×720, fondo gris), ocupando el 80, 50, 30 y 20 % del alto. Así se simula que
está más cerca o más lejos. Para la detección más segura da además el porcentaje de **verde
intenso** dentro de su caja.

```bash
cd "ENTREGA 2/WEEK3"
python probar_senuelo.py --tapar ../../docs/informes/figuras/senuelo/*.jpg
```

## 3. Resultados

Confianza máxima del detector. Por encima de 0,95 (95 %), la demo dispara.

| Imagen | Original | 80 % alto | 50 % alto | 30 % alto | 20 % alto | Verde en la caja | ¿Dispara? |
|---|---|---|---|---|---|---|---|
| Detective con bigote | 99,5 % | 99,7 % | 99,8 % | 99,9 % | 99,6 % | 0,0 % | 5 de 5 |
| Detective | 98,8 % | 99,8 % | 99,8 % | 99,9 % | 99,7 % | 0,0 % | 5 de 5 |
| Aliado S1 | 99,8 % | 99,9 % | 99,9 % | 99,9 % | 99,9 % | 5,7 % | 5 de 5 |
| Aliado cabeza redonda | 99,8 % | 99,9 % | 99,9 % | 99,9 % | 99,9 % | 11,0 % | 5 de 5 |
| Aliado en dibujo | 97,8 % | 97,9 % | 96,5 % | 93,7 % | 92,7 % | 7,6 % | 3 de 5 |
| Aliado blanco | 95,4 % | 95,7 % | 97,1 % | 98,9 % | 98,5 % | 12,5 % | 5 de 5 |

**¿En qué se fija el modelo?** Se taparon en blanco partes del detective con bigote:

| Zona tapada | Confianza |
|---|---|
| Ruedas y zapatos | 99,3 % |
| Cañón | 99,2 % |
| Cabeza y gimbal | 94,2 % |
| Chasis central | 99,8 % |
| Todas a la vez | 52,0 % |

Tapando una sola parte apenas cambia; solo la cabeza con el gimbal lo deja justo por debajo
del umbral. El modelo reconoce el robot por el conjunto.

**Formas que no son robots.** También se dibujaron sobre fondo gris un círculo verde, una caja
gris y una caja con ruedas, cabeza y cañón. Ninguna dio detección. El modelo no dispara a
cualquier objeto destacado.

## 4. Conclusiones

- **El disfraz no engaña al detector.** El detective da entre 98,8 y 99,9 % a todas las
  distancias. Para la demo se le da la vuelta a la idea: en P1, tras eliminar al rival de la
  derecha, el robot gira la torreta a la izquierda y elimina al **robot camuflado**
  (`detective.jpg`). Mensaje: aunque se disfrace, lo reconoce.
- **El modelo ha aprendido el concepto de robot, no solo el RoboMaster.** Cinco robots
  distintos, también con cabeza redonda o en dibujo, dan positivo. Solo el dibujo
  baja del umbral, y solo a distancia y por poco. Con un robot "con forma de robot" no se
  puede garantizar que el detector no lo vea. En la demo real bastaría un reflejo o un cambio
  de luz para que pase del umbral.
- **Un aliado se reconoce por una marca, no por su forma.** Los aliados tienen entre un 5,7 y
  un 12,5 % de verde intenso dentro de su caja, y el detective un 0 %. Con la regla "más de un
  2 % de verde dentro de la caja: aliado", los dos grupos quedan separados con margen. Es lo
  que se hace en las competiciones de RoboMaster, donde los equipos se distinguen por el color
  de las luces de la armadura.

## 5. Propuesta del robot aliado (no implementada)

El grupo decidió el 06/11 dejar en la demo solo el robot camuflado. La identificación de
aliados queda documentada para la presentación y como trabajo futuro en la memoria:

1. Con cada detección que supere el umbral, medir la fracción de verde intenso dentro de la
   caja (HSV: tono 70-170º, saturación y brillo altos), como hace `probar_senuelo.py`.
2. Por encima del 2 %, marcarla como aliado: no se dispara, el LED se pone verde, puede sonar
   un aviso de "aliado" y la imagen de evidencias lo indica.
3. Con robots reales, el aliado llevaría sus LED en verde (`led.set_led` del SDK) o una
   bandera verde.

Riesgos que habría que medir antes de usarlo: la luz del laboratorio cambia el tono, y un
fondo verde detrás de un enemigo podría confundirse con la marca. Por eso se mide dentro de la
caja y no en toda la imagen.

## 6. En la demo y en la presentación

- **Robot camuflado:** imprimir `informes/figuras/senuelo/detective_imprimir.jpg` en A3 (unos
  35 cm de alto, como la caja de un RoboMaster real) y colocarlo a la izquierda de P1.
  Comprobarlo antes con el robot quieto y sin disparar:
  `python demo.py --sin-mover --sin-disparar --paradas P1 --ver`.
- **Presentación:** la tabla del apartado 3 y la figura con el detective y un aliado cuentan
  la historia en una diapositiva. "¿Y si el rival se disfraza? Lo detecta igual. ¿Y un
  aliado? Por su forma, también. Para no dispararle hace falta una marca, como en la
  competición."
