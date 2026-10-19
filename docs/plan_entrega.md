# Plan hasta la entrega de los bloques 1 y 2

Última actualización: 19/10/2026. Lo que falta para entregar la memoria de los bloques 1
y 2, en orden. Cada uno puede apuntarse en la columna **Responsable** de las tablas.

**Fechas:** **[PENDIENTE: confirmar las fechas de las dos entregas]**. Los
entrenamientos necesitan **unas 12 horas de GPU** (dos noches en el laboratorio). Hay que
empezar por la sección 1.

## Punto de partida

Resultados en validación (672 imágenes, 1561 robots), confianza 0,5 e IoU 0,5:

| Experimento | lr | Resolución | Mejor época | AP@0,5 | AP 0,50:0,95 | AP@0,5 `difficult` | FP | FN | ms/imagen (una a una) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `faster_rcnn_v1_sin_aug` | 0,0001 | 800 | 20 | 0,923 | 0,581 | 0,552 | 221 | 115 | 75 |
| `faster_rcnn_v1_aug` | 0,0001 | 800 | 29 | 0,942 | 0,608 | 0,634 | 210 | 83 | 75 |
| **`faster_rcnn_v1_aug_lr001`** (referencia) | 0,001 | 800 | 5 | **0,943** | **0,630** | **0,646** | **190** | 83 | 75 |
| `faster_rcnn_v1_aug_lr001_res1024` | 0,001 | 1024 | 2 | 0,946 | 0,605 | 0,628 | 324 | 68 | 122 |

**Qué dicen estos resultados sobre lo que conviene entrenar:**
- **lr 0,001 llega a su mejor resultado en la época 5.** A partir de ahí la pérdida de
  validación sube, y res1024 llega a su mejor resultado en la época 2. Entrenar 30
  épocas con esa tasa es tiempo perdido: **bastan 12**. Así, cada experimento tarda la
  mitad (~2,3 h) y la comparación con lr001 sigue siendo justa, porque su mejor época
  cae dentro de esas 12.
- **No conviene subir la tasa a 0,005.** Con 0,001 ya hay sobreajuste temprano; con
  0,005 habría más.
- **La resolución 1024 no compensa:** gana 0,3 puntos de AP@0,5, pero tiene un 70 % más
  de falsos positivos y tarda un 62 % más por imagen. Se descarta para la *demo*.
- **El punto débil siguen siendo los `difficult`** (AP@0,5 de 0,646). Para eso están los
  perfiles nuevos de `data_aug.ipynb`, que aún no se han entrenado.

## 1. Reentrenar con los perfiles nuevos de aumento

Perfiles de `data_aug.ipynb` (sección 9, detalles en
[`resultados_aug/experimentos/README.md`](../ENTREGA%201/WEEK1/resultados_aug/experimentos/README.md)):
`difficult_v1`, `oclusion_v1`, `sombras_v1`, `lluvia_v1` y `robusto_v1`, que combina
los cuatro.

### Experimentos propuestos

Mismo modelo, `faster_rcnn_v1` a 800, semilla 0, lote 8, y el mismo número de copias
que la referencia. Cada uno se compara con lr001.

| # | Sufijo | Perfil | lr | Épocas | Qué responde | GPU aprox. | Responsable | Estado |
|---|---|---|---:|---:|---|---:|---|---|
| E1 | `difficult_v1` | `difficult_v1` | 0,001 | 12 | ¿Ayuda el refuerzo de movimiento y oscuridad a los `difficult`? | 2,5 h | | Pendiente |
| E2 | `oclusion_v1` | `oclusion_v1` | 0,001 | 12 | ¿Ayudan los postes con textura a los robots tapados? | 2,5 h | | Pendiente |
| E3 | `robusto_v1` | `robusto_v1` | 0,001 | 12 | ¿Suman las cuatro ampliaciones juntas? | 2,5 h | | Pendiente |
| E4 | `<perfil>_lr0005` | El mejor de E1–E3 | 0,0005 | 15 | ¿Una tasa intermedia evita el sobreajuste de la época 5 sin volver a la lentitud de 0,0001? | 3 h | | Pendiente |

**Por qué solo estos:**
- **`sombras_v1` y `lluvia_v1` no se prueban por separado.** Solo afectan a los dos
  vídeos de exterior (V04 y V09), y validación no tiene lluvia. Su efecto ya queda
  medido dentro de `robusto_v1`.
- **Cada experimento que se elige mirando validación la va desgastando** (ver
  [`mejoras_entrenamiento.md`](mejoras_entrenamiento.md)). Por eso son cuatro como
  mucho.

**Opcional, si sobra tiempo de laboratorio:** `faster_rcnn_v2` con el mejor perfil.
Tiene mejores pesos de COCO, pero es más lento y quizá no quepa en memoria con lote 8:
probar antes con `herramientas/comprobar_res1024.py` como modelo.

### Cambios de código antes de lanzar

1. **`train.ipynb`:**
   - Añadir `perfil_aumento = 'base'`. Si no es `base`, `path_data_train` pasa a
     `{RAIZ}/datasets_experimentos/{perfil_aumento}/data_train`.
   - El sufijo debe incluir el perfil, para que **ningún experimento pise ni reanude
     otro** en `models/`.
   - Validación sigue siendo la de siempre, `data_val`.
2. **`test.ipynb`:** el mismo `perfil_aumento` y el mismo sufijo, para que cargue el
   modelo correcto. Mientras se elige el modelo, `conjunto = 'val'`.
3. **Un script para lanzarlos uno tras otro en el laboratorio.** Para cada
   experimento hace tres cosas, cada una con su log y su fichero `.exit`, como
   res1024:
   - genera el dataset del perfil con `data_aug.ipynb` y `PERFIL_AUMENTO` (unos 15
     minutos por perfil);
   - entrena;
   - evalúa en validación.
4. **En el laboratorio:** comprobar que `albucore==0.0.17` está instalado, porque lo
   exigen los perfiles. Pasar las pruebas `python -m pytest
   herramientas/tests/test_aumento_robusto.py -q`.

### Cómo se elige el modelo definitivo

1. **Criterio principal:** el mayor AP@0,5 en validación con todos los robots.
2. **Si la diferencia es de menos de 0,5 puntos,** se considera empate, porque solo hay
   una semilla. Entonces decide el AP@0,5 de los `difficult` y, después, el menor
   número de FP.
3. **Si ningún perfil supera a lr001, se queda lr001.** Es más sencillo y ya está
   medido.
4. **La latencia no decide aquí:** todos usan el mismo modelo y la misma resolución, y
   tardan lo mismo.

## 2. Comparar los resultados

| Tarea | Responsable | Estado |
|---|---|---|
| Generalizar `herramientas/comparar_entrenamientos.py` para que acepte una lista de experimentos. Ahora compara solo dos, fijos en el código | | Pendiente |
| Generar `ENTREGA 1/WEEK2/comparaciones/perfiles/`: tabla con todos los experimentos, curvas de validación superpuestas, AP@0,5 por secuencia y FP/FN por grupo | | Pendiente |
| Revisar a ojo los `ejemplos_peores.jpg` del modelo elegido: si los FP son robots que el otro grupo no anotó, se explica en la memoria. Ya hay un caso confirmado en `PIDS2024_GR02_0001/frame_0444.jpg` | | Pendiente |
| Fijar el **umbral de la *demo*** con el F1 de validación del modelo elegido (lr001 lo tiene en 0,85) | | Pendiente |
| **Evaluar en test una sola vez**, con el modelo definitivo y el umbral ya fijado: `conjunto = 'test'` en `test.ipynb`. Anotar fecha y commit; no se repite | | Pendiente |

## 3. Preparar los archivos finales

Los notebooks que se entregan: `eda.ipynb`, `data_aug.ipynb`, `train.ipynb` y
`test.ipynb`. **[PENDIENTE: confirmar con la asignatura el formato: notebooks
sueltos, zip o enlace al repositorio]**.

| Notebook | Qué hay que dejar | Responsable | Estado |
|---|---|---|---|
| `ENTREGA 1/WEEK1/eda.ipynb` | Ejecutado de principio a fin con las 796 imágenes depuradas y con salidas. La PR #13 de Pedro (selección de gráficas) se cerró sin fusionar. Si se quiere esa selección, rehacerla en otra PR **sin quitar** la celda que genera `metricas_imagenes.csv`, que usa la depuración, y sin conclusiones que remitan a secciones borradas | | Pendiente |
| `ENTREGA 1/WEEK1/data_aug.ipynb` | `PERFIL_AUMENTO` con el perfil elegido (o `base`) y ejecutado con salidas. Que la sección 9 explique qué perfiles se probaron y con qué resultado | | Pendiente |
| `ENTREGA 1/WEEK2/train.ipynb` | Valores por defecto del modelo definitivo: perfil, `lr`, épocas, sufijo. Copia ejecutada en el laboratorio con salidas y curvas | | Pendiente |
| `ENTREGA 1/WEEK2/test.ipynb` | Dos copias ejecutadas: validación (para ajustar) y test (resultado final), con salidas | | Pendiente |
| Variantes sueltas (`train_res1024.ipynb`, `test_val_res1024.ipynb`) | Moverlas a `ENTREGA 1/WEEK2/experimentos/` o quitarlas, para que no se confundan con los notebooks entregables. Su configuración ya está en `resultados_train/*/configuracion.json` | | Pendiente |

**Comprobaciones antes de entregar cada notebook:**
- Se ejecuta entero en el JupyterHub del laboratorio con «Restart & Run All», sin
  celdas rotas ni dependencias de variables de otra sesión.
- Sin credenciales, tokens ni rutas personales; las rutas de `/home/jovyan` del
  laboratorio no son personales.
- Cada fichero pesa menos de 50 MB (los ejecutados de `test` rondan los 4,5 MB) y no
  tiene salidas enormes: barras de progreso de miles de líneas o imágenes repetidas.
- Los textos y las conclusiones coinciden con las cifras finales de la memoria.

## 4. Enlaces a las gráficas interactivas

Hay gráficas interactivas en
[`resultados_eda/interactivos/`](../ENTREGA%201/WEEK1/resultados_eda/interactivos/), con
[`indice.html`](../ENTREGA%201/WEEK1/resultados_eda/interactivos/indice.html) como
portada. GitHub muestra los `.html` como código, así que hace falta publicarlos.

| Tarea | Responsable | Estado |
|---|---|---|
| **Publicar con GitHub Pages una página única con todas las figuras.** Cada figura tiene título, descripción, cómo usarla y conclusiones. La página es [`web/index.html`](../web/index.html); la monta [`herramientas/construir_web.py`](../herramientas/construir_web.py), y el flujo [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) la publica en cada push a `main` que toque la web o los resultados. No publica el dataset | Javier Saguar | Hecho |
| Activar Pages en *Settings → Pages → Source: GitHub Actions* | Javier Saguar | Hecho |
| Gráficas interactivas del Bloque 2, generadas desde los CSV de resultados: curvas de entrenamiento, AP@0,5 y errores por grupo, y AP@0,5 por secuencia. **Al añadir experimentos (E1–E4),** hay que añadirlos a `EXPERIMENTOS` en `construir_web.py` y revisar las conclusiones de la página. Falta la curva del umbral de confianza | Javier Saguar | Hecha, salvo el umbral |
| Comprobar que cada enlace se abre sin sesión iniciada, también en el móvil, y que `plotly.min.js` se carga desde la propia web | | Pendiente |
| Poner los enlaces en la memoria: uno por figura, en el pie («versión interactiva: …»), y una lista en un anexo | | Pendiente |

Enlaces (cada figura tiene su ancla en la página única):

| Figura | Enlace |
|---|---|
| Página completa | https://javiersaguar.github.io/PIDS-Proyecto2/ |
| 1 · Posición por vídeo | https://javiersaguar.github.io/PIDS-Proyecto2/#mapas-video |
| 2 · Posición en el tiempo | https://javiersaguar.github.io/PIDS-Proyecto2/#mapas-tiempo |
| 3 · Robots por fotograma | https://javiersaguar.github.io/PIDS-Proyecto2/#robots-fotograma |
| 4 · Curvas de entrenamiento | https://javiersaguar.github.io/PIDS-Proyecto2/#curvas |
| 5 · Resultados por grupo | https://javiersaguar.github.io/PIDS-Proyecto2/#grupos |
| 6 · Resultados por secuencia | https://javiersaguar.github.io/PIDS-Proyecto2/#secuencias |

Las páginas sueltas del EDA (`.../eda/interactivos/*.html`) se siguen publicando, para que no se rompan los enlaces antiguos.

**Alternativa sin configurar nada:** `https://htmlpreview.github.io/?<URL del html en
GitHub>`. Es más lenta y depende de un servicio externo; mejor solo como reserva.

## 5. Actualizar los informes

Los informes se generan desde el repositorio con `herramientas/generar_informes.py` (ver
[`informes/README.md`](informes/README.md)). Hay que actualizar el generador y los
textos, no los Word a mano.

| Tarea | Responsable | Estado |
|---|---|---|
| **Fase 1** (entrega 1, máximo 10 páginas de cuerpo): describir los perfiles nuevos de aumento solo como parte del Bloque 1, y su efecto medido si se adopta alguno | | Pendiente |
| **Fase 1:** cerrar en grupo T01 (borde superior del robot, antenas) y reflejar el acuerdo | | Pendiente |
| **Fase 1:** confirmar el número de grupo (2, por el usuario `pids2`), las fechas y el reparto del trabajo | | Pendiente |
| **Fase 2** (entrega 2, incremental, con la fase 1 corregida): sección de experimentos con E1–E4 y la tabla completa | | Pendiente |
| **Fase 2:** la elección del modelo definitivo con el criterio de la sección 1 | | Pendiente |
| **Fase 2:** el resultado en test y el umbral de la *demo* | | Pendiente |
| **Fase 2:** el análisis de los FP con etiquetas incompletas | | Pendiente |
| Enlaces a las gráficas interactivas (sección 4) en los pies y en el anexo | | Pendiente |
| Pasar `docs/informe_borrador.md` a los informes o marcarlo como histórico, para que no haya dos versiones con cifras distintas | | Pendiente |
| Regenerar Word y Markdown y exportar el PDF desde Word: actualizar el índice con F9, revisar todas las páginas y contar las páginas de cuerpo | | Pendiente |
| Nombres finales: `PIDS_grupo2_entrega1.pdf` y `PIDS_grupo2_entrega2.pdf` | | Pendiente |
| Revisión final de las cifras: todas las de la memoria salen de los CSV de `resultados_*` y `comparaciones/` | | Pendiente |

## Orden recomendado

1. **Hoy:** cambios de código de la sección 1 y lanzamiento de E1–E3 en cadena. Los
   que no estén en el laboratorio pueden ir con la sección 3 (EDA) y el flujo
   de Pages de la sección 4.
2. **Al día siguiente:** comparar E1–E3 y lanzar E4 con el mejor perfil.
3. **Después de E4:** elegir el modelo, evaluar en test una vez y fijar el umbral.
4. **Notebooks finales** ejecutados (sección 3) y **gráficas del Bloque 2** (sección 4).
5. **Informes** (sección 5) y revisión cruzada de las cifras. Entrega 1 primero.
