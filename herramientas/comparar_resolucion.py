"""Compara dos evaluaciones existentes de validación sin ejecutar modelos."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parents[1] / 'ENTREGA 1/WEEK2'
DESTINO = BASE / 'comparaciones/res1024'
EXPERIMENTOS = ['faster_rcnn_v1_aug_lr001', 'faster_rcnn_v1_aug_lr001_res1024']


def leer_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def generar():
    DESTINO.mkdir(parents=True, exist_ok=True)
    historias = [leer_csv(BASE/'resultados_train'/e/'historial.csv') for e in EXPERIMENTOS]
    resumenes = [json.loads((BASE/'resultados_test'/(e+'_val')/'resumen.json').read_text(encoding='utf-8')) for e in EXPERIMENTOS]
    mapas = [{r['grupo']: r for r in s['map']} for s in resumenes]
    videos = [{r['grupo']: r for r in s['por_video']} for s in resumenes]
    assert all([int(r['epoch']) for r in h] == list(range(1,31)) for h in historias)
    assert set(videos[0]) == set(videos[1])
    for grupo in videos[0]:
        for k in ['imagenes','robots','robots_normales','robots_difficult']:
            assert videos[0][grupo][k] == videos[1][grupo][k], (grupo,k)
    for s in resumenes:
        assert s['conjunto']=='val' and s['score_threshold']==s['iou_threshold']==0.5
        assert sum(r['fp'] for r in s['por_video'][1:])==s['por_video'][0]['fp']
        assert sum(r['fn'] for r in s['por_video'][1:])==s['por_video'][0]['fn']
    filas=[]
    for grupo in ['todos','normales','difficult']:
        for k in ['map_50','map','map_75','map_small','map_medium','map_large']:
            a,b=[m[grupo][k] for m in mapas]
            filas.append(dict(grupo=grupo,metrica=k,res800=a,res1024=b,diferencia_puntos=round(100*(b-a),4)))
    secuencias=[]
    for grupo in videos[0]:
        a,b=[v[grupo] for v in videos]
        row=dict(secuencia=grupo)
        for k in ['map_50','map','map_50_difficult','fp','fn','fn_difficult']:
            row[k+'_res800']=a[k];row[k+'_res1024']=b[k]
        row['diferencia_ap50_puntos']=round(100*(b['map_50']-a['map_50']),4)
        secuencias.append(row)
    for name,datos in [('metricas_comparadas.csv',filas),('secuencias_comparadas.csv',secuencias)]:
        with (DESTINO/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(datos[0]));w.writeheader();w.writerows(datos)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.grid':True,'grid.alpha':0.18,'axes.axisbelow':True})
    colores=['#25476A','#B65B32'];labels=['800 / 1333 · lote 8','1024 / 1820 · microbatch 4 × 2']
    fig,axes=plt.subplots(2,2,figsize=(11.2,7.2),constrained_layout=True)
    for ax,k,titulo in zip(axes.flat,['train_loss','valid_loss','valid_map_50','valid_map'],
        ['Pérdida de entrenamiento','Pérdida de validación','AP a IoU 0,50 en validación','AP a IoU 0,50 a 0,95 en validación']):
        for h,c,label in zip(historias,colores,labels):
            xs=[int(r['epoch']) for r in h];ys=[float(r[k]) for r in h]
            ax.plot(xs,ys,color=c,label=label,lw=2)
            if k.startswith('valid_map'):
                j=int(np.argmax([float(r['valid_map_50']) for r in h]));ax.scatter(xs[j],ys[j],color=c,zorder=5,s=45)
                ax.annotate('época '+str(xs[j]),(xs[j],ys[j]),xytext=(8,8 if j==1 else -16),textcoords='offset points',fontsize=8,color=c)
        ax.set_title(titulo,fontsize=11,weight='bold');ax.set_xlabel('Época');ax.set_xlim(1,30)
    axes[0,0].legend(frameon=False,fontsize=8)
    guardar(fig,'curvas_comparadas')
    fig,ax=plt.subplots(figsize=(10,3.1),constrained_layout=True)
    for h,c,label in zip(historias,colores,labels):
        ax.step([int(r['epoch']) for r in h],[float(r['lr']) for r in h],where='mid',color=c,label=label,lw=2)
    ax.set_yscale('log');ax.set_xlabel('Época');ax.set_ylabel('Tasa usada');ax.set_title('ReduceLROnPlateau sin cambiar la configuración');ax.legend(frameon=False,fontsize=9)
    guardar(fig,'lr_comparado')
    datos=sorted(secuencias[1:],key=lambda r:r['diferencia_ap50_puntos']); vals=[r['diferencia_ap50_puntos'] for r in datos]
    fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
    ys=np.arange(len(datos));ax.barh(ys,vals,color=['#B54F40' if v<0 else '#337C68' for v in vals])
    ax.set_yticks(ys,[r['secuencia'].replace('PIDS','') for r in datos]);ax.axvline(0,color='#555',lw=1)
    ax.set_xlabel('Cambio de AP50 en puntos porcentuales');ax.set_title('Resolución 1024 frente a 800 por secuencia')
    ax.set_xlim(min(vals)-0.6,max(vals)+0.7)
    for y,v in zip(ys,vals):ax.text(v+(0.06 if v>=0 else -0.06),y,f'{v:+.2f}',va='center',ha='left' if v>=0 else 'right',fontsize=9)
    guardar(fig,'secuencias_comparadas')
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.5),constrained_layout=True)
    nombres=['AP50','AP 0,50:0,95','AP50 difficult','AP small'];claves=[('todos','map_50'),('todos','map'),('difficult','map_50'),('todos','map_small')]
    xs=np.arange(4)
    for i,(m,c,label) in enumerate(zip(mapas,colores,labels)):
        vs=[m[g][k] for g,k in claves];bars=axes[0].bar(xs+(i-.5)*.36,vs,width=.36,color=c,label=label)
        axes[0].bar_label(bars,fmt='%.3f',fontsize=8,padding=3)
    axes[0].set_xticks(xs,nombres,rotation=15);axes[0].set_ylim(0,1.08);axes[0].set_title('Mejor checkpoint elegido por AP50');axes[0].legend(frameon=False,fontsize=7)
    vs=[s['ms_por_imagen_una_a_una'] for s in resumenes]
    bars=axes[1].bar(['800 / 1333','1024 / 1820'],vs,color=colores,width=.55);axes[1].bar_label(bars,fmt='%.1f ms',padding=4)
    axes[1].set_ylim(0,145);axes[1].set_ylabel('Milisegundos por imagen');axes[1].set_title('Inferencia individual en RTX 3060')
    guardar(fig,'precision_y_coste')
    salida=dict(experimentos=EXPERIMENTOS,conjunto='val',semilla=0,
        mejores_epocas=[max(h,key=lambda r:float(r['valid_map_50'])) for h in historias],
        maximos_ap_promedio_historial=[max(h,key=lambda r:float(r['valid_map'])) for h in historias],
        metricas=filas,por_video=secuencias,
        umbrales_f1=[s['umbral_f1_maximo'] for s in resumenes],
        latencias_ms=[dict(lote=s['ms_por_imagen_lote'],individual=s['ms_por_imagen_una_a_una']) for s in resumenes],
        notas=['Checkpoint seleccionado por AP50 en ambas ejecuciones, no por AP 0,50:0,95.',
        'Microbatch 4 y acumulación 2 no equivalen numéricamente a lote físico 8.',
        'Las latencias en lote usan tamaños distintos; la individual es más comparable.',
        'Una semilla y etiquetas incompletas limitan las conclusiones; test no se evalúa.'])
    (DESTINO/'comparacion.json').write_text(json.dumps(salida,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Tercer panel de la primera fila: conservar su nombre de secuencia y frame.
    origen=Image.open(BASE/'resultados_test'/(EXPERIMENTOS[1]+'_val')/'ejemplos_peores.jpg')
    assert origen.size == (1725,695), 'Revisar el recorte si cambia la lámina original'
    origen.crop((1150,28,1725,350)).save(DESTINO/'ejemplo_errores_res1024.png')
    return salida


def guardar(fig,nombre):
    fig.savefig(DESTINO/(nombre+'.png'),dpi=240);fig.savefig(DESTINO/(nombre+'.pdf'));plt.close(fig)


if __name__=='__main__':
    print(json.dumps(generar()['mejores_epocas'],ensure_ascii=False))
