"""Prepara los audios locales del mando, sin ejecutar contenido descargado."""
import argparse
import os
import sys
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preparar_disparo import leer, guardar, recortar_silencio, FRECUENCIA
from convertir_audio import ffmpeg


def preparar(carpeta):
    fuentes = {'moonwalk': 'billie_jean.mp3', 'waka': 'waka.mp3',
               'risa': 'risa.mp3', 'motor': 'f1.mp3',
               'scar': 'scar_fuerte.wav', 'superestrella': 'superestrella.wav'}
    for nombre, archivo in fuentes.items():
        x = recortar_silencio(leer(os.path.join(carpeta, archivo)))
        if nombre == 'moonwalk':
            x = x[:round(48 * 60 / 117 * FRECUENCIA)]
        if nombre == 'motor':
            x = x[int(4.2 * FRECUENCIA):int(7.0 * FRECUENCIA)]
            n = int(.25 * FRECUENCIA)
            mezcla = np.linspace(0, 1, n)
            x = np.concatenate([x[n:-n], x[-n:] * (1-mezcla) + x[:n] * mezcla])
        elif nombre not in ('risa', 'scar'):
            n = min(int(.3 * FRECUENCIA), len(x))
            x[-n:] *= np.linspace(1, 0, n)
        destino = os.path.join(carpeta, 'mando_' + nombre)
        temporal = destino + '_entrada.wav'
        guardar(temporal, x)
        try:
            subprocess.run([ffmpeg(), '-y', '-v', 'error', '-i', temporal,
                            '-af', 'loudnorm=I=-16:TP=-1:LRA=11',
                            '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le',
                            destino + '.wav'], check=True)
            subprocess.run([ffmpeg(), '-y', '-v', 'error', '-i', destino + '.wav',
                            '-c:a', 'libvorbis', '-q:a', '5', destino + '.ogg'], check=True)
            if nombre in ('moonwalk', 'waka', 'superestrella', 'risa'):
                # El altavoz necesita un margen de arranque, como el de la SCAR.
                subprocess.run([ffmpeg(), '-y', '-v', 'error', '-i', destino + '.wav',
                                '-af', 'adelay=300', '-ac', '1', '-ar', '48000',
                                '-c:a', 'pcm_s16le', destino + '_robot.wav'], check=True)
        finally:
            os.remove(temporal)
        print(nombre, round(len(x)/FRECUENCIA, 3), 's')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('carpeta', nargs='?', default=os.path.join(os.path.dirname(__file__), 'propios'))
    preparar(p.parse_args().carpeta)
