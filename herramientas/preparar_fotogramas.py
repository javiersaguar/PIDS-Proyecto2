"""Extrae los vídeos comprimidos en cinco lotes y registra su procedencia.

Desde la raíz del repositorio:
    python herramientas/preparar_fotogramas.py

Requiere opencv-python. No sobrescribe un destino existente ni crea etiquetas.
Los MP4 se leen desde una carpeta temporal, sin versionarlos descomprimidos.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

import cv2


RAIZ = Path(__file__).resolve().parents[1]
LOTES = [
    ("A_javier-saguar", "Javier Saguar", (1, 2)),
    ("B_alejandro-cuevas", "Alejandro Cuevas", (3, 4)),
    ("C_monica-fernandez", "Mónica Fernández", (5, 6)),
    ("D_pedro-orrego", "Pedro José Orrego", (7, 8)),
    ("E_daniel-naval", "Daniel Naval", (9, 10)),
]


def sha256(ruta):
    resumen = hashlib.sha256()
    with ruta.open("rb") as fichero:
        for bloque in iter(lambda: fichero.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def extraer_video(ruta_zip, destino, intervalo, lote, responsable):
    """Muestrea frames numerados desde 1, como video2frames.ipynb."""
    secuencia = ruta_zip.stem
    imagenes = destino / lote / secuencia / "images"
    etiquetas = imagenes.parent / "labels"
    imagenes.mkdir(parents=True)
    etiquetas.mkdir()
    (etiquetas / ".gitkeep").touch()
    registros = []
    with tempfile.TemporaryDirectory(prefix="pids_video_") as temporal:
        with zipfile.ZipFile(ruta_zip) as archivo:
            videos = [e for e in archivo.infolist()
                      if not e.is_dir() and Path(e.filename).suffix.lower() in (".mp4", ".avi", ".mov", ".mkv")]
            if len(videos) != 1:
                raise ValueError(f"{ruta_zip.name}: se esperaba exactamente un vídeo")
            ruta_video = Path(temporal) / Path(videos[0].filename).name
            with archivo.open(videos[0]) as entrada, ruta_video.open("wb") as salida:
                shutil.copyfileobj(entrada, salida)
        cap = cv2.VideoCapture(str(ruta_video))
        if not cap.isOpened():
            raise ValueError(f"No se puede abrir {ruta_zip.name}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        anunciados = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if fps <= 0 or ancho <= 0 or alto <= 0:
            cap.release()
            raise ValueError(f"Metadatos inválidos en {ruta_zip.name}")
        numero = 0
        try:
            while True:
                ok, imagen = cap.read()
                if not ok:
                    break
                numero += 1
                if imagen.shape[:2] != (alto, ancho):
                    raise ValueError(f"Resolución cambiante en {secuencia}, frame {numero}")
                if numero % intervalo:
                    continue
                ruta = imagenes / f"frame_{numero:04d}.jpg"
                if not cv2.imwrite(str(ruta), imagen, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    raise OSError(f"No se ha guardado {ruta}")
                registros.append({
                    "lote": lote, "responsable": responsable, "video": secuencia,
                    "frame": numero, "segundo": f"{(numero - 1) / fps:.6f}",
                    "ruta": ruta.relative_to(destino).as_posix(),
                    "bytes": ruta.stat().st_size, "sha256": sha256(ruta),
                })
        finally:
            cap.release()
    if numero != anunciados:
        raise ValueError(f"{secuencia}: se decodificaron {numero} de {anunciados} fotogramas")
    resumen = {
        "video": secuencia, "zip": ruta_zip.name, "zip_sha256": sha256(ruta_zip),
        "lote": lote, "responsable": responsable, "ancho": ancho, "alto": alto,
        "fps": fps, "fotogramas": numero, "duracion_s": numero / fps,
        "intervalo": intervalo, "imagenes": len(registros),
    }
    print(f"{secuencia}: {numero} frames -> {len(registros)} imágenes ({lote})", flush=True)
    return resumen, registros


def preparar(origen, destino, intervalo=24):
    if intervalo < 1:
        raise ValueError("El intervalo debe ser mayor que cero")
    archivos = [origen / f"ROBOMASTER_VIDEO_{n:02d}.zip" for n in range(1, 11)]
    if not all(p.is_file() for p in archivos):
        raise FileNotFoundError("Falta alguno de los diez ZIP de ROBOMASTER_VIDEO_01 a 10")
    if destino.exists():
        raise FileExistsError(f"El destino ya existe: {destino}. Elige una carpeta nueva para no pisar anotaciones.")
    destino.mkdir(parents=True)
    resumenes, registros = [], []
    for lote, responsable, numeros in LOTES:
        for numero in numeros:
            resumen, filas = extraer_video(archivos[numero - 1], destino, intervalo, lote, responsable)
            resumenes.append(resumen)
            registros.extend(filas)
    with (destino / "manifest.csv").open("w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(registros[0]))
        escritor.writeheader()
        escritor.writerows(registros)
    (destino / "videos.json").write_text(
        json.dumps({"intervalo": intervalo, "calidad_jpeg": 95,
                    "opencv": cv2.__version__, "videos": resumenes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"TOTAL: {len(registros)} imágenes, {sum(r['bytes'] for r in registros) / 1024**2:.1f} MiB")
    return resumenes, registros


def comprobar(destino, origen=None):
    """Comprueba integridad, resolución, numeración y cobertura de los diez vídeos."""
    destino = destino.resolve()
    metadata = json.loads((destino / "videos.json").read_text(encoding="utf-8"))
    with (destino / "manifest.csv").open(encoding="utf-8", newline="") as fichero:
        registros = list(csv.DictReader(fichero))
    if len(metadata['videos']) != 10 or len({v['video'] for v in metadata['videos']}) != 10:
        raise ValueError("Se esperaban diez vídeos distintos")
    rutas = set()
    for video in metadata["videos"]:
        filas = [r for r in registros if r["video"] == video["video"]]
        esperados = list(range(video["intervalo"], video["fotogramas"] + 1, video["intervalo"]))
        if [int(r["frame"]) for r in filas] != esperados or len(filas) != video["imagenes"]:
            raise ValueError(f"Muestreo incompleto de {video['video']}")
        if origen is not None and sha256(origen / video["zip"]) != video["zip_sha256"]:
            raise ValueError(f"Ha cambiado el ZIP original de {video['video']}")
        secuencia = destino / video["lote"] / video["video"]
        if not (secuencia / "labels").is_dir():
            raise ValueError(f"Falta labels/ en {video['video']}")
        if {p.name for p in (secuencia / "images").glob("*.jpg")} != {Path(r["ruta"]).name for r in filas}:
            raise ValueError(f"Hay imágenes adicionales o ausentes en {video['video']}")
        for fila in filas:
            ruta = (destino / fila["ruta"]).resolve()
            if destino not in ruta.parents or fila["ruta"] in rutas:
                raise ValueError(f"Ruta inválida o duplicada: {fila['ruta']}")
            rutas.add(fila["ruta"])
            if fila["lote"] != video["lote"] or fila["responsable"] != video["responsable"]:
                raise ValueError(f"Asignación inconsistente: {fila['ruta']}")
            if ruta.stat().st_size != int(fila["bytes"]) or sha256(ruta) != fila["sha256"]:
                raise ValueError(f"Imagen modificada o incompleta: {fila['ruta']}")
            imagen = cv2.imread(str(ruta))
            if imagen is None or imagen.shape != (video["alto"], video["ancho"], 3):
                raise ValueError(f"JPEG inválido o resolución incorrecta: {fila['ruta']}")
    if len(rutas) != len(registros):
        raise ValueError("El manifiesto contiene filas de vídeos desconocidos")
    print(f"Verificadas {len(registros)} imágenes de diez vídeos: SHA-256, muestreo y resolución correctos.")
    return metadata["videos"], registros


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", type=Path, default=RAIZ / "ENTREGA 1/WEEK1/DATASET PIDS")
    parser.add_argument("--destino", type=Path, default=RAIZ / "ENTREGA 1/WEEK1/ANOTACION")
    parser.add_argument("--intervalo", type=int, default=24)
    args = parser.parse_args()
    preparar(args.origen.resolve(), args.destino.resolve(), args.intervalo)
