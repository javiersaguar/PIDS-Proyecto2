"""Figura del recorrido de la demo del Bloque 3, a partir de circuito.PARADAS y circuito.RIVALES.

Dibuja sobre el plano (origen en la salida, x a la derecha, y hacia abajo):
- el camino del chasis, con la longitud y la velocidad de cada tramo;
- los tramos en los que se ataca en marcha;
- dónde va cada rival, la distancia a la que queda de nuestro robot y, para el rival 2, el
  tramo que recorre mientras nuestro robot le dispara.

    python herramientas/figura_circuito.py docs/informes/figuras/circuito_demo.png

Se ejecuta con el entorno de ENTREGA 2/WEEK3 (necesita circuito.py y recorrido.py).
"""

import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'ENTREGA 2', 'WEEK3'))
import circuito as C  # noqa: E402
from recorrido import aplicar, movimiento  # noqa: E402

TINTA, SECUNDARIA, REJILLA = '#1f2933', '#52606d', '#d9dee3'
CAMINO, ATAQUE, RIVAL, TIRO = '#3a6ea5', '#c2410c', '#7f1d1d', '#b91c1c'
LARGO_ROBOT, ANCHO_ROBOT = 0.32, 0.24      # m, RoboMaster EP visto desde arriba

# Dónde va el texto de cada tramo (por orden): desplazamiento (dx, dy) desde su punto medio,
# alineación y giro. Sin entrada, encima del tramo. Los tramos verticales llevan el texto en dos líneas.
ETIQUETAS = {
    0: (0.0, -0.14, 'center', 0),       # recta de salida, encima
    1: (0.2, -0.14, 'center', 0),       # 3.1, encima
    2: (-0.08, 0.0, 'right', 0),        # 3.2, a su izquierda
    3: (-0.12, -0.14, 'center', 0),     # 3.3 (ataque), encima
    4: (-0.08, 0.0, 'right', 0),        # 3.4, a su izquierda
    5: (0.05, 0.17, 'center', 0),       # 4.1, debajo
    6: (0.08, 0.0, 'left', 0),          # 4.2, a su derecha
    7: (0.0, 0.17, 'center', 0),        # 4.3 (ataque), debajo
}


def num(v, decimales=2):
    """Número con coma decimal y sin ceros sobrantes: 2.50 -> '2,5'."""
    texto = f'{v:.{decimales}f}'
    if '.' in texto:
        texto = texto.rstrip('0').rstrip('.')
    return texto.replace('.', ',').replace('-', '−')


def robot(ax, x, y, color, rumbo=0.0, alfa=1.0, borde=None):
    """Rectángulo del tamaño de un RoboMaster en (x, y), orientado con `rumbo` (grados)."""
    horizontal = abs(math.cos(math.radians(rumbo))) > 0.5
    largo, ancho = (LARGO_ROBOT, ANCHO_ROBOT) if horizontal else (ANCHO_ROBOT, LARGO_ROBOT)
    ax.add_patch(FancyBboxPatch((x - largo / 2, y - ancho / 2), largo, ancho,
                                boxstyle='round,pad=0,rounding_size=0.04', facecolor=color, alpha=alfa,
                                edgecolor=borde or color, lw=1.2 if borde else 0, zorder=6))


def cota(ax, a, b, texto, lado=(0.0, 0.0), ha='center'):
    """Línea de tiro discontinua de `a` a `b` con su distancia."""
    ax.plot([a[0], b[0]], [a[1], b[1]], color=TIRO, lw=1.2, ls=(0, (4, 2)), zorder=2)
    medio = ((a[0] + b[0]) / 2 + lado[0], (a[1] + b[1]) / 2 + lado[1])
    ax.text(*medio, texto, color=TIRO, fontsize=7.5, ha=ha, va='center', zorder=7,
            bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))


def main(salida):
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=200)
    punto, rumbo = (0.0, 0.0), float(C.RUMBO_INICIAL)
    ataques = {}            # nombre del rival -> (inicio, fin) del tramo desde el que se le ataca
    i = 0
    for p in C.PARADAS:
        for m in p['movimientos']:
            x, y, z, op = movimiento(m)
            nuevo, nuevo_rumbo = aplicar(punto, rumbo, x, y, z)
            ataque = op.get('atacar') is not None
            ax.annotate('', xy=nuevo, xytext=punto, zorder=3,
                        arrowprops=dict(arrowstyle='-|>', color=ATAQUE if ataque else CAMINO,
                                        lw=3 if ataque else 2, shrinkA=0, shrinkB=0))
            largo = math.hypot(x, y)
            if largo > 0:
                v = op.get('velocidad', C.VELOCIDAD_XY)
                dx, dy, ha, giro = ETIQUETAS.get(i, (0.0, -0.14, 'center', 0))
                medio = ((punto[0] + nuevo[0]) / 2 + dx, (punto[1] + nuevo[1]) / 2 + dy)
                separador = '\n' if abs(nuevo[0] - punto[0]) < 1e-6 else ' · '
                ax.text(*medio, f'{num(largo)} m{separador}{num(v)} m/s', fontsize=7.5, ha=ha, va='center',
                        rotation=giro, color=ATAQUE if ataque else CAMINO, fontweight='bold' if ataque else 'normal', zorder=7,
                        bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.85))
                i += 1
            if ataque and op.get('rival'):
                ataques[op['rival']] = (punto, nuevo)
            punto, rumbo = nuevo, nuevo_rumbo
        if p['barrido']:
            ataques.setdefault('P1', punto)
            ax.plot(*punto, 's', color=TINTA, ms=8, zorder=5)
            ax.text(punto[0] - 0.12, punto[1] + 0.14, f'{p["nombre"]} ({num(punto[0])}; {num(punto[1])})',
                    fontsize=8.5, color=TINTA, ha='right', va='top', fontweight='bold')

    ax.plot(0, 0, 'o', color=TINTA, ms=7, zorder=5)
    ax.text(0, 0.16, 'salida (0; 0)', fontsize=8.5, color=TINTA, ha='center', va='top')
    ax.plot(*punto, 'o', color=TINTA, ms=7, zorder=5)
    ax.text(punto[0] + 0.15, punto[1], f'baile final\n({num(punto[0])}; {num(punto[1])})', fontsize=8.5,
            color=TINTA, ha='left', va='center')

    # Rivales
    rivales = getattr(C, 'RIVALES', {})
    p1 = ataques.get('P1', (0.0, 0.0))
    for nombre, r in rivales.items():
        x, y = r['punto']
        if r.get('hasta') is not None:
            hx, hy = r['hasta']
            robot(ax, hx, hy, RIVAL, alfa=0.25, borde=RIVAL)
            ax.annotate('', xy=(hx + 0.18, hy), xytext=(x - 0.18, y), zorder=6,
                        arrowprops=dict(arrowstyle='-|>', color=RIVAL, lw=1.6))
            ax.text((x + hx) / 2, y - 0.2, f'{nombre}: {num(math.hypot(hx - x, hy - y))} m a '
                    f'{num(r["velocidad"])} m/s', fontsize=8, color=RIVAL, ha='center', va='bottom')
            ax.text(x + 0.2, y, f'({num(x)}; {num(y)})', fontsize=6.5, color=SECUNDARIA, ha='left', va='center')
            ax.text(hx - 0.2, hy, f'({num(hx)}; {num(hy)})', fontsize=6.5, color=SECUNDARIA, ha='right',
                    va='center')
        robot(ax, x, y, RIVAL)
        if nombre in ataques:
            (ax0, ay0), (ax1, ay1) = ataques[nombre]
            if r.get('hasta') is not None:
                # Distancia lateral entre el retroceso de nuestro robot y el camino del rival
                cota(ax, (x, ay0), (x, y + ANCHO_ROBOT / 2), f'{num(abs(y - ay0))} m',
                     lado=(0.08, 0.0), ha='left')
            else:
                cerca, lejos = math.hypot(x - ax0, y - ay0), math.hypot(x - ax1, y - ay1)
                cota(ax, (ax0, ay0), (x + LARGO_ROBOT / 2, y), f'{num(cerca)} m', lado=(0.0, -0.13))
                alto = f'\nen alto ({num(r["alto"] * 100, 0)} cm)' if r.get('alto') else ''
                ax.text(x, y + 0.18, f'{nombre} ({num(x)}; {num(y)}){alto}', fontsize=8, color=RIVAL,
                        ha='center', va='top', linespacing=1.1)
                ax.text((ax0 + ax1) / 2, ay1 - 0.15, f'se aleja de {num(cerca)} a {num(lejos)} m',
                        fontsize=7.5, color=TIRO, ha='center', va='bottom')
        else:
            d = math.hypot(x - p1[0], y - p1[1])
            cota(ax, p1, (x, y), f'{num(d)} m', lado=(-0.08, 0.0), ha='right')
            arriba = y < p1[1]
            ax.text(x, y - 0.22 if arriba else y + 0.22, f'{nombre} ({num(x)}; {num(y)})', fontsize=8,
                    color=RIVAL, ha='center', va='bottom' if arriba else 'top')

    ax.plot([], [], color=CAMINO, lw=2, label='desplazamiento')
    ax.plot([], [], color=ATAQUE, lw=3, label='ataque en marcha')
    ax.plot([], [], 's', color=RIVAL, ms=7, label='rival')
    ax.plot([], [], color=RIVAL, lw=1.6, label='movimiento del rival 2')
    ax.plot([], [], color=TIRO, lw=1.2, ls=(0, (4, 2)), label='distancia de tiro')
    ax.legend(loc='lower right', fontsize=7.5, frameon=False, ncol=1)
    ax.set_aspect('equal')
    ax.invert_yaxis()                      # y hacia abajo, como en el boceto del circuito
    ax.set_xlim(-0.6, 8.9)
    ax.set_ylim(1.75, -2.75)
    ax.set_xlabel('x (m)', color=SECUNDARIA, fontsize=9)
    ax.set_ylabel('y (m)', color=SECUNDARIA, fontsize=9)
    ax.tick_params(colors=SECUNDARIA, labelsize=8)
    ax.grid(color=REJILLA, lw=0.6)
    for lado in ax.spines.values():
        lado.set_color(REJILLA)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    fig.savefig(salida, facecolor='white')
    print(f'Creada {salida}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python herramientas/figura_circuito.py <salida.png>')
    main(sys.argv[1])
