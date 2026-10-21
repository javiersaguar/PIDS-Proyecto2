# Bloque 2 · Entrenamiento y evaluación

Abre `index.html` en el navegador. Todos los recursos están en esta carpeta y las cuatro figuras funcionan también sin servidor ni conexión a Internet.

La página reutiliza el diseño claro y el recorrido vertical del EDA. Cada figura incluye una explicación breve, sus conclusiones y descargas PNG y SVG. El selector de la primera figura cambia sus datos; no hay menús de navegación.

Para actualizar las figuras después de cambiar los CSV, ejecuta desde la raíz:

```sh
python web/Bloque2/preparar_figuras.py
```

El script reutiliza las funciones de `herramientas/construir_web.py`, guarda los datos en `datos.js` y copia la biblioteca local de Plotly. Las conclusiones son texto revisado, no se generan automáticamente: hay que comprobarlas si cambian los resultados.

Para construir GitHub Pages con ambos bloques y el selector común:

```sh
python herramientas/construir_spa.py /tmp/pids-pages
```

La portada muestra el Bloque 1; `bloque2/index.html` muestra el Bloque 2. El selector se añade a las copias publicadas. Las páginas originales conservan su diseño independiente. El flujo de `.github/workflows/pages.yml` publica esta construcción cuando se integran los cambios en `main`.
