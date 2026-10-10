# Guía para anotar paso a paso

Guía práctica para que los cinco anotemos **igual y bien**. Las reglas completas y su justificación están en [`criterios_anotacion.md`](criterios_anotacion.md). Esta guía es lo que hay que tener delante mientras se anota.

**Antes de empezar:**
1. Lee la [chuleta de reglas](#4-reglas-de-anotacion-la-chuleta) de la sección 4.
2. Anota las **20 imágenes de calibración** (sección 6) **antes** que tu lote.

---

## 1. Qué necesitas

- **labelImg**. Los ordenadores del laboratorio ya lo tienen. Para instalarlo en casa:
  - **Linux / macOS** (Python 3.8–3.9):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install labelImg==1.8.6
    labelImg
    ```
  - **Windows con Anaconda:**
    ```bash
    conda create -n venv python=3.7
    conda activate venv
    pip install labelImg==1.8.6
    labelImg
    ```
  - **Windows con Python 3.10 o superior:** labelImg 1.8.6 se cierra al dibujar o al hacer zoom, porque pasa números decimales a funciones de Qt que solo aceptan enteros. Usa Python 3.9 o anterior. Si solo tienes Python 3.12, pide a Javier el arreglo que él aplicó.
- **Tu rama personal clonada**, con tu lote en `ENTREGA 1/WEEK1/ANOTACION/<letra>_<tu-nombre>/`. Ver [`ANOTACION/README.md`](../ENTREGA%201/WEEK1/ANOTACION/README.md).

## 2. Abrir labelImg en la carpeta correcta

Cada vídeo de tu lote tiene su carpeta con `images/` (los fotogramas) y `labels/` (donde se guardan los `.xml`). **Se anota vídeo a vídeo.**

1. **Open Dir** → `ROBOMASTER_VIDEO_XX/images`.
2. **Change Save Dir** → `ROBOMASTER_VIDEO_XX/labels`, **del mismo vídeo**. Es el error más típico: si te equivocas, los `.xml` acaban en otra carpeta.

Atajo: también se puede abrir desde la terminal pasando las dos carpetas y un fichero de clases que contenga una sola línea, `robot`:

```bash
labelImg "ROBOMASTER_VIDEO_XX/images" clases.txt "ROBOMASTER_VIDEO_XX/labels"
```

## 3. Configuración, una sola vez al empezar

| Dónde | Qué poner | Por qué |
|---|---|---|
| Botón bajo *Save* (barra izquierda) | **PascalVOC**, no YOLO ni CreateML | Los notebooks leen `.xml` PascalVOC |
| Menú **View** | ✔ **Single Class Mode** | No pregunta la clase en cada caja |
| Menú **View** | ✔ **Auto Save mode** | Guarda solo al pasar de imagen |
| Primera caja | Escribir `robot`, en minúsculas y sin espacios | Única clase del proyecto |

### Atajos

| Tecla | Acción |
|---|---|
| `w` | Dibujar una caja nueva (clic y arrastrar) |
| `d` / `a` | Imagen siguiente / anterior |
| `Ctrl+S` | Guardar la imagen actual |
| `Ctrl` + rueda del ratón | Zoom, imprescindible para los robots pequeños |
| `Supr` | Borrar la caja seleccionada |
| Casilla **difficult** (panel derecho) | Marca la caja seleccionada como difícil |

Para mover una caja, arrástrala. Para ajustarla, arrastra sus esquinas. En la *File List* (abajo a la derecha) se puede hacer doble clic para ir a una imagen concreta.

## 4. Reglas de anotación (la chuleta)

### Qué SÍ lleva caja

- **Cualquier RoboMaster**, con cualquier color de luces, de frente, de lado o de espaldas, y esté quieto o en movimiento.
- **Un robot por caja**, aunque estén pegados o se solapen.
- **Robots tapados** (por sillas, piernas u otro robot) si se **reconocen** y se ve aproximadamente un **30 %** o más. La caja cubre **solo lo visible**.
- **Robots cortados por el borde** de la imagen, con el mismo criterio. La caja llega **hasta el borde**.
- **Robots muy cerca** que llenan media imagen.
- **Robots lejanos** de al menos **10 px**. Usa el zoom para ajustar bien.

### Qué NO lleva caja

- **Nuestro propio cañón** naranja, abajo en el centro de **todas** las imágenes. Nunca.
- **Reflejos** de los robots en el suelo.
- Robots en **pantallas de móvil**, carteles o fotos.
- Personas, sillas, motos, zapatos o cualquier otra cosa.
- **Estelas o manchas** donde sabes que hay un robot porque viste el vídeo, pero que en la foto no se reconoce.

### Cómo se ajusta la caja

```
        antenas ← FUERA
     ┌──────────────┐  ← borde superior: lo alto del gimbal
     │  gimbal +    │
     │  cañón       │  ← el cañón SÍ va dentro, aunque sobresalga
     │  chasis      │
     │  ruedas      │
     └──────────────┘  ← borde inferior: donde las ruedas tocan el suelo
        reflejo ← FUERA
```

- La caja va **ajustada** al robot, con unos ±2 px de margen y sin fondo de sobra.
- **Sin antenas**, sin sombra, sin reflejo y sin el halo de luz de los LED.
- Si el robot está **movido**, la caja va al **cuerpo** del robot, no a toda la estela.

### Cuándo marcar `difficult`

Selecciona la caja y marca la casilla **difficult** si el robot:

- mide **menos de 30 px de ancho** (lejano);
- se ve **menos de la mitad** (tapado o cortado);
- está **muy movido** pero aún se reconoce.

Si el robot está nítido, completo y es grande, **no** se marca, aunque te haya costado verlo.

### Imágenes sin robots

**Pulsa `Ctrl+S` igualmente.** Así se crea su `.xml` vacío, que enseña a la red lo que *no* es un robot. Si no lo guardas, la imagen no se usa.

### Regla de oro para las dudas

> **«Si viera SOLO este fotograma, sin el vídeo, ¿diría sin dudar que ahí hay un robot?»**
>
> - **Sí** → caja, siguiendo las reglas de arriba.
> - **No** → sin caja, y apúntalo en [`casos_dudosos.md`](casos_dudosos.md).

Más vale **no poner caja que poner una mala**: el entrenamiento convierte toda caja en «robot».

## 5. Errores más comunes (visto en la calibración)

| Error | Cómo evitarlo |
|---|---|
| Caja que empieza en la punta de las antenas | Baja el borde superior hasta el gimbal |
| No marcar `difficult` en robots muy movidos o medio tapados | Repasa la lista de la sección 4 en cada caja |
| Marcar `difficult` en un robot nítido y completo | Solo se marca en los tres casos de la lista |
| Olvidar guardar las imágenes sin robots | `Ctrl+S` en **todas** las imágenes |
| `Change Save Dir` apuntando a otro vídeo | Compruébalo cada vez que cambies de vídeo |
| Clic sin arrastrar, que deja una caja de 0 px y rompe el entrenamiento | El validador lo detecta; bórrala con `Supr` |
| Caja para el reflejo o para nuestro cañón | Nunca llevan caja |

## 6. Orden de trabajo

1. **Calibración (T01):**
   - Abre `ENTREGA 1/WEEK1/ANOTACION/calibracion/images` y guarda en `calibracion/<tu-nombre>/labels`.
   - Anota las 20 imágenes **por tu cuenta, sin mirar las de los demás**. Sirve para medir si anotamos igual.
2. **Tu lote (T04–T08):** primero un vídeo y luego el otro, revisando **todas** las imágenes, incluidas las vacías.
3. **Repaso:** pasa otra vez todas las imágenes con `d` y comprueba:
   - que no falte ningún robot;
   - que no haya cajas de más;
   - las antenas;
   - el `difficult`.
4. **Validar** desde la raíz del repositorio:
   ```bash
   python herramientas/revisar_anotaciones.py validar "ENTREGA 1/WEEK1/ANOTACION/<tu-lote>"
   ```
   Tiene que acabar en **«Sin errores.»** Los avisos hay que revisarlos uno a uno.
5. **Subir:**
   - Haz commit en **tu rama** y actualiza tu PR hacia `main`.
   - Mensaje en español y en imperativo, por ejemplo `Anota el lote B: vídeos 03 y 04 (T05)`.
   - **Sin coautores ni atribuciones a herramientas** (ver [`AGENTS.md`](../AGENTS.md)).

## 7. Si algo no encaja

- Apúntalo en [`casos_dudosos.md`](casos_dudosos.md) con el vídeo, el fichero, tu nombre, el problema y la decisión tomada.
- Si es un caso que se repite mucho, coméntalo en el grupo para añadirlo a los criterios. No lo resuelvas cada uno a su manera.
