# Presentación del proyecto

Borrador de la presentación final de PIDS (Grupo 2): las tres fases del proyecto (datos, modelo y robot) en 26 diapositivas animadas, hechas con React, Vite y Framer Motion.

## Cómo se usa

Hace falta Node 18 o posterior.

```bash
cd presentacion
npm install
npm run dev        # http://localhost:5190 con recarga en caliente
```

Otros comandos:

| Comando | Qué hace |
|---|---|
| `npm run build` | Genera `dist/`, una versión estática que se abre con cualquier servidor (rutas relativas). |
| `npm run preview` | Sirve `dist/` en http://localhost:5191 para comprobar la versión final. |
| `npm run datos` | Vuelve a generar `src/datos/generados.json` y `src/datos/fotogramas.js` a partir del repositorio. |
| `npm run html` | Genera la presentación en un solo fichero, `docs/entregas/PIDS_grupo2_presentacion.html`, con las imágenes y las fuentes incrustadas: se abre con doble clic, sin servidor ni conexión. |
| `npm run boceto` | Sirve en http://localhost:5192 la versión anterior a las animaciones, para compararlas (ver más abajo). |

## Teclado

| Tecla | Acción |
|---|---|
| → · Espacio · Intro · AvPág | Siguiente paso de la diapositiva o siguiente diapositiva |
| ← · Retroceso · RePág | Paso o diapositiva anterior |
| ↑ · ↓ | Diapositiva anterior o siguiente, sin pasos |
| Inicio · Fin | Primera o última diapositiva |
| G · Esc | Índice de diapositivas |
| N | Notas del presentador |
| R | Repite la entrada de la diapositiva actual |
| F | Pantalla completa |

Un clic en el 70 % derecho de la pantalla avanza y en el resto retrocede. La dirección guarda la diapositiva (`#12`), así que se puede recargar o enlazar una concreta. Si el sistema tiene activado «reducir movimiento», las animaciones se simplifican.

## Animaciones

Ninguna animación añade clics ni cambia el contenido: todas arrancan solas al entrar en la diapositiva y acaban en la misma imagen que la versión sin animar. La única excepción es la 12, donde las propuestas sobrantes desaparecen en vez de quedar atenuadas.

- **Para toda la presentación.** El cambio de diapositiva es un corte de 0,55 s con una línea verde que barre la pantalla; las portadas de fase salen con la cortina de su color. La barra inferior lleva un punto en la diapositiva actual. El componente `Fijar` (`componentes/fotograma.jsx`) engancha las esquinas de la caja de detección a lo importante de cada diapositiva: la barra elegida, el modelo final o la cifra clave. Las imágenes de la diapositiva siguiente se cargan por adelantado (`Componente.imagenes`).
- **Seis animaciones grandes**, una por tramo de la charla: 5 (las cajas se anotan en vivo), 7 (barrido de radar sobre los puntos), 12 (las propuestas colapsan sobre el robot), 16 (el círculo recorre la curva hasta el umbral 0,95), 22 (interferencia en las fotos del profesor) y 23 (los puntos suben hasta la barrera del umbral).
- **Plan B.** Con `?fx=0` en la dirección (por ejemplo `http://localhost:5190/?fx=0#12`) las seis grandes se sustituyen por su entrada sencilla. Sirve si el ordenador del aula va justo.

Solo se animan posición, escala, opacidad y recortes; no hay desenfoques.

### Comparar con la versión anterior

La versión anterior a las animaciones es el commit `ae80529` (etiqueta local `presentacion-boceto-v1`) y está compilada en `boceto/` (fuera del repositorio). Para verlas a la vez:

```bash
npm run boceto     # la versión anterior, en http://localhost:5192
npm run dev        # la actual; después se abre http://localhost:5190/comparar.html
```

`comparar.html` muestra las dos presentaciones, pasa las diapositivas a la vez con las flechas o con un clic, y repite la entrada de ambas con la tecla R. Con dos presentaciones abiertas el ordenador trabaja el doble: la fluidez se comprueba con la actual sola. Si falta `boceto/`, se vuelve a generar con `git stash`, `git checkout ae80529`, `npm run build -- --outDir boceto` y de vuelta a la rama.

## De dónde salen los datos

No hay copias de imágenes ni cifras inventadas: todo se lee del repositorio.

- **Imágenes.** El alias `@repo` de `vite.config.js` apunta a la raíz del repositorio. Los fotogramas, las figuras de la memoria, las fotos del laboratorio y las fuentes del mando se importan desde su sitio.
- **`scripts/preparar_datos.mjs`** lee:
  - los XML de `ENTREGA 1/WEEK1/ANOTACION/`, con los recuentos por vídeo y las cajas de los fotogramas que se muestran. Comprueba que el total sigue siendo 808 imágenes, 1420 robots y 375 difficult;
  - las curvas precisión-exhaustividad de `ENTREGA 1/WEEK2/resultados_test/`;
  - las pérdidas por época y el AP de las siete arquitecturas de la web del Bloque 2;
  - el EDA de las cajas (posición, tamaño, forma, solapamiento y nitidez relativa de `ENTREGA 1/WEEK1/resultados_eda/metricas_imagenes.csv`). Comprueba que salen las cifras de los apartados 4.2 a 4.4 de la memoria.
- **`herramientas/figuras_aumento.py`** (con el entorno `.venv-aug`, albumentations 1.4.18) aplica cada transformación del aumento por separado, también las que no se usaron, y escribe las imágenes en `docs/informes/figuras/aumento/` y sus cajas en `src/datos/aumento.js`.
- **`src/datos/cifras.js`** recoge las tablas de la memoria: recogida, dataset, aumento, tasas, test, latencias, circuito, presupuesto de tiempo y robot camuflado. Si cambia una cifra en la memoria, se cambia aquí.

## Estructura

```
presentacion/
├── index.html
├── comparar.html               la versión anterior y la actual, lado a lado (solo con npm run dev)
├── vite.config.js              alias @repo y puertos
├── scripts/preparar_datos.mjs  datos generados desde el repositorio
├── scripts/html_unico.mjs      la presentación en un solo .html para entregar
└── src/
    ├── App.jsx                 motor: escala 1600×900, teclado, pasos, transiciones, índice, notas y barra de progreso
    ├── estilos.css             colores y tipografías del mando (Geist, JetBrains Mono, Silkscreen)
    ├── componentes/            contadores, cascadas, cajas de detección, gráficas SVG y portadas de fase
    ├── datos/                  cifras.js (memoria) y los ficheros generados
    └── diapositivas/
        ├── index.js            orden, fase y notas de cada diapositiva
        ├── inicio.jsx          portada y el caso
        ├── fase1.jsx           datos: recogida, anotación, EDA y aumento
        ├── fase2.jsx           modelo: sistema, arquitecturas, ajuste, comparación, test y análisis
        ├── fase3.jsx           robot: circuito, ataque en marcha y mando
        └── cierre.jsx          gracias y preguntas
```

Para añadir una diapositiva: se crea el componente en el fichero de su fase y se añade a `DIAPOSITIVAS` en `diapositivas/index.js` con su `id`, `fase` y `notas`. Si tiene fragmentos, se indica `pasos: N` y el componente recibe `paso` (de 0 a N).

## Nota sobre Rollup

`package.json` sustituye Rollup por `@rollup/wasm-node` (`overrides`). En los equipos con Windows y control de aplicaciones, el binario nativo de Rollup no se puede cargar y `vite build` falla. La versión WebAssembly da el mismo resultado.

## Pendiente

Es un borrador. Las diapositivas de la fase 3 (circuito y ataques en marcha) se actualizarán con los resultados del laboratorio, igual que la memoria del Bloque 3.
