from pathlib import Path
import csv
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import numpy as np
from PIL import Image

repo=Path(__file__).resolve().parents[1]
out=repo/'docs/informes/figuras';out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                    'axes.spines.right':False,'axes.axisbelow':True,'grid.alpha':0.18})
imagenes=[];cajas=[]
for carpeta in sorted((repo/'ENTREGA 1/WEEK1/ANOTACION').glob('*/*')):
 if not (carpeta/'images').is_dir() or 'calibracion' in carpeta.parts:continue
 sec='V'+carpeta.name[-2:]
 for p in sorted((carpeta/'images').glob('*.jpg')):
  labs=[]
  for o in ET.parse(carpeta/'labels'/(p.stem+'.xml')).getroot().iter('object'):
   b=o.find('bndbox');v={c.tag:float(c.text) for c in b};v.update(sec=sec,difficult=int(o.findtext('difficult','0')))
   labs.append(v);cajas.append(v)
  imagenes.append(dict(sec=sec,frame=int(p.stem.split('_')[-1]),ruta=p,cajas=labs))
assert len(imagenes)==808 and len(cajas)==1420

def guardar(fig,nombre):
 fig.savefig(out/(nombre+'.png'),dpi=240,bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7,2.7),constrained_layout=True)
for ax,sec in zip(axes,['V02','V04']):
 m=max((m for m in imagenes if m['sec']==sec),key=lambda m:len(m['cajas']))
 ax.imshow(Image.open(m['ruta']))
 for c in m['cajas']:
  ax.add_patch(Rectangle((c['xmin'],c['ymin']),c['xmax']-c['xmin'],c['ymax']-c['ymin'],fill=False,
                         lw=1.4,edgecolor='#D35C24' if c['difficult'] else '#2466A0'))
 ax.axis('off');ax.set_title(sec+'  '+m['ruta'].stem,fontsize=10)
guardar(fig,'anotaciones')

secs=[f'V{i:02d}' for i in range(1,11)]
fig,axes=plt.subplots(1,2,figsize=(7,2.6),constrained_layout=True)
for ax,k,title in zip(axes,['robots','difficult'],['Robots anotados por vídeo','Proporción de difficult']):
 vals=[sum(c['sec']==s and (k=='robots' or c['difficult']) for c in cajas) for s in secs]
 if k=='difficult': vals=[100*v/sum(c['sec']==s for c in cajas) for s,v in zip(secs,vals)]
 ax.bar(secs,vals,color='#2C6188' if k=='robots' else '#D27531');ax.tick_params(axis='x',rotation=45,labelsize=8)
 ax.set_title(title,fontsize=10);ax.set_ylabel('Cajas' if k=='robots' else 'Porcentaje');ax.grid(axis='y')
guardar(fig,'inventario')

areas=np.array([(c['xmax']-c['xmin'])*(c['ymax']-c['ymin']) for c in cajas])/1000
aspect=np.array([(c['xmax']-c['xmin'])/(c['ymax']-c['ymin']) for c in cajas])
fig,axes=plt.subplots(1,2,figsize=(7,2.7),constrained_layout=True)
axes[0].hist(areas,bins=np.geomspace(areas.min(),areas.max(),23),color='#2C6188');axes[0].set_xscale('log');axes[0].set_xlabel('Área de caja en miles de píxeles²');axes[0].set_ylabel('Cajas');axes[0].set_title('Tamaños heterogéneos',fontsize=10)
axes[1].hist(aspect,bins=np.linspace(0.3,2.5,26),color='#D27531');axes[1].axvline(np.median(aspect),color='#333',ls='--');axes[1].set_xlabel('Ancho / alto');axes[1].set_ylabel('Cajas');axes[1].set_title('Aspecto mediano 1,11',fontsize=10)
guardar(fig,'tamano_forma')

with (repo/'ENTREGA 1/WEEK1/resultados_eda/metricas_imagenes.csv').open(encoding='utf8') as f:metricas=list(csv.DictReader(f))
fig,axes=plt.subplots(1,2,figsize=(7,2.7),constrained_layout=True)
for ax,k,title in zip(axes,['brillo','contraste'],['Brillo medio en escala de grises','Contraste en escala de grises']):
 datos=[[float(r[k]) for r in metricas if r['secuencia']==s] for s in secs]
 ax.boxplot(datos,tick_labels=secs,showfliers=False);ax.tick_params(axis='x',rotation=45,labelsize=8)
 ax.set_title(title,fontsize=9);ax.set_ylabel('Intensidad 0 a 255' if k=='brillo' else 'Desviación típica');ax.grid(axis='y')
guardar(fig,'iluminacion')

from matplotlib.colors import LinearSegmentedColormap
gamma=.4;paleta=[[0,'#FFFFFF'],[.2,'#FFE49A'],[.45,'#FDB44B'],[.7,'#F06724'],[1,'#9F2717']]
cmap=LinearSegmentedColormap.from_list('calido',[(p**(1/gamma),c) for p,c in paleta],N=1024)
mapas={}
for s in secs:
 denom=sum(m['sec']==s for m in imagenes)
 for grupo in ['todos','difficult']:
  cs=[c for c in cajas if c['sec']==s and (grupo=='todos' or c['difficult'])]
  mapas[s,grupo]=np.histogram2d([(c['ymin']+c['ymax'])/1440 for c in cs],[(c['xmin']+c['xmax'])/2560 for c in cs],bins=(9,16),range=[[0,1],[0,1]])[0]*100/denom
vmax=max(m.max() for m in mapas.values())
fig,axes=plt.subplots(2,2,figsize=(7,4.6),constrained_layout=True)
for row,s in enumerate(['V04','V06']):
 for col,g in enumerate(['todos','difficult']):
  ax=axes[row,col];im=ax.imshow(mapas[s,g],cmap=cmap,vmin=0,vmax=vmax,extent=[0,1,1,0],aspect=720/1280)
  ax.set_title(s+'  '+g,fontsize=10);ax.set_xlabel('Posición horizontal');ax.set_ylabel('Posición vertical')
fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.85,label='Centros por 100 imágenes  color no lineal')
guardar(fig,'mapas_seleccionados')

fig,axes=plt.subplots(1,2,figsize=(7,2.65),constrained_layout=True)
for ax,s in zip(axes,['V05','V06']):
 ms=[m for m in imagenes if m['sec']==s];x=[m['frame']/30.303 for m in ms];y=[len(m['cajas']) for m in ms]
 ax.step(x,y,where='mid',color='#2C6188',lw=1.2);ax.axhline(np.mean(y),color='#C16B2E',ls='--',label=f'Media {np.mean(y):.2f}')
 ax.set_title(s,fontsize=10);ax.set_xlabel('Tiempo desde inicio en segundos');ax.set_ylabel('Robots anotados');ax.set_ylim(-.1,3.2);ax.set_yticks(range(4));ax.legend(frameon=False,fontsize=8);ax.grid()
guardar(fig,'recuentos_temporales')

p=repo/'ENTREGA 1/WEEK1/resultados_aug/ejemplos_aumento.jpg';im=Image.open(p);im.crop((0,0,im.width//2,im.height//6)).save(out/'ejemplo_aumento.png')

fig,ax=plt.subplots(figsize=(7,3.7),constrained_layout=True)
ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
boxes=[(0.1,3.2,2.4,1.1,'JPEG y XML\noriginales y aumentos'),(3.6,3.2,2.4,1.1,'DataLoader\n8 imágenes por lote'),(7.1,3.2,2.7,1.1,'Faster R CNN\nResNet 50 y FPN'),(7.1,0.7,2.7,1.1,'Pérdidas RPN\ny clasificación y cajas'),(3.6,0.7,2.4,1.1,'Gradientes y SGD\nactualización de pesos'),(0.1,0.7,2.4,1.1,'Validación por época\nAP y checkpoint mejor')]
for x,y,w,h,t in boxes:
 ax.add_patch(Rectangle((x,y),w,h,fc='#EDF2F7',ec='#50728B',lw=1.1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=9)
for a,b in [((2.5,3.75),(3.6,3.75)),((6,3.75),(7.1,3.75)),((8.45,3.2),(8.45,1.8)),((7.1,1.25),(6,1.25)),((3.6,1.25),(2.5,1.25))]:
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,color='#50728B'))
ax.text(5,4.8,'Entrenamiento y selección con conjuntos separados',ha='center',fontsize=12,fontweight='bold')
guardar(fig,'pipeline')

p=repo/'ENTREGA 1/WEEK2/DATOS_ASIGNATURA/data_val/PIDS2024_GR02_0001/images/frame_0444.jpg'
fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True);ax.imshow(Image.open(p));ax.axis('off')
lab=p.parent.parent/'labels/frame_0444.xml'
for o in ET.parse(lab).getroot().iter('object'):
 b=o.find('bndbox');v={c.tag:float(c.text) for c in b};ax.add_patch(Rectangle((v['xmin'],v['ymin']),v['xmax']-v['xmin'],v['ymax']-v['ymin'],fill=False,ec='#1F82B0',lw=2))
ax.set_title('GR02 0001  frame 0444  una caja XML y cuatro robots visibles',fontsize=10)
guardar(fig,'etiqueta_incompleta')
for name in ['peores','al_azar']:
 p=repo/f'ENTREGA 1/WEEK2/resultados_test/faster_rcnn_v1_aug_lr001_val/ejemplos_{name}.jpg';im=Image.open(p)
 # Una muestra del mosaico para conservar legibilidad dentro de la memoria.
 im.crop((0,0,im.width//3,im.height//2)).save(out/('caso_'+name+'.png'))
print('Figuras preparadas',len(list(out.glob('*.png'))))
