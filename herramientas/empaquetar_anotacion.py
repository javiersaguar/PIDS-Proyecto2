"""Crea un ZIP con data_train/<vídeo>/{images,labels}, listo para JupyterHub.

    python herramientas/empaquetar_anotacion.py salida.zip
    python herramientas/empaquetar_anotacion.py salida.zip --lote A_javier-saguar

No modifica los originales ni sobrescribe un ZIP existente. Incluye los XML que
ya se hayan anotado; nunca genera etiquetas vacías para imágenes sin revisar.
"""

import argparse
from pathlib import Path
import zipfile

from preparar_fotogramas import RAIZ, LOTES, comprobar


def empaquetar(destino, lote=None):
    datos = RAIZ / "ENTREGA 1/WEEK1/ANOTACION"
    resumenes, _ = comprobar(datos)
    if lote is not None and lote not in {l[0] for l in LOTES}:
        raise ValueError(f"Lote desconocido: {lote}")
    if destino.exists():
        raise FileExistsError(f"Ya existe {destino}; elige otro nombre")
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagenes = etiquetas = 0
    with zipfile.ZipFile(destino, "x", compression=zipfile.ZIP_DEFLATED) as archivo:
        for video in resumenes:
            if lote is not None and video["lote"] != lote:
                continue
            secuencia = datos / video["lote"] / video["video"]
            for subcarpeta, extension in (("images", "*.jpg"), ("labels", "*.xml")):
                archivo.writestr(f"data_train/{video['video']}/{subcarpeta}/", b"")
                for ruta in sorted((secuencia / subcarpeta).glob(extension)):
                    archivo.write(ruta, f"data_train/{video['video']}/{subcarpeta}/{ruta.name}")
                    imagenes += subcarpeta == "images"
                    etiquetas += subcarpeta == "labels"
    print(f"{destino}: {imagenes} imágenes, {etiquetas} XML, {destino.stat().st_size / 1024**2:.1f} MiB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destino", type=Path)
    parser.add_argument("--lote", choices=[l[0] for l in LOTES])
    args = parser.parse_args()
    empaquetar(args.destino.resolve(), args.lote)
