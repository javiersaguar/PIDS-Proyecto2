# Bloque 2 · Entrenamiento y evaluación

Abre `index.html` en el navegador. Todos los recursos están en esta carpeta y las catorce figuras funcionan también sin servidor ni conexión a Internet.

La página reutiliza el diseño claro y el recorrido vertical del EDA. Cada figura incluye una explicación breve, sus conclusiones y descargas PNG y SVG. El selector de la primera figura cambia sus datos; no hay menús de navegación.

La página tiene dos partes. Las cuatro primeras figuras (`datos.js`, `graficas.js`) son los primeros experimentos con Faster R-CNN. Las diez siguientes (`datos_cadena.js`, `graficas_cadena.js`) comparan los 13 entrenamientos de la cadena y el test: arquitecturas, pérdida y AP por época, tasa de aprendizaje, coste, precisión frente a velocidad, validación frente a test, errores, umbral de confianza, secuencias de test y mapa de medidas. Cada una tiene selectores (medida, modelo, conjunto, escala) y se dibuja al acercarse a ella.

Para actualizar las figuras después de cambiar los CSV, ejecuta desde la raíz:

```sh
python web/Bloque2/preparar_figuras.py
```

El script reutiliza las funciones de `herramientas/construir_web.py`, guarda los datos en `datos.js` y copia la biblioteca local de Plotly. Las figuras de la cadena las genera `herramientas/construir_web_cadena.py` (solo biblioteca estándar) a partir de `ENTREGA 1/WEEK2/cadena/` y `resultados_train/`, y las guarda en `datos_cadena.js`; también se pueden regenerar solas con `python herramientas/construir_web_cadena.py`. Las conclusiones son texto revisado, no se generan automáticamente: hay que comprobarlas si cambian los resultados.

Para construir GitHub Pages con ambos bloques y el selector común:

```sh
python herramientas/construir_spa.py /tmp/pids-pages
```

La portada muestra el Bloque 1; `bloque2/index.html` muestra el Bloque 2. El selector se añade a las copias publicadas. Las páginas originales conservan su diseño independiente. El flujo de `.github/workflows/pages.yml` publica esta construcción cuando se integran los cambios en `main`.
