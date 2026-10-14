# Entrenar en el JupyterHub del laboratorio

Guía para preparar los datos en JupyterHub y dejar el entrenamiento corriendo (T03,
T19 y T20). Comprobada el 14/10/2026 en la cuenta `pids2`.

| | En el laboratorio |
|---|---|
| Python del kernel «Python 3 (ipykernel)» | 3.11.9 (`/opt/conda/bin/python`) |
| PyTorch / torchvision / torchmetrics | 2.4.1 / 0.19.1 / 1.9.0 |
| GPU | NVIDIA GeForce RTX 3060, 12 GB |
| **Falta instalar** | **`albumentations` 1.4.18** (para `data_aug.ipynb`) y **`pycocotools`** (para el mAP de `train.ipynb` y `test.ipynb`) |

> El servicio está deshabilitado por las mañanas en horas de docencia. Conviene lanzar
> el entrenamiento por la tarde, para que no lo corten.

## 1. Instalar lo que falta (una sola vez)

Desde un terminal de JupyterHub (*File → New → Terminal*):

```bash
pip install --user "albumentations==1.4.18" pycocotools
python -c "import albumentations, pycocotools; print(albumentations.__version__)"
```

`--user` lo instala en la carpeta personal, así que se conserva entre sesiones. OpenCV
ya está instalado y no se toca.

## 2. Traer el proyecto

```bash
cd ~
git clone https://github.com/javiersaguar/PIDS-Proyecto2.git    # la primera vez
cd ~/PIDS-Proyecto2 && git pull                                  # las siguientes
```

El repositorio ya trae todo lo necesario:

- nuestras 808 imágenes anotadas (`ENTREGA 1/WEEK1/ANOTACION/`);
- los conjuntos de validación y test que da la asignatura
  (`ENTREGA 1/WEEK2/DATOS_ASIGNATURA/`), solo las imágenes con `.xml`.

## 3. Generar los conjuntos

Abrir `ENTREGA 1/WEEK1/data_aug.ipynb` y ejecutarlo entero (*Run → Run All Cells*).
Tarda unos minutos y crea en la raíz del repositorio:

| Carpeta | Contenido | Imágenes |
|---|---|---:|
| `data_train/` | Nuestros 10 vídeos tras la depuración, con sus copias `-aug` | 3184 |
| `data_val/` | Validación de la asignatura (11 secuencias de otros grupos) | 672 |
| `data_test/` | Test de la asignatura (13 secuencias de otros grupos) | 718 |

Al final, el notebook debe decir `Sin errores.` en los tres conjuntos.

Las carpetas `data_val/` y `data_test/` que hay en la raíz de la cuenta (`~/data_val`,
`~/data_test`) son las originales de la asignatura. Los notebooks no las usan: usan
las copias dentro del repositorio.

## 4. Dejar el entrenamiento corriendo

Si se ejecuta `train.ipynb` desde el navegador y se cierra la pestaña, el kernel
sigue, pero se pierde la salida. Es más seguro lanzarlo desde el terminal con
`nohup`, que sigue aunque se cierre el navegador:

```bash
cd ~/PIDS-Proyecto2/"ENTREGA 1/WEEK2"
nohup python -m jupyter nbconvert --to notebook --execute train.ipynb \
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

### Memoria y duración

- **Memoria de la GPU.** Faster R-CNN con imágenes de 1280×720 y `batch_size = 8` puede
  no caber en los 12 GB de la RTX 3060. Si `train.log` muestra `CUDA out of memory`,
  hay que bajar `batch_size` a 4 en `train.ipynb` y relanzar.
- **Duración.** Son 3184 imágenes de entrenamiento y 672 de validación por época, y
  30 épocas. Hay que contar con **varias horas**; la hora a la que se escribe la
  primera fila de `historial.csv` da la duración real de una época.

## 5. Experimento sin aumento

Para medir si el aumento ayuda (T19), se entrena otra vez con `usar_aumento = False`.
Cada experimento guarda sus modelos y resultados en carpetas distintas, así que no se
pisan. **No hay que lanzar los dos a la vez**: comparten la GPU.

```bash
cd ~/PIDS-Proyecto2/"ENTREGA 1/WEEK2"
sed 's/usar_aumento = True /usar_aumento = False/' train.ipynb > train_sin_aug.ipynb
grep -c "usar_aumento = False" train_sin_aug.ipynb          # debe dar 1
nohup python -m jupyter nbconvert --to notebook --execute train_sin_aug.ipynb \
      --output train_sin_aug_ejecutado.ipynb --ExecutePreprocessor.timeout=-1 > train_sin_aug.log 2>&1 &
```

## 6. Evaluar

Cuando termine, `test.ipynb` se ejecuta desde el navegador (tarda poco):

- con `conjunto = 'val'` mientras se ajusta el modelo;
- con `conjunto = 'test'` **una sola vez al final**, para el resultado de la memoria.

## 7. Qué subir al repositorio

Sí: los notebooks ejecutados y las carpetas `resultados_train/` y `resultados_test/`,
desde la rama personal y con su PR.

No: `models/` (unos 160 MB por modelo), `data_train/`, `data_val/`, `data_test/` ni
`dataset_pids.zip`. Para la demo (`ENTREGA 2/WEEK3`) hay que descargar
`models/<experimento>/model_best.pt` y guardarlo fuera del repositorio.
