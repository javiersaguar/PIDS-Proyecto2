# Entrenar en el JupyterHub del laboratorio

Guía para llevar el dataset a JupyterHub y dejar el entrenamiento corriendo (T03, T19
y T20). El JupyterHub tiene Python 3.8 y albumentations 1.4.18, las mismas versiones
con las que se ha probado `data_aug.ipynb`.

> El servicio está deshabilitado por las mañanas en horas de docencia. Conviene lanzar
> el entrenamiento por la tarde, para que no lo corten.

## 1. Llevar el proyecto y los datos

Todo funciona igual que en local si el repositorio está en JupyterHub y los datos en
su raíz: los notebooks encuentran la raíz solos, buscando `herramientas/`.

**Opción A (recomendada): clonar el repositorio y generar los datos allí.** Así se
comprueba además que `data_aug.ipynb` funciona en JupyterHub. Desde un terminal de
JupyterHub (*File → New → Terminal*):

```bash
cd ~
git clone https://github.com/javiersaguar/PIDS-Proyecto2.git
```

Si el repositorio es privado o no hay acceso a GitHub desde el laboratorio, descargar
`Code → Download ZIP` de `main`, subirlo con el botón de subir ficheros y descomprimirlo
con `unzip PIDS-Proyecto2-main.zip`.

Después, abrir `ENTREGA 1/WEEK1/data_aug.ipynb` y ejecutarlo entero
(*Run → Run All Cells*). Tarda un par de minutos y crea `data_train/`, `data_val/` y
`data_test/` en la raíz del repositorio. Al final debe decir `Sin errores.` en los
tres conjuntos.

**Opción B: subir el dataset ya generado.** `data_aug.ipynb` con `EXPORTAR_ZIP = True`
crea `dataset_pids.zip` (unos 350 MB). Se sube a la raíz del repositorio en
JupyterHub y se descomprime allí, en una carpeta sin `data_train/`:

```bash
cd ~/PIDS-Proyecto2
unzip -q dataset_pids.zip
ls data_train data_val data_test | head
```

## 2. Comprobar la GPU y el Python del kernel

En una celda de cualquier notebook:

```python
import sys, torch
print(sys.executable)
print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')
```

Hay que apuntar la ruta que imprime `sys.executable`: es el Python del entorno
`pids:default`, el que tiene PyTorch.

## 3. Dejar el entrenamiento corriendo

Si se ejecuta `train.ipynb` desde el navegador y se cierra la pestaña, el kernel
sigue, pero se pierde la salida. Es más seguro lanzarlo desde el terminal con
`nohup`, que sigue aunque se cierre el navegador:

```bash
cd ~/PIDS-Proyecto2/"ENTREGA 1/WEEK2"
PY=/ruta/que/dio/sys.executable
nohup "$PY" -m jupyter nbconvert --to notebook --execute train.ipynb \
      --output train_ejecutado.ipynb --ExecutePreprocessor.timeout=-1 > train.log 2>&1 &
echo $! > train.pid
```

Para seguirlo:

```bash
tail -n 5 train.log                                          # errores de arranque
cat resultados_train/faster_rcnn_v1_aug/historial.csv        # una fila por época terminada
nvidia-smi                                                   # uso de la GPU
```

`train.ipynb` guarda un checkpoint al final de cada época. Si se corta, al volver a
lanzarlo **continúa desde la última época**, no desde cero.

Para pararlo: `kill $(cat train.pid)`.

### Duración aproximada

Son 1908 imágenes de entrenamiento y 147 de validación, a 1280×720, con
`faster_rcnn_v1` y 30 épocas. Con una GPU de laboratorio habitual, cada época tarda
unos minutos, así que **hay que contar con varias horas**. Para medirlo, basta con
mirar la hora a la que se escribe la primera fila de `historial.csv`.

Si la GPU se queda sin memoria (`CUDA out of memory` en `train.log`), hay que bajar
`batch_size` en `train.ipynb` de 8 a 4 y relanzar.

## 4. Experimento sin aumento

Para medir si el aumento ayuda (T19), se entrena otra vez con `usar_aumento = False`.
Cada experimento guarda sus modelos y resultados en carpetas distintas, así que no se
pisan. **No hay que lanzar los dos a la vez**: comparten la GPU.

```bash
cd ~/PIDS-Proyecto2/"ENTREGA 1/WEEK2"
sed 's/usar_aumento = True /usar_aumento = False/' train.ipynb > train_sin_aug.ipynb
grep -c "usar_aumento = False" train_sin_aug.ipynb          # debe dar 1
nohup "$PY" -m jupyter nbconvert --to notebook --execute train_sin_aug.ipynb \
      --output train_sin_aug_ejecutado.ipynb --ExecutePreprocessor.timeout=-1 > train_sin_aug.log 2>&1 &
```

## 5. Evaluar

Cuando termine, `test.ipynb` se ejecuta desde el navegador (tarda poco):

- con `conjunto = 'val'` mientras se ajusta el modelo;
- con `conjunto = 'test'` **una sola vez al final**, para el resultado de la memoria.

## 6. Qué subir al repositorio

Sí: los notebooks ejecutados y las carpetas `resultados_train/` y `resultados_test/`,
desde la rama personal y con su PR.

No: `models/` (unos 160 MB por modelo), `data_train/`, `data_val/`, `data_test/` ni
`dataset_pids.zip`. Si hace falta conservar un modelo, se descarga y se guarda fuera
del repositorio.
