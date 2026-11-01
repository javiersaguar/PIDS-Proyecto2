"""SSD300 con 40 épocas frente a 12: pérdida y AP@0,5 por época. Uso: python figura_ssd300_40_epocas.py <repo> <salida.png>"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
R = Path(sys.argv[1]) / 'ENTREGA 1' / 'WEEK2' / 'resultados_train'
h40 = pd.read_csv(R / 'ssd_v1_aug_robusto_v1_lr001_ep40' / 'historial.csv')
h12 = pd.read_csv(R / 'ssd_v1_aug_robusto_v1_lr001' / 'historial.csv')
assert (h12.valid_map_50.values == h40.valid_map_50.values[:len(h12)]).all(), 'las 12 primeras épocas deberían coincidir'
TINTA = '#1F2937'
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#E5E7EB', 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'axes.edgecolor': '#9CA3AF', 'axes.titleweight': 'bold'})
coma = matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.2f}'.replace('.', ',') if v < 1.5 else f'{v:.1f}'.replace('.', ','))
cortes = h40.epoch[h40.lr.diff() < 0].tolist()
fig, ejes = plt.subplots(1, 2, figsize=(8.2, 2.9))
ax = ejes[0]
ax.plot(h40.epoch, h40.train_loss, color='#1F5FA8', lw=2, label='Entrenamiento')
ax.plot(h40.epoch, h40.valid_loss, color='#2A9D8F', lw=2, label='Validación')
mv = h40.valid_loss.idxmin()
ax.plot(h40.epoch[mv], h40.valid_loss[mv], 'o', color='#2A9D8F', ms=7, mec='white')
ax.annotate(f'mínimo, época {h40.epoch[mv]}', (h40.epoch[mv], h40.valid_loss[mv]), xytext=(4, -16),
            textcoords='offset points', fontsize=8, color=TINTA)
ax.set(title='Pérdida por época', xlabel='Época', ylabel='Pérdida')
ax.legend(frameon=False, fontsize=8, loc='upper right')
ax = ejes[1]
ax.plot(h40.epoch, h40.valid_map_50, color='#1F5FA8', lw=2)
b = h40.valid_map_50.idxmax()
ax.plot(h40.epoch[b], h40.valid_map_50[b], 'o', color='#1F5FA8', ms=7, mec='white')
ax.annotate(f'mejor: {h40.valid_map_50[b]:.4f} (época {h40.epoch[b]})'.replace('.', ',', 1), (h40.epoch[b], h40.valid_map_50[b]),
            xytext=(6, -22), textcoords='offset points', fontsize=8, color=TINTA)
ax.annotate(f'12 épocas: {h12.valid_map_50.max():.4f}'.replace('.', ','), (12, h12.valid_map_50.iloc[-1]),
            xytext=(-10, -40), textcoords='offset points', fontsize=8, color=TINTA,
            arrowprops=dict(arrowstyle='-', color='#6B7280', lw=0.8))
ax.set(title='AP@0,5 en validación', xlabel='Época', ylabel='AP@0,5', ylim=(0.8, 0.92))
ax.yaxis.set_major_formatter(coma)
for ax in ejes:
    ax.axvline(12, color='#6B7280', ls='--', lw=1)
    for c in cortes:
        ax.axvline(c, color='#D9692B', ls=':', lw=1)
    ax.set_xlim(0.5, 40.5)
ejes[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.1f}'.replace('.', ',')))
ejes[0].text(12.4, ejes[0].get_ylim()[1] * 0.97, 'fin con 12 épocas', fontsize=7.5, color='#4B5563', va='top')
ejes[1].text(cortes[0] + 0.4, 0.805, 'bajadas de la tasa', fontsize=7.5, color='#D9692B')
plt.tight_layout()
fig.savefig(sys.argv[2], dpi=220)
print('cortes', cortes, 'min val', h40.epoch[mv], h40.valid_loss[mv], 'best', h40.epoch[b], h40.valid_map_50[b], 'final', h40.valid_map_50.iloc[-1])
print('train 12->40', h40.train_loss[11], h40.train_loss.iloc[-1])
