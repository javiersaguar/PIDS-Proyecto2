# Presentación del proyecto

Borrador de la presentación final de PIDS (Grupo 2): las tres fases del proyecto (datos, modelo y robot) en 23 diapositivas animadas, hechas con React, Vite y Framer Motion.

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

## Teclado

| Tecla | Acción |
|---|---|
| → · Espacio · Intro · AvPág | Siguiente paso de la diapositiva o siguiente diapositiva |
| ← · Retroceso · RePág | Paso o diapositiva anterior |
| ↑ · ↓ | Diapositiva anterior o siguiente, sin pasos |
| Inicio · Fin | Primera o última diapositiva |
| G · Esc | Índice de diapositivas |
| N | Notas del presentador |
| F | Pantalla completa |

Un clic en el 70 % derecho de la pantalla avanza y en el resto retrocede. La dirección guarda la diapositiva (`#12`), así que se puede recargar o enlazar una concreta. Si el sistema tiene activado «reducir movimiento», las animaciones se simplifican.

## De dónde salen los datos

No hay copias de imágenes ni cifras inventadas: todo se lee del repositorio.

- **Imágenes.** El alias `@repo` de `vite.config.js` apunta a la raíz del repositorio. Los fotogramas, las figuras de la memoria, las fotos del laboratorio y las fuentes del mando se importan desde su sitio.
- **`scripts/preparar_datos.mjs`** lee:
  - los XML de `ENTREGA 1/WEEK1/ANOTACION/`, con los recuentos por vídeo y las cajas de los fotogramas que se muestran. Comprueba que el total sigue siendo 808 imágenes, 1420 robots y 375 difficult;
  - las curvas precisión-exhaustividad de `ENTREGA 1/WEEK2/resultados_test/`;
  - las pérdidas por época y el AP de las siete arquitecturas de la web del Bloque 2.
- **`src/datos/cifras.js`** recoge las tablas de la memoria: recogida, dataset, aumento, tasas, test, latencias, circuito, presupuesto de tiempo y robot camuflado. Si cambia una cifra en la memoria, se cambia aquí.

## Estructura

```
presentacion/
├── index.html
├── vite.config.js              alias @repo y puertos
├── scripts/preparar_datos.mjs  datos generados desde el repositorio
└── src/
    ├── App.jsx                 motor: escala 1600×900, teclado, pasos, índice, notas y barra de progreso
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
