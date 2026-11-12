# Bloque 3 · El detector en el robot

Abre `index.html` en el navegador. No necesita servidor, conexión ni bibliotecas: las tres figuras se dibujan en SVG con `graficas.js`.

- **La demo, foto a foto.** Las fotos que guarda la demo cada 0,5 s (`FOTOS_RECORRIDO` en `circuito.py`), con la posición del robot en el plano medido y las fases del recorrido.
- **Qué vio el detector en cada imagen.** Cada imagen analizada en los ataques: confianza de las detecciones frente al umbral, ángulo de la torreta y tiempo por imagen. Al pulsar un punto se ve la imagen con las cajas.
- **Cuánto duró cada fase.** Las dos pasadas comparadas fase a fase.

Los datos son los dos intentos del 12/11/2026 en clase: la demo oficial y el intento sorpresa del profesor. Las evidencias no se versionan, así que `datos.js` y las miniaturas de `imagenes/` (WebP de 480 px) se guardan ya generados. Para regenerarlos, desde la raíz y con Pillow:

```sh
python web/Bloque3/preparar_datos.py ["ENTREGA 2/WEEK3/evidencias"]
```

Las conclusiones son texto revisado: hay que comprobarlas si cambian los datos.
