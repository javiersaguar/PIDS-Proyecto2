"""Figura del recorrido de la demo del Bloque 3, a partir de circuito.PARADAS.

Dibuja el camino del chasis sobre el plano (origen en la salida, x a la derecha, y hacia
abajo), las paradas, los tramos en los que se ataca en marcha y hacia dónde apunta la
torreta en cada ataque. Las posiciones de los rivales aún no están medidas: solo se
dibuja la dirección de la torreta.

    python herramientas/figura_circuito.py docs/informes/figuras/circuito_demo.png

Se ejecuta con el entorno de ENTREGA 2/WEEK3 (necesita circuito.py y recorrido.py).
"""

import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'ENTREGA 2', 'WEEK3'))
import circuito as C  # noqa: E402
from recorrido import aplicar, movimiento  # noqa: E402

TINTA, SECUNDARIA, REJILLA = '#1f2933', '#52606d', '#d9dee3'
CAMINO, ATAQUE, TORRETA = '#3a6ea5', '#c2410c', '#b91c1c'


def flecha(ax, x, y, rumbo, largo, texto, lado=1, rumbo_camino=None):
    r = math.radians(rumbo)
    dx, dy = largo * math.cos(r), largo * math.sin(r)
    if rumbo_camino is not None and abs(math.sin(math.radians(rumbo - rumbo_camino))) < 0.3:
        # La torreta apunta a lo largo del camino: la flecha va a un lado, por encima
        y -= 0.25
        ax.text(x + dx / 2, y - 0.3, texto, color=TINTA, fontsize=8.5, ha='center', va='center')
    else:
        ax.text(x + dx * 1.08, y + dy * 1.08 + 0.12 * lado, texto, color=TINTA, fontsize=8.5,
                ha='center', va='center')
    ax.annotate('', xy=(x + dx, y + dy), xytext=(x, y),
                arrowprops=dict(arrowstyle='-|>', color=TORRETA, lw=1.6, linestyle=(0, (4, 2))))


def main(salida):
    fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=200)
    punto, rumbo = (0.0, 0.0), float(C.RUMBO_INICIAL)
    ax.plot(*punto, 'o', color=TINTA, ms=7, zorder=5)
    ax.text(punto[0] - 0.1, punto[1] + 0.3, 'salida', fontsize=9, color=TINTA, ha='center')
    rivales = 0
    for p in C.PARADAS:
        for m in p['movimientos']:
            x, y, z, op = movimiento(m)
            nuevo, nuevo_rumbo = aplicar(punto, rumbo, x, y, z)
            ataque = op.get('atacar') is not None
            ax.annotate('', xy=nuevo, xytext=punto, zorder=3,
                        arrowprops=dict(arrowstyle='-|>', color=ATAQUE if ataque else CAMINO,
                                        lw=3 if ataque else 2, shrinkA=0, shrinkB=0))
            if ataque:
                rivales += 1
                medio = ((punto[0] + nuevo[0]) / 2, (punto[1] + nuevo[1]) / 2)
                alto = ' en alto' if op.get('pitch') else ''
                rumbo_camino = math.degrees(math.atan2(nuevo[1] - punto[1], nuevo[0] - punto[0]))
                flecha(ax, *medio, rumbo + op['atacar'], 0.9, f'rival {rivales}{alto}\n(en marcha)',
                       lado=-1 if math.sin(math.radians(rumbo + op['atacar'])) < 0 else 1,
                       rumbo_camino=rumbo_camino)
            punto, rumbo = nuevo, nuevo_rumbo
        if p['barrido']:
            ax.plot(*punto, 's', color=TINTA, ms=8, zorder=5)
            ax.text(punto[0] - 0.3, punto[1] - 0.15, p['nombre'], fontsize=9, color=TINTA, ha='center',
                    fontweight='bold')
            # Las dos primeras direcciones del barrido: el rival de la derecha y el camuflado
            for yaw, texto in zip(p['barrido'][:p.get('objetivos') or 1], ('rival 1', 'robot\ncamuflado')):
                flecha(ax, *punto, rumbo + yaw, 0.9, texto, lado=1 if yaw > 0 else -1)
                if texto == 'rival 1':
                    rivales = 1
    ax.plot(*punto, 'o', color=TINTA, ms=7, zorder=5)
    ax.text(punto[0] + 0.15, punto[1] + 0.3, 'baile final', fontsize=9, color=TINTA, ha='center')

    ax.plot([], [], color=CAMINO, lw=2, label='desplazamiento (hasta 0,5 m/s)')
    ax.plot([], [], color=ATAQUE, lw=3, label='ataque en marcha (0,1 m/s)')
    ax.plot([], [], color=TORRETA, lw=1.6, ls=(0, (4, 2)), label='dirección de la torreta')
    ax.legend(loc='lower right', fontsize=8, frameon=False)
    ax.set_aspect('equal')
    ax.invert_yaxis()                      # y hacia abajo, como en el boceto del circuito
    ax.set_xlim(-0.6, 8.8)
    ax.set_ylim(1.3, -2.1)
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
