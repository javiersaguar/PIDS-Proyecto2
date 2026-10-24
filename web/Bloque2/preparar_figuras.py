"""Actualiza las gráficas locales del Bloque 2 a partir de los CSV del proyecto.

Uso desde la raíz: python web/Bloque2/preparar_figuras.py
La página resultante también funciona abriendo index.html directamente.
"""

import json
import shutil
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parents[1]
sys.path.insert(0, str(RAIZ / 'herramientas'))
import construir_web  # noqa: E402
import construir_web_cadena  # noqa: E402


def preparar():
    figuras = {
        'epocas': construir_web.curvas_por_experimento(),
        'comparacion': construir_web.curvas_entrenamiento(),
        'grupos': construir_web.resultados_por_grupo(),
        'secuencias': construir_web.resultados_por_secuencia(),
    }
    contenido = json.dumps(figuras, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    (CARPETA / 'datos.js').write_text('window.PIDS_BLOQUE2 = ' + contenido + ';\n', encoding='utf-8')
    origen = RAIZ / 'ENTREGA 1/WEEK1/resultados_eda/interactivos/plotly.min.js'
    shutil.copyfile(origen, CARPETA / 'plotly.min.js')
    print(f'Preparadas {len(figuras)} figuras en {CARPETA}')
    construir_web_cadena.escribir()


if __name__ == '__main__':
    preparar()
