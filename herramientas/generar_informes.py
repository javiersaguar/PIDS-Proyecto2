"""Rellena copias de PIDS-template.docx sin modificar la plantilla ni sus estilos.

Requiere python-docx, lxml y Pillow. Los PDF se exportan y revisan por separado.
"""
from copy import deepcopy
import csv
import json
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import os
import re
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from lxml import etree
from PIL import Image

RAIZ=Path(__file__).resolve().parents[1]
TEMPLATE=RAIZ/'docs/PIDS-template.docx'
DESTINO=RAIZ/'docs/informes'
FIG=DESTINO/'figuras'
WEEK=RAIZ/'ENTREGA 1/WEEK2'
AUTORES=['Javier Saguar','Alejandro Cuevas','Mónica Fernández','Pedro José Orrego','Daniel Naval']
NOMBRES={'faster_rcnn_v2':'Faster R-CNN v2','retinanet_v2':'RetinaNet v2','faster_rcnn_v1':'Faster R-CNN v1','retinanet_v1':'RetinaNet v1',
         'faster_rcnn_v3':'Faster R-CNN MobileNet','ssd_v1':'SSD300 VGG16','ssd_v2':'SSDlite320'}


def num(x,dec=4):
    return f'{float(x):.{dec}f}'.replace('.',',')


def leer_csv(ruta):
    with open(ruta,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))


def f1(precision,exhaustividad):
    p,r=float(precision),float(exhaustividad)
    return 2*p*r/(p+r)


SHA_TEMPLATE='e05f22eed16ea28bd2cab409d0d37c1274ff563232d53dc9b523a3ee016c7f4b'


REFS_B2 = [
    ('{L}', 'T.-Y. Lin et al. Focal Loss for Dense Object Detection. 2017. https://arxiv.org/abs/1708.02002'),
    ('{S}', 'W. Liu et al. SSD: Single Shot MultiBox Detector. 2016. https://arxiv.org/abs/1512.02325'),
    ('{R}', 'K. He et al. Deep Residual Learning for Image Recognition. 2016. https://arxiv.org/abs/1512.03385'),
    ('{P}', 'T.-Y. Lin et al. Feature Pyramid Networks for Object Detection. 2017. https://arxiv.org/abs/1612.03144'),
    ('{M}', 'A. Howard et al. Searching for MobileNetV3. 2019. https://arxiv.org/abs/1905.02244'),
    ('{V}', 'K. Simonyan y A. Zisserman. Very Deep Convolutional Networks for Large-Scale Image Recognition. 2015. https://arxiv.org/abs/1409.1556'),
    ('{C}', 'T.-Y. Lin et al. Microsoft COCO: Common Objects in Context. 2014. https://arxiv.org/abs/1405.0312'),
    ('{W}', 'Y. Li et al. Benchmarking Detection Transfer Learning with Vision Transformers. 2021. https://arxiv.org/abs/2111.11429'),
    ('{Z}', 'M. Sandler et al. MobileNetV2: Inverted Residuals and Linear Bottlenecks. 2018. https://arxiv.org/abs/1801.04381'),
    ('{T}', 'A. Paszke et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library. 2019. https://arxiv.org/abs/1912.01703'),
]


def componer_casos():
    """Une un acierto y el caso con más errores de validación en una sola figura."""
    a, b = Image.open(FIG/'caso_al_azar.png').convert('RGB'), Image.open(FIG/'caso_peores.png').convert('RGB')
    alto = min(a.height, b.height)
    a, b = (im.resize((round(im.width*alto/im.height), alto)) for im in (a, b))
    lienzo = Image.new('RGB', (a.width+b.width+10, alto), 'white')
    lienzo.paste(a, (0, 0));lienzo.paste(b, (a.width+10, 0))
    lienzo.save(FIG/'casos_validacion.png')


class Informe:
    def __init__(self, modo):
        self.modo=modo;self.doc=Document(TEMPLATE);self.nfig=0;self.ntabla=0
        self.md=['# Memoria del proyecto '+{'fase1':'Fase 1','fase2':'Fase 2','completo':'Fases 1 y 2'}[modo]+'\n',
                 'Autores: '+', '.join(AUTORES)+'\n']
        self.nueva_pagina=False
        self.cit={tok:f'[{6+n}]' for n,(tok,_) in enumerate(REFS_B2)};self.fb=self.tb=0
        body=self.doc._element.body
        cover=[]
        for el in body:
            text=''.join(el.itertext())
            if el.tag==qn('w:p') and 'Cómo usar esta plantilla' in text:break
            if el.tag==qn('w:tbl') and '[ELIMINAR' in text:continue
            if el.tag!=qn('w:sectPr'):
                copy=deepcopy(el)
                for br in list(copy.iter(qn('w:br'))):
                    if br.get(qn('w:type'))=='page':br.getparent().remove(br)
                cover.append(copy)
        for el in list(body):
            if el.tag!=qn('w:sectPr'):body.remove(el)
        for i,el in enumerate(cover):body.insert(i,el)
        for p in self.doc.paragraphs:
            if 'Sistema de detección' in p.text:
                p.style=self.doc.styles['Title']
                for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
                borders=OxmlElement('w:pBdr')
                for edge in ['top','bottom','left','right']:
                    b=OxmlElement('w:'+edge);b.set(qn('w:val'),'nil');borders.append(b)
                p._p.get_or_add_pPr().append(borders)
            if 'MEMORIA DEL PROYECTO' in p.text:
                p.text={'completo':'MEMORIA DEL PROYECTO  FASES 1 Y 2',
                        'fase1':'MEMORIA DEL PROYECTO  FASE 1',
                        'fase2':'MEMORIA DEL PROYECTO  FASE 2'}[modo]
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        portada=self.doc.tables[0]
        valores=['2', '\n'.join(AUTORES),
                 'Entrega 1 · Bloque 1' if modo=='fase1' else 'Avance de entrega 2 · Bloques 1 y 2' if modo=='completo' else 'Copia de trabajo · solo Bloque 2',
                 '20/10/2026' if modo=='fase1' else 'Pendiente de confirmación', '2026/2027']
        for row,text in zip(portada.rows,valores):
            row.cells[1].text=text
            for p in row.cells[1].paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:r.font.size=Pt(10)
        self.p('Contenido actualizado el 25 de octubre de 2026. Grupo 2 según el usuario pids2; confirmar identificación administrativa y fecha de entrega.')
        self.page()
        self.h('Respuesta a la revisión anterior')
        self.p('No aplica a la primera entrega.' if modo=='fase1' else 'No se han recibido comentarios del profesor sobre la entrega 1, por lo que no se ha introducido ningún cambio derivado de una revisión.')
        self.h('Reparto del trabajo')
        if self.modo=='fase1':
            self.table(['Integrante','Tareas del Bloque 1'],[
                ['Javier Saguar','Lote A (vídeos 01-02): extracción, anotación y revisión cruzada. Fichas de los vídeos, criterios de anotación y depuración del dataset. Aumento de datos sobre el script de Alejandro, que mejoró y ejecutó. Redacción de la memoria.'],
                ['Alejandro Cuevas','Lote B (vídeos 03-04): extracción, anotación y revisión cruzada. Análisis exploratorio de los datos (EDA) y script de entrenamiento sobre el que se integró el aumento. Redacción de la memoria.'],
                ['Mónica Fernández','Lote C (vídeos 05-06): extracción, anotación y revisión cruzada. Calibración entre anotadores y revisión de la memoria.'],
                ['Pedro José Orrego','Lote D (vídeos 07-08): extracción, anotación y revisión cruzada. Calibración, selección de figuras del EDA y diseño de la web de figuras interactivas (GitHub Pages).'],
                ['Daniel Naval','Lote E (vídeos 09-10): extracción, anotación y revisión cruzada. Calibración y redacción de la memoria.']],widths=[3.5,12.5],size=9)
            self.caption('Reparto del trabajo del Bloque 1 entre los cinco integrantes.',tipo='Tabla')
        else:
            self.p('Distribución documentada en los commits y tareas. La participación final se revisará en grupo antes de entregar.')
            self.table(['Integrante','Datos y análisis','Entrenamiento y evaluación'],[
                ['Javier Saguar','Organización, extracción, lote A, revisión, depuración, aumento y ampliaciones del EDA','Experimentos en laboratorio, evaluación y memoria'],
                ['Alejandro Cuevas','Lote B, revisión de C y EDA','Adaptación de train/test y propuestas de mejora'],
                ['Mónica Fernández','Lote C y calibración','Pendiente de consolidar reparto'],
                ['Pedro José Orrego','Lote D, calibración y selección de figuras','Pendiente de consolidar reparto'],
                ['Daniel Naval','Lote E y calibración','Pendiente de consolidar reparto']],widths=[3.0,6.5,6.5],size=9)
            self.caption('Reparto provisional del trabajo documentado.',tipo='Tabla')
        self.page();self.h('Índice')
        p=self.doc.add_paragraph();r=p.add_run()
        for kind,text in [('begin',None),(None,' TOC \\o "1-1" \\h \\z \\u '),('separate',None)]:
            el=OxmlElement('w:fldChar' if kind else 'w:instrText')
            if kind:el.set(qn('w:fldCharType'),kind)
            else:el.text=text
            r._r.append(el)
        r.add_text('El índice se actualiza al abrir el documento en Word.')
        end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');r._r.append(end)
        self.page()

    def c(self,text):
        for k,v in self.cit.items():text=text.replace(k,v)
        text=re.sub(r'@F(\d+)',lambda m:f'Figura {self.fb+int(m.group(1))}',text)
        return re.sub(r'@T(\d+)',lambda m:f'Tabla {self.tb+int(m.group(1))}',text)
    def p(self,text):
        text=self.c(text);self.doc.add_paragraph(text);self.md.append(text+'\n')
    def h(self,text,level=1):
        p=self.doc.add_paragraph(text,style='Heading '+str(level))
        if self.nueva_pagina:p.paragraph_format.page_break_before=True;self.nueva_pagina=False
        self.md.append('#'*(level+1)+' '+text+'\n')
    def page(self):self.nueva_pagina=True
    def table(self,headers,rows,widths=None,size=10):
        self.ntabla+=1
        t=self.doc.add_table(rows=1,cols=len(headers));t.autofit=False
        if widths is None:widths=[16/len(headers)]*len(headers)
        for col,w in zip(t.columns,widths):col.width=Cm(w)
        for c,h,w in zip(t.rows[0].cells,headers,widths):c.text=str(h);c.width=Cm(w)
        for row in rows:
            for cell,text,w in zip(t.add_row().cells,row,widths):cell.text=self.c(str(text));cell.width=Cm(w)
        for ri,row in enumerate(t.rows):
            trPr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trPr.append(cant)
            if ri==0:
                repeat=OxmlElement('w:tblHeader');trPr.append(repeat)
            for ci,cell in enumerate(row.cells):
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcPr=cell._tc.get_or_add_tcPr()
                borders=OxmlElement('w:tcBorders')
                for edge in ['top','left','bottom','right']:
                    b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
                tcPr.append(borders)
                margin=OxmlElement('w:tcMar')
                for edge in ['top','bottom','left','right']:
                    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'65');e.set(qn('w:type'),'dxa');margin.append(e)
                tcPr.append(margin)
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'203B65' if ri==0 else 'F1F4F8' if ri%2 else 'FFFFFF');tcPr.append(shade)
                for p in cell.paragraphs:
                    p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2);p.paragraph_format.keep_with_next=(ri<2 or ri>=len(t.rows)-2)
                    p.paragraph_format.line_spacing=1.05
                    for r in p.runs:
                        r.font.name='Calibri';r.font.size=Pt(size)
                        if ri==0:r.bold=True;r.font.color.rgb=RGBColor(255,255,255)
        self.md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(self.c(str(x)) for x in r)+' |' for r in rows)+'\n')
        return t
    def caption(self,text,tipo='Figura'):
        if tipo=='Figura':self.nfig+=1;n=self.nfig
        else:n=self.ntabla
        p=self.doc.add_paragraph(f'{tipo} {n}. {text}',style='Caption')
        p.paragraph_format.keep_with_next=False
        p.paragraph_format.keep_together=True
        self.md.append(f'{tipo} {n}. {text}\n')
    def fig(self,path,text,width=16,maxheight=12):
        path=Path(path);im=Image.open(path);w=min(width,maxheight*im.width/im.height)
        p=self.doc.add_paragraph();p.paragraph_format.keep_with_next=True
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path),width=Cm(w))
        self.caption(text)
        relativo=Path(os.path.relpath(path,DESTINO)).as_posix().replace(' ','%20')
        self.md.append(f'![{text}]({relativo})\n')
    def fase1(self):
        self.h('1. Introducción')
        self.h('1.1. Contexto y motivación',2)
        self.p('El proyecto desarrolla un detector de RoboMasters rivales desde la cámara de un robot móvil. Movimiento, cambios de tamaño, iluminación y oclusión dificultan localizar sus cajas. La percepción alimentará una futura estrategia de apuntado y actuación.')
        self.h('1.2. Objetivos del proyecto',2)
        self.p('El Bloque 1 construye y caracteriza datos; el Bloque 2 ajusta el detector y el Bloque 3 lo integrará con el robot. Se obtienen 808 originales anotados y se seleccionan 796 tras revisar sus etiquetas.')
        self.h('2. Recolección de datos')
        self.h('2.1. Estrategia y condiciones de captura',2)
        self.p('Se grabaron diez vídeos en seis tipos de escenario, variando luz, contraluces, reflejos, obstáculos y distancias. Se incluyeron movimiento y patas de sillas porque se prevén en la demo. Los dos exteriores comparten ubicación; aún falta el circuito definitivo.')
        self.h('2.2. Extracción de imágenes',2)
        self.p('La cámara entrega 1280 × 720 a unos 30,30 fps. INTERVAL=24 conserva una muestra cada 0,79 s. La suma por vídeo floor(frames/24) produce 808 imágenes a partir de 19 508 frames y 643,8 s; no se redondea la duración global. Se reduce redundancia sin multiplicar el coste de anotación.')
        self.table(['Vídeo','Escenario','Duración s','Frames','Imágenes'],[
            ['V01','Vestíbulo granito','65,4','1982','82'],['V02','Aula con sillas','59,9','1815','75'],['V03','Aula blanca','60,2','1823','75'],['V04','Exterior','66,1','2003','83'],['V05','Pasillo','59,6','1807','75'],['V06','Vestíbulo de color','74,1','2244','93'],['V07','Vestíbulo granito','61,2','1855','77'],['V08','Vestíbulo de color','81,2','2460','102'],['V09','Exterior','56,2','1704','71'],['V10','Aula con sillas','59,9','1815','75'],['Total','1280 × 720 a 30,30 fps','643,8','19 508','808']],widths=[1.5,6.4,2.5,2.8,2.8],size=9)
        self.caption('Grabaciones propias y número exacto de imágenes extraídas.',tipo='Tabla')
        self.page();self.h('3. Anotación de datos')
        self.p('Se utilizó labelImg [1] y XML PascalVOC, con una única clase robot. Cada integrante anotó su lote y otro revisó las cajas. Se conservaron imágenes negativas con XML vacío para que el entrenamiento no las ignore.')
        self.table(['Caso','Criterio operativo'],[
            ['Robot rival','Incluir chasis, ruedas, gimbal y cañón; excluir antenas.'],['Elementos ajenos','No anotar el cañón propio, reflejos ni robots en pantallas.'],['Oclusión y borde','Anotar si es reconocible y se ve al menos un 30 %; caja sobre la parte visible.'],['Difficult','Marcar si tiene menos de 30 px de ancho, menos de la mitad visible o está muy movido.'],['Robot muy pequeño','No anotar por debajo de 10 px de lado; conservar criterios en el aumento.'],['Negativo','Guardar imagen y XML sin objetos.']],widths=[3.5,12.5])
        self.caption('Criterios comunes aplicados a los lotes.',tipo='Tabla')
        self.p('Como se observa en la figura siguiente, el criterio distingue cajas normales y difficult sin crear una segunda clase. Una frontera superior distinta alteraría tamaños y centros, por lo que se excluyen antenas y se ajusta el resto del robot de manera consistente.')
        self.fig(FIG/'anotaciones.png','Anotaciones de interior y exterior. Azul: normal; naranja: difficult.',maxheight=6)
        self.p('Los cinco anotadores etiquetaron las mismas 20 imágenes de calibración. El IoU medio entre parejas fue 0,81; el borde superior presenta la mayor discrepancia, 7 px de mediana frente a 4–5 px en los otros bordes. Esto identifica un criterio por discutir, pero no establece un techo matemático del AP del modelo. Falta cerrar en grupo la ronda de discusión de T01.')
        self.page();self.h('4. Análisis exploratorio de los datos')
        self.h('4.1. Inventario y equilibrio',2)
        self.p('El EDA se calcula sobre los 808 originales, antes de excluir imágenes. Los aumentos no se mezclan en estas estadísticas. Las cifras de la tabla y la figura permiten separar cantidad de imágenes, número de objetos y dificultad.')
        self.table(['Estadística','Valor'],[['Secuencias / imágenes','10 / 808'],['Imágenes medias por secuencia','80,8'],['Cajas / cajas medias por imagen','1420 / 1,76'],['Difficult','375 cajas · 26,4 %'],['Imágenes negativas','41 · 5,07 %'],['Área media de caja','33,627 miles de píxeles²'],['Área mínima / máxima','1,020 / 661,074 miles de píxeles²'],['Aspecto mediano ancho / alto','1,11']],widths=[10,6])
        self.caption('Estadísticas de los originales anotados.',tipo='Tabla')
        self.fig(FIG/'inventario.png','Recuento y dificultad por vídeo; sus diferencias motivan analizar cada secuencia.',maxheight=6.2)
        self.p('No basta con equilibrar imágenes: V05 contiene 170 robots y V06 solo 117. V06 tiene 22 negativos en 93 imágenes, mientras V08 no tiene negativos y concentra 65 difficult. Se conservan estas diferencias porque representan situaciones reales de captura.')
        self.page();self.h('4.2. Tamaño forma e iluminación',2)
        self.fig(FIG/'tamano_forma.png','Área y forma de las cajas de los 1420 robots. El eje de área es logarítmico.',maxheight=6)
        self.p('La distribución de la figura tiene una cola amplia de áreas, pero no hay cajas originales de menos de 30 px de ancho. La relación de aspecto mediana es 1,11. El análisis de cobertura de anclas obtiene un 99,6 % con IoU ≥0,5: no se cambia su configuración por ahora y se evita deformar las proporciones durante el aumento.')
        self.fig(FIG/'iluminacion.png','Brillo y contraste por secuencia, calculados en escala de grises.',maxheight=6)
        self.p('Los canales RGB caracterizan el color dominante, no solo la iluminación: también dependen del suelo y las paredes. Por eso se complementan con media y desviación típica de intensidad, y con nitidez por varianza del Laplaciano. El tono azulado de exteriores justifica cambios de color suaves; no se confunde ese tono con falta de luz. Se identificaron 52 imágenes poco nítidas para revisión visual.')
        self.p('La miniatura más parecida a una imagen procede del mismo vídeo en el 74 % de los casos. Esa correlación aconseja separar grabaciones completas, evitando una validación artificialmente fácil con fotogramas vecinos.')
        self.page();self.h('4.3. Posición y evolución temporal',2)
        self.fig(FIG/'mapas_seleccionados.png','Selección de mapas por vídeo. Todos y difficult comparten escala; se cuentan centros por 100 imágenes, incluidos los negativos.',maxheight=10)
        self.p('La figura compara la posición de las anotaciones en un exterior y un interior con muchos negativos. Se normalizan los centros por tamaño de imagen y el histograma 16 × 9 por número de imágenes. La paleta cálida con intensidad no lineal hace visibles frecuencias bajas, pero mantiene cero blanco y un máximo común. No representa el área cubierta por las cajas.')
        self.fig(FIG/'recuentos_temporales.png','Recuento por fotograma anotado en V05 y V06; la línea discontinua es su media.',maxheight=5.8)
        self.p('Las curvas muestran por qué la media de V05 es 2,27 y la de V06 1,26: el segundo vídeo contiene tramos sin objetivos. El complemento HTML incluye los diez vídeos y 132 ventanas disjuntas de 5 s para comparar todos frente a difficult. Son muestras cada 24 frames, no trayectorias individuales ni presencia inferida entre fotogramas.')
        self.page();self.h('5. Aumento de datos')
        self.p('Se aplica solo al entrenamiento y desde originales. Tres copias por imagen se combinan con las 796 originales depuradas: 3184 imágenes y 5566 cajas. Las 672 imágenes de validación y las 718 de test son secuencias independientes de otros grupos y no reciben aumento. Se mantiene un manifiesto de semillas y transformaciones [2].')
        self.table(['Técnica','Probabilidad','Variabilidad simulada'],[
            ['Volteo horizontal','0,50','Orientaciones válidas de robots; no se invierte el suelo.'],['Afín sin deformación','0,70','Escala ×0,6–1,25; giro ±6°; desplazamiento horizontal ±8 % y vertical ±5 %.'],['Brillo y contraste o gamma','0,50 conjunta','Exposición y sombras de intensidad global.'],['Tono y saturación o RGB','0,30 conjunta','Balance de blancos y cambios suaves de color.'],['MotionBlur 3–9 px','0,15','Movimiento de cámara y objetivos.'],['JPEG o ruido o resolución','0,30 conjunta','Una degradación entre JPEG, ruido gaussiano, ISO o resolución ×0,5–0,75.'],['Oclusión de barras','0,15','Obstáculos finos; cada barra limita la anchura tapada de cada robot.']],widths=[4.5,2.9,8.6],size=9)
        self.caption('Configuración del aumento base. Las alternativas OneOf no se aplican todas a la vez.',tipo='Tabla')
        self.fig(FIG/'ejemplo_aumento.png','Original y una copia del aumento base, con las cajas transformadas.',maxheight=6)
        self.p('Se descartan volteo vertical y giros de 90°, el recorte 4:3 redimensionado a 16:9 que ensancha robots y la perspectiva con cajas incorrectas en Albumentations 1.4.18. El relleno gris evita duplicar robots sin etiqueta en los bordes. Se usan cajas ajustadas y filtros de lado mínimo 10 px y visibilidad 30 %.')
        self.page();self.h('6. Depuración de datos')
        self.p('Se revisaron visualmente 69 imágenes: 52 de baja nitidez, 11 casi duplicadas y 6 casos dudosos. Se excluyeron una imagen con un robot visible imposible de anotar de forma consistente y 11 redundantes. Se conservaron 41 imágenes movidas con sus robots difficult y los negativos difíciles. La baja nitidez no es por sí sola un motivo para borrar.')
        self.table(['Conjunto','Imágenes','Cajas'],[['Original anotado','808','1420'],['Original tras depuración','796','1399'],['Copias del aumento base','2388','4167'],['Entrenamiento total','3184','5566']],widths=[9,3.5,3.5])
        self.caption('Efecto de la depuración y del aumento base.',tipo='Tabla')
        self.p('Las exclusiones están identificadas en docs/depuracion_excluir.csv; no se borra ningún original. Quedan cuatro imágenes por debajo del objetivo de unas 800. Se prioriza no entrenar con etiquetas contradictorias, y se mantiene prevista una captura complementaria si el grupo o el profesorado exige reponerlas.')
        self.p('Al aumentar se pierden 30 de las 4197 cajas que entrarían en las copias, un 0,715 %, frente al 14,1 % del aumentador de referencia de la asignatura. La relación de aspecto mediana permanece en 1,10 frente a 1,11 original. Es una comprobación de integridad del dataset, no una prueba de mejora del detector.')
        self.h('6.1. Ampliaciones preparadas y límites',2)
        self.p('Se han implementado perfiles optativos con sombras y llovizna solo en V04/V09, obstáculos con textura y oscuridad o movimiento adicionales en una copia de imágenes con difficult. La unión de máscaras de los obstáculos se limita al 25 % del área de cada caja, que no equivale al área visible del cuerpo del robot. El combinado se ha comprobado en memoria sobre 2388 copias, pero aún no se ha entrenado.')
        self.p('Estas ampliaciones tienen destinos separados y no sustituyen el aumento base de los experimentos ya medidos. La lluvia sintética no acredita robustez en lluvia real. Los límites principales del Bloque 1 son la variedad de exteriores, el desacuerdo sobre el borde superior y la falta de ejemplos del circuito definitivo.')

    def fase2(self):
        self.fb,self.tb=self.nfig,self.ntabla
        componer_casos()
        self.h('7. El pipeline de entrenamiento')
        self.p('Se entrena con PyTorch {T} y torchvision [4] sobre 3184 imágenes (las 796 originales y tres copias aumentadas de cada una). Validación contiene 672 imágenes de 11 secuencias externas, con 1561 robots, 255 difficult y ningún negativo. Test contiene 718 imágenes de 13 secuencias externas, con 1721 robots y 270 difficult, y se reservó para evaluar una sola vez cada modelo, sin usarlo para elegir nada (apartado 11.5).')
        self.fig(FIG/'pipeline.png','Flujo realmente usado para ajustar pesos y seleccionar el checkpoint con validación.',maxheight=4.4)
        self.p('La @F1 resume el flujo. Los JPEG y XML (originales y aumentos) pasan al Dataset, que carga una muestra: la imagen RGB como tensor en [0,1] y un diccionario con sus cajas y etiquetas. El DataLoader agrupa varias en un batch de 8 imágenes y se lo entrega al modelo, que normaliza y escala la imagen internamente y devuelve, en entrenamiento, las pérdidas de RPN, clasificación y regresión; su suma es la función de pérdida. Tras la retropropagación, SGD usa los gradientes para actualizar los pesos. Un batch es el subconjunto de imágenes que se procesa en cada paso y una época es una pasada completa por el entrenamiento. Se procesa por batches porque las 3184 imágenes no caben a la vez en la memoria de la GPU y porque actualizar los pesos con subconjuntos da muchas más actualizaciones por época que hacerlo una sola vez con todo el conjunto. Al final de cada época se pasa la validación: el modelo recorre las 672 imágenes de secuencias que no ha visto sin actualizar los pesos (no_grad) y se calculan la pérdida de validación y el AP. Sirve para medir cuánto generaliza y para elegir el checkpoint, y por eso no puede modificar los pesos: si aprendiera de esas imágenes dejaría de ser una medida independiente. model_last se guarda siempre y model_best solo cuando sube el AP@0,5.')
        self.p('Las cajas difficult también participan en el entrenamiento: sin_difficult elimina el flag del diccionario que se entrega al detector, no sus cajas.')
        self.h('8. Modelos y transfer learning')
        self.p('Un detector tiene un backbone, la red convolucional (ResNet-50 {R}, MobileNetV3 {M}, VGG16 {V}) que convierte la imagen en mapas de características, y un resto que decide dónde y qué hay: el cuello FPN {P}, que combina escalas, y las cabezas de propuesta, clasificación y regresión. Se habla del backbone por separado porque es la parte intercambiable, la que más pesa en el coste y la que llega ya preentrenada. En todos los modelos se aplica transfer learning: se parte de los pesos aprendidos en COCO {C}, una base de datos de propósito general con más de cien mil imágenes anotadas, y se sustituye la cabeza de clasificación (las capas finales de predicción) por otra de dos clases (fondo y robot), de modo que la red conserva lo que sabe de bordes, texturas y formas y solo ajusta su salida a nuestro objeto [3,4]. Es determinante porque solo hay 796 imágenes originales de diez vídeos, muy pocas para aprender desde cero las decenas de millones de parámetros de estas redes, y porque así el mejor checkpoint llega en pocas épocas (apartado 11.3).')
        self.table(['Modelo','Familia','Idea y rasgo distintivo','Backbone'],[
            ['Faster R-CNN v1','Dos etapas','Un RPN propone regiones y una segunda cabeza las clasifica y ajusta su caja','ResNet-50 + FPN'],
            ['Faster R-CNN v2','Dos etapas','Misma idea con FPN y cabeza más profundas y normalizadas, y una receta de entrenamiento más reciente {W}','ResNet-50 + FPN'],
            ['Faster R-CNN MobileNet','Dos etapas ligera','Misma estructura con un backbone pequeño y entrada reducida: prioriza la velocidad','MobileNetV3-L + FPN'],
            ['RetinaNet v1 / v2','Una etapa','Predice en todas las posiciones sobre anclas y usa pérdida focal para compensar que casi todo es fondo {L}; la v2 mejora cabeza y receta','ResNet-50 + FPN'],
            ['SSD300','Una etapa','Predice en varias escalas a partir de una entrada de 300 × 300 {S}','VGG16'],
            ['SSDlite320','Una etapa ligera','SSD con convoluciones separables y entrada de 320 × 320 {Z}','MobileNetV3-L']],widths=[3.4,2.4,7.4,2.8],size=8.5)
        self.caption('Los siete modelos comparados. En el código de partida son faster_rcnn_v1, v2 y v3, retinanet_v1 y v2, ssd_v1 y ssd_v2.',tipo='Tabla')
        self.p('La @T1 describe los siete modelos. Los resultados de COCO no predicen la ganancia en nuestros datos, por eso la comparación mide precisión y también latencia, que es lo que condiciona el uso en el robot.')
        self.p('Si se entrenara el mismo modelo desde cero con nuestras imágenes, cabe esperar un resultado claramente peor y un entrenamiento más largo: sin las características generales que aporta COCO, la red tendría que aprender bordes y formas solo con 796 imágenes de diez vídeos y tendería a memorizarlas (sobreajuste). No se ha comprobado experimentalmente, así que es una expectativa y no un resultado.')
        self.h('9. Hiperparámetros')
        self.table(['Parámetro','Valor aplicado'],[['Épocas / lote efectivo / semilla','12 (15 con lr 0,0005; 30 al inicio) / 8 / 0; res1024: microbatch 4 × 2'],['Optimizador','SGD; momentum 0,9; weight decay 0,0005'],['Tasa inicial','0,0001 en originales; 0,001 en lr001 y res1024'],['Programador','ReduceLROnPlateau con pérdida de validación'],['Bajada / paciencia / mínimo','×0,1 / 5 épocas / 1e−10'],['Resolución del detector','800/1333; res1024: 1024/1820'],['Datos aumentados','Originales y 3 copias; mismo aumento base'],['Checkpoint seleccionado','Mayor AP@0,5 en validación'],['Entorno','PyTorch 2.4.1; torchvision 0.19.1; RTX 3060 12 GB']],widths=[5.7,10.3],size=9)
        self.caption('Configuración común de los experimentos medidos.',tipo='Tabla')
        self.p('La @T2 reúne la configuración común de los experimentos. Batch size. Es el número de imágenes por actualización de pesos: con valores muy bajos el gradiente es ruidoso y la época tarda más; con valores muy altos es más estable, pero falla por memoria. Eso ocurrió: con 8 GB, Faster R-CNN v1 y RetinaNet v2 no caben con lote 8, y Faster R-CNN v2 y res1024 se entrenan con microlotes de 4 acumulados dos veces, que mantiene el lote efectivo en 8. No se varió el lote para medir su efecto en el AP: se fijó en 8 para comparar el resto, así que lo dicho sobre lotes bajos es lo esperado y no una medida.')
        self.p('Learning rate. Es el tamaño del paso. Con 0,0001 el mejor checkpoint llega en la época 29; con 0,001, en la 5; con 0,002, en la 1 o la 2, y después el AP pierde entre 1,1 y 1,4 puntos: un paso demasiado grande desestabiliza. Con 0,0005 el máximo llega entre las épocas 5 y 14, es decir, se necesitan más épocas. El programador baja la tasa ×0,1 tras cinco épocas sin mejorar la pérdida de validación, pero tarde para recuperar el óptimo (apartado 11.1).')
        self.p('Épocas. Merece la pena entrenar poco: el mejor checkpoint cae entre las épocas 3 y 7 en seis de los siete modelos (SSD300 en la 12 y, con 40 épocas, en la 18, con el mismo AP@0,5) y, con 30 épocas, la pérdida de validación toca su mínimo en la 4 y sube después mientras la de entrenamiento sigue bajando. Esa es la señal para parar: la pérdida de validación deja de bajar o sube mientras la de entrenamiento continúa bajando, y el AP de validación se estanca. Entre el 50 % y el 75 % del tiempo posterior al mejor checkpoint no mejora nada.')
        self.p('Optimizador y programador. El optimizador, SGD, mueve cada peso en sentido contrario a su gradiente, multiplicado por la tasa; sus parámetros propios son el momentum (0,9), que arrastra parte de la dirección anterior para suavizar el ruido, y el weight decay (0,0005), que penaliza los pesos grandes para limitar el sobreajuste. El learning-rate scheduler ReduceLROnPlateau reduce la tasa (×0,1) cuando la pérdida de validación no mejora durante cinco épocas: al principio conviene dar pasos grandes para avanzar deprisa y cerca del óptimo pasos pequeños para ajustarlo sin pasarse, por eso la tasa no tiene por qué ser constante. No se ensayaron otros optimizadores.')
        self.h('10. Métricas')
        self.p('IoU es la intersección entre caja predicha y real dividida por su unión. Con IoU≥0,5 y confianza≥0,5 se emparejan detecciones por confianza: acierto TP, detección sin pareja FP y robot sin pareja FN. Precisión es TP/(TP+FP), exhaustividad TP/(TP+FN) y F1 la media armónica de ambas. El score_threshold es la confianza mínima para aceptar una detección: al subirlo se descartan detecciones dudosas (menos FP y más precisión, pero más FN y menos exhaustividad) y al bajarlo ocurre lo contrario, de ahí el compromiso entre ambas (apartado 11.5).')
        self.p('AP resume la curva precisión–exhaustividad al variar la confianza: es el área bajo ella. AP@0,5 fija IoU en 0,5; AP@0,75 exige cajas más ajustadas; AP 0,50:0,95 promedia umbrales de IoU de 0,50 a 0,95 (es lo que COCO llama mAP); la «m» indica la media entre clases, y con una sola clase la mAP coincide con la AP. AP small usa la categoría de área de COCO, no el criterio de ancho <30 px de nuestra anotación. Las etiquetas incompletas de validación pueden penalizar detecciones correctas como FP; no se interpreta el recuento como error visual confirmado.')
        self.h('11. Experimentos')
        self.p('Los experimentos siguieron este orden: ajuste de la tasa de aprendizaje con un único modelo (apartados 11.1 y 11.2), comparación de siete arquitecturas con los hiperparámetros ya fijados (11.3 y 11.4) y evaluación final en test (11.5). Se desvía de lo recomendado en un punto: el aumento no se dejó para el final con el mejor modelo, sino que se midió pronto con Faster R-CNN v1 (@T3) y las siete arquitecturas se entrenaron ya con el perfil robusto_v1, por lo que no hay una comparación sin aumento para el modelo final. Tampoco se varió el batch size. Los experimentos que no mejoraron (resolución 1024, perfil robusto_v1, tasas distintas de 0,001) se documentan igual que los demás.')
        self.h('11.1. Aumento de datos y tasa de aprendizaje',2)
        self.table(['Experimento','Mejor época','AP50 historial','AP50 evaluación','AP evaluación'],[['Sin aumento lr 0,0001','20','0,9229','0,9228','0,5809'],['Aumento base lr 0,0001','29','0,9425','0,9416','0,6081'],['Aumento base lr 0,001','5','0,9432','0,9433','0,6302'],['lr 0,001 res1024','2','0,9464','0,9465','0,6047']],widths=[5.4,2.2,2.8,2.8,2.8],size=9)
        self.caption('Mejor checkpoint por AP50 en validación. AP sin sufijo es AP 0,50:0,95. El historial y la evaluación final se mantienen separados.',tipo='Tabla')
        self.p('La @T3 compara los cuatro primeros experimentos. El aumento base mejora especialmente difficult: AP50 de 0,5518 a 0,6341. La comparación a igual número de épocas incluye cuatro veces más imágenes y actualizaciones con aumento, así que no permite atribuir toda la diferencia a las transformaciones. Pasar de 0,0001 a 0,001 mejora sobre todo el ajuste de las cajas (AP 0,50:0,95 +2,21 puntos y AP75 +3,14) y apenas el AP50 (+0,17), pero lo alcanza en la época 5 en lugar de la 29.')
        self.fig(WEEK/'comparaciones/lr001/curvas_comparadas.png','Pérdidas y AP por época. Los puntos señalan los checkpoints elegidos por AP50.',maxheight=4.8)
        self.p('Con lr 0,001 la pérdida de validación mínima aparece en la época 4 (0,2212) y sube hasta 0,2413 en la 30 mientras la de entrenamiento baja a 0,0657 (@F2), y el AP50 final cae a 0,9332: hay sobreajuste después del óptimo temprano, y por eso se conserva model_best y no model_last. La @F3 muestra la tasa usada en cada época: ReduceLROnPlateau la baja de 0,001 a 1e−7 en las épocas 11, 17, 23 y 29 sin recuperar el óptimo.')
        self.fig(WEEK/'comparaciones/lr001/lr_comparado.png','Tasa usada en cada época. Las bajadas de ReduceLROnPlateau no recuperan el óptimo temprano.',maxheight=4.2)
        self.h('11.2. Resolución de entrada',2)
        self.p('La ganancia modesta en objetos pequeños (AP small 0,1182) motivó subir min_size/max_size de 800/1333 a 1024/1820 desde COCO con lr 0,001 y aumento base. Un frame pasa de 1333 × 750 a 1820 × 1024 píxeles, un 86 % más. Por memoria se usaron microbatch 4 con acumulación 2, no idéntico numéricamente a un lote de 8. La @T4 compara ambas resoluciones.')
        self.table(['Mejor por AP50 en validación','lr001 800','lr001 1024','Cambio'],[['AP50 todos','0,9433','0,9465','+0,32 pp'],['AP 0,50:0,95 todos','0,6302','0,6047','−2,55 pp'],['AP75 todos','0,7460','0,6990','−4,70 pp'],['AP50 difficult','0,6462','0,6282','−1,80 pp'],['AP small','0,1182','0,1886','+7,04 pp'],['FP / FN (conf. 0,5)','190 / 83','324 / 68','+134 / −15'],['F1 (conf. 0,5)','0,9155','0,8840','−3,15 pp'],['Latencia por imagen','75,1 ms','121,6 ms','+61,9 %']],widths=[6.4,3.2,3.2,3.2],size=9)
        self.caption('Resolución 800 frente a 1024 con el mismo procedimiento. La inferencia es una imagen cada vez en la RTX 3060, sin captura ni actuación.',tipo='Tabla')
        self.p('Res1024 detecta 15 robots más, nueve de ellos difficult, y mejora los pequeños, pero añade 134 FP, empeora el ajuste de cajas y cuesta un 62 % más de tiempo (unas 8,2 frente a 13,3 imágenes/s). El mejor AP50 llega en la época 2 y el máximo AP 0,50:0,95 del historial (0,6322) en la 5; se respeta el criterio AP50 fijado de antemano. No es una mejora uniforme, y la referencia queda en lr001 800. Por secuencias, lr001 mejora el AP50 en 7 de las 11 de validación y res1024 en 4; GR04_0003 de 2024 pierde sus seis difficult con las dos.')
        self.h('11.3. Comparación de arquitecturas',2)
        self.p('Se entrenaron los siete modelos del apartado 8, todos desde COCO con la cabeza sustituida, con el perfil de aumento robusto_v1 (las 796 originales y tres copias), 12 épocas, SGD con tasa 0,001 y semilla 0, y se conserva el checkpoint con mayor AP@0,5 en validación. La @T5 recoge los resultados y la @F4 las curvas de AP por época. Las figuras interactivas, con selectores de medida, modelo y conjunto, están en https://javiersaguar.github.io/PIDS-Proyecto2/bloque2/.')
        self.table(['Modelo','Época','AP50 todos','AP50 normales','AP50 difficult','AP 0,5:0,95','F1 máx. (umbral)','ms/imagen','Min'],[
            ['Faster R-CNN v2','3','0,9513','0,9759','0,6422','0,6192','0,9361 (0,95)','99,5','151'],
            ['RetinaNet v2','6','0,9447','0,9748','0,6213','0,6114','0,9264 (0,65)','67,3','102'],
            ['Faster R-CNN v1','5','0,9426','0,9733','0,6471','0,6273','0,9305 (0,90)','75,1','106'],
            ['RetinaNet v1','7','0,9396','0,9687','0,5994','0,6196','0,9229 (0,65)','72,2','98'],
            ['Faster R-CNN MobileNet','3','0,9281','0,9597','0,6027','0,5789','0,9167 (0,55)','16,0','19'],
            ['SSD300 VGG16','12','0,9008','0,9404','0,5199','0,5144','0,8926 (0,25)','12,5','19'],
            ['SSDlite320','7','0,6823','0,7272','0,3233','0,3943','0,6839 (0,20)','4,2','6']],widths=[3.5,1.0,1.5,1.7,1.6,1.6,2.6,1.4,1.1],size=8)
        self.caption('Siete arquitecturas con lr 0,001 en validación (672 imágenes, 1561 robots, 255 difficult): época del mejor checkpoint, F1 máximo de la rejilla de umbrales de 0,05, milisegundos por imagen de una en una y minutos de entrenamiento.',tipo='Tabla')
        self.fig(FIG/'curvas_arquitecturas.png','AP@0,5 en validación por época. El punto marca el checkpoint elegido.',maxheight=4.8)
        self.p('Faster R-CNN v2 es el más preciso (0,9513), seguido de RetinaNet v2 (0,9447), Faster R-CNN v1 (0,9426) y RetinaNet v1 (0,9396): las cuatro redes con ResNet-50 quedan a 1,2 puntos entre sí, diferencias pequeñas con una sola semilla. Faster R-CNN alcanza su máximo en las épocas 3 a 5 y después pierde entre 0,6 y 1 punto mientras su pérdida de entrenamiento baja (sobreajuste temprano); RetinaNet arranca más despacio, pero es más estable. SSD300 todavía mejoraba en la época 12, pero con 40 épocas el AP@0,5 pasa de 0,9008 a 0,9009: doce épocas no eran pocas.')
        self.fig(FIG/'precision_latencia.png','Precisión frente a tiempo por imagen. Faster R-CNN con MobileNet es el mejor compromiso rápido; los círculos pequeños son las variantes de tasa.',maxheight=5.0)
        self.p('Las redes ligeras pierden precisión (@F5). Faster R-CNN con MobileNet baja 2,3 puntos, pero tarda 16,0 ms por imagen frente a 99,5 de la v2, unas seis veces menos. SSD300 (0,9008) es más rápida que las de ResNet-50, pero MobileNet le saca 2,7 puntos por 3,5 ms más. SSDlite320 (0,6823) no sirve: reduce la imagen a 320 × 320 y los robots lejanos casi desaparecen. El coste también separa a las arquitecturas: los 13 entrenamientos suman 1306 minutos (21,8 horas de GPU), Faster R-CNN v2 es la más cara (151 minutos) y MobileNet cuesta 19. Los difficult son el punto débil de todas: su AP@0,5 queda entre 0,60 y 0,65 (de 33 a 37 puntos por debajo de los normales), y cambiar de arquitectura no cierra esa brecha.')
        self.h('11.4. Tasa de aprendizaje y perfil de aumento',2)
        self.table(['Modelo','lr','Mejor época','AP50 todos','AP50 difficult','AP 0,50:0,95','Min'],[
            ['Faster R-CNN v2','0,0005','5','0,9507','0,6361','0,6126','189'],['Faster R-CNN v2','0,0010','3','0,9513','0,6422','0,6192','151'],['Faster R-CNN v2','0,0020','1','0,9497','0,6223','0,6403','151'],
            ['RetinaNet v2','0,0005','11','0,9451','0,6133','0,6170','126'],['RetinaNet v2','0,0010','6','0,9447','0,6213','0,6114','102'],['RetinaNet v2','0,0020','6','0,9469','0,6246','0,6177','101'],
            ['Faster R-CNN v1','0,0005','14','0,9420','0,6323','0,6104','132'],['Faster R-CNN v1','0,0010','5','0,9426','0,6471','0,6273','106'],['Faster R-CNN v1','0,0020','2','0,9434','0,6465','0,6024','105']],widths=[3.6,1.9,2.2,2.2,2.3,2.2,1.6],size=8.5)
        self.caption('Variación de la tasa de aprendizaje en los tres modelos con mejor AP@0,5. Con 0,0005 se entrenaron 15 épocas; con 0,001 y 0,002, 12.',tipo='Tabla')
        self.p('La tasa casi no cambia el AP@0,5 (@T6): entre la mejor y la peor variante hay 0,16 puntos en Faster R-CNN v2, 0,22 en RetinaNet v2 y 0,14 en Faster R-CNN v1, lo que cabe esperar de cambiar la semilla. No hay razón para preferir otra que 0,001, que además necesita menos épocas que 0,0005. Lo que sí cambia es la estabilidad: con 0,002 Faster R-CNN alcanza su máximo en la primera o segunda época y después pierde entre 1,1 y 1,4 puntos, con la pérdida de validación subiendo (de 0,182 a 0,224 en la v2): inestabilidad y sobreajuste, no infraajuste.')
        self.p('El perfil robusto_v1 (sombras y llovizna en exteriores, obstáculos con textura y refuerzo de las imágenes con difficult; apartado 6.1) se comparó con el aumento base repitiendo Faster R-CNN v1 con lr 0,001: AP@0,5 de 0,9426 frente a 0,9433, y 0,6471 frente a 0,6462 en difficult. No hay diferencia medible (la comparación no es idéntica: 12 épocas frente a 30), y no se pudo medir cada transformación por separado ni hay una serie de lluvia real que la contraste; el perfil robusto_v1 no se adopta como mejora.')
        self.h('11.5. Evaluación final en test',2)
        self.p('El criterio se fijó antes de abrir el test y quedó registrado en el repositorio (docs/seleccion_modelo_final.md, 24/10/2026): el modelo final es el de mayor AP@0,5 en validación, el umbral de confianza es el de mejor F1 en validación, y se evalúan en test los siete modelos con lr 0,001, una sola vez cada uno. El test no se ha usado para elegir nada.')
        self.table(['Modelo','AP50 val.','AP50 test','Diff. test','Umbral','Precis.','Exhaust.','F1','FP / FN'],[
            ['Faster R-CNN v2','0,9513','0,9523','0,6921','0,95','0,9447','0,9332','0,9389','94 / 115'],
            ['RetinaNet v2','0,9447','0,9457','0,6313','0,65','0,9409','0,9064','0,9233','98 / 161'],
            ['Faster R-CNN v1','0,9426','0,9355','0,6057','0,90','0,9224','0,9250','0,9237','134 / 129'],
            ['RetinaNet v1','0,9396','0,9362','0,6273','0,65','0,9226','0,9210','0,9218','133 / 136'],
            ['Faster R-CNN MobileNet','0,9281','0,9240','0,5744','0,55','0,9145','0,9140','0,9142','147 / 148'],
            ['SSD300 VGG16','0,9008','0,8797','0,4316','0,25','0,9128','0,8216','0,8648','135 / 307'],
            ['SSDlite320','0,6823','0,6412','0,2742','0,20','0,7284','0,5985','0,6571','384 / 691']],widths=[3.7,1.5,1.5,1.5,1.3,1.5,1.6,1.4,2.0],size=8)
        self.caption('Evaluación final en test, una vez por modelo, con el umbral fijado en validación. Precisión, exhaustividad, F1 y recuento de falsos positivos y robots perdidos a ese umbral; AP50 en todos los robots y en difficult.',tipo='Tabla')
        self.fig(FIG/'validacion_vs_test.png','AP@0,5 en validación y en test. El orden se mantiene; las SSD pierden más al pasar a test.',maxheight=5.6)
        self.p('El modelo final, Faster R-CNN v2 con lr 0,001, obtiene en test un AP@0,5 de 0,9523 (0,9513 en validación; @T7 y @F6): 0,9658 en robots normales y 0,6921 en difficult. Con el umbral 0,95 detecta 1606 de los 1721 robots (exhaustividad 0,9332), con 94 falsos positivos (precisión 0,9447) y un F1 de 0,9389; el mejor F1 posible en test sería 0,9413, con umbral 0,90, a solo 0,24 puntos. Las cifras son coherentes con las de validación: el orden se mantiene salvo el intercambio entre RetinaNet v1 y Faster R-CNN v1 (0,07 puntos), las redes con ResNet-50 varían entre −0,7 y +0,1 puntos y las SSD pierden más (2,1 y 4,1).')
        self.fig(FIG/'errores_test.png','Errores en test con el umbral fijado en validación (izquierda) y curvas de umbral del modelo final (derecha); la línea punteada es el umbral elegido.',maxheight=5.8)
        self.p('Según la @F7, 74 de los 115 robots que pierde el modelo final (64 %) son difficult, que son el 16 % de los robots. Subir el umbral de 0,5 a 0,95 baja los falsos positivos de 226 a 94, pero la exhaustividad en difficult cae de 0,84 a 0,73: el umbral decide cuántos difficult se sacrifican. La opción rápida para la demo, Faster R-CNN con MobileNet, obtiene 0,9240 en test y un F1 de 0,9143 a 16,0 ms por imagen frente a 96,3 del modelo final. Los límites son una sola semilla, etiquetas de otros grupos con criterios algo distintos (antenas, robots cortados) y latencias medidas en la RTX 3060 sin captura ni actuación; no se ha medido nada en el robot.')
        self.h('12. Análisis cualitativo')
        self.p('La @F8 muestra dos predicciones del modelo lr001 sobre validación (todavía no se han dibujado predicciones sobre test): un acierto, con tres detecciones correctas, una de ellas con confianza 0,51 sobre un robot difficult, y el caso con más errores de la muestra, con cuatro detecciones sin pareja frente a las etiquetas. Las cajas verdes son aciertos y las rojas detecciones sin pareja. El segundo caso es de la secuencia GR02_0001 de 2024, en la que se confirmó una anotación incompleta (@F9), así que parte de esos falsos positivos puede deberse a etiquetas omitidas y no a errores del detector.')
        self.fig(FIG/'casos_validacion.png','Predicciones del modelo lr001 sobre validación: acierto en PIDS2025_GR01_0010/frame_1566 (TP 3, FP 0, FN 0) y el caso con más errores, PIDS2024_GR02_0001/frame_0492 (TP 2, FP 4, FN 0).',maxheight=4.3)
        self.p('La inspección de las predicciones distingue errores del detector y carencias de las etiquetas. En la @F9 se ven cuatro robots, pero el XML de GR02_0001/frame_0444 de 2024 contiene una sola caja: una detección correcta de los otros tres se cuenta como FP. No se modifican las etiquetas, para conservar la comparación. Esto limita la interpretación de los 190 FP de lr001 y los 324 de res1024, aunque no se ha cuantificado cuántos FP se deben a omisiones.')
        self.fig(FIG/'etiqueta_incompleta.png','Caso confirmado de anotación incompleta. La caja azul es la única del XML.',width=11,maxheight=4.4)
        self.fig(WEEK/'comparaciones/res1024/ejemplo_errores_res1024.png','Res1024 en PIDS2025_GR03_0011/frame_0600: TP 4, FP 4 y FN 1 frente a las etiquetas; rojo indica detección sin pareja.',width=11,maxheight=4.2)
        self.p('Los fallos reales se agrupan en tres tipos y se relacionan con lo visto en el Bloque 1. Primero, los difficult (movimiento, oclusión y tamaño pequeño, según el criterio de anotación): concentran 65 de los 83 FN de lr001 y 74 de los 115 del modelo final en test, y son solo el 26,4 % de las cajas anotadas (375 de 1420). Segundo, los objetos lejanos, con un AP small de 0,12 a 0,19: las redes de entrada pequeña no los ven y en el EDA no hay cajas originales de menos de 30 px de ancho, de modo que los robots muy lejanos están poco representados. Tercero, secuencias concretas: en test, PIDS2025_GR02_0009 pierde 40 de 204 robots (33 difficult) y PIDS2025_GR04_0000, con 13 imágenes, pierde 10 de 21; en validación, GR04_0003 de 2024 pierde siempre sus seis difficult. Entre los FP hay además detecciones sobre una pierna y cajas solapadas en torno a un robot (@F10), que las etiquetas omitidas no explican.')
        self.p('Umbral de confianza. En test, con el modelo final, subir el umbral de 0,5 a 0,95 baja los falsos positivos de 226 a 94, pero la exhaustividad en difficult cae de 0,84 a 0,73 (@F7, derecha). Se elige 0,95, que es el de mejor F1 en validación, fijado antes de abrir el test, y queda a 0,24 puntos del óptimo en test (0,90); la decisión final para el robot dependerá en el Bloque 3 del coste relativo de disparar a un falso positivo o de dejar pasar un robot.')
        self.h('12.1. Conclusiones y trabajo pendiente',2)
        self.p('El modelo final es Faster R-CNN v2 con lr 0,001, checkpoint de la época 3: AP@0,5 de 0,9523 en test (0,9658 en robots normales y 0,6921 en difficult) y F1 de 0,9389 con el umbral 0,95 fijado en validación. La opción rápida es Faster R-CNN con MobileNet, con 0,9240 en test y 16,0 ms por imagen frente a 96,3; se elige el modelo final para llevarlo al robot por ser el más preciso en validación y en test, con una latencia de 96,3 ms por imagen que parece admisible si el robot se detiene a mirar en cada punto de parada; si la latencia real resultara un problema, la alternativa es MobileNet.')
        self.p('La arquitectura importa más que la tasa de aprendizaje y que el aumento: las cuatro redes con ResNet-50 quedan a 1,2 puntos entre sí, la tasa mueve el AP@0,5 menos de 0,25 puntos y robusto_v1 no mejora al aumento base. Los difficult siguen siendo el punto débil de todas (AP@0,5 de test entre 0,57 y 0,69), las SSD no sirven para robots lejanos y Faster R-CNN sobreajusta pronto con cualquier tasa, por lo que el checkpoint se elige por validación.')
        self.p('Queda por hacer: mejorar los difficult (más imágenes reales con movimiento y oclusión, o resolución mayor con Faster R-CNN v2), repetir con varias semillas, variar el batch size y medir en el robot la latencia de toda la cadena, que corresponde al Bloque 3.')

    def terminar(self):
        if self.modo=='completo':
            self.page()
            for title in ['13. Módulos del robot','14. El circuito','15. Estrategia de búsqueda y detección','16. Funcionalidades adicionales','17. La demostración final','18. Limitaciones y trabajo futuro']:
                self.h(title);self.p('Pendiente del Bloque 3. No se han realizado ni medido todavía estas funciones en el circuito definitivo.')
        self.page();self.h('Referencias')
        refs=['[1] labelImg. Herramienta de anotación PascalVOC. https://github.com/HumanSignal/labelImg',
                  '[2] Albumentations 1.4.18. Código de transformaciones. https://github.com/albumentations-team/albumentations/tree/1.4.18',
                  '[3] S. Ren et al. Faster R-CNN Towards Real-Time Object Detection with Region Proposal Networks. 2015. https://arxiv.org/abs/1506.01497',
                  '[4] torchvision 0.19. Faster R-CNN ResNet-50 FPN. https://docs.pytorch.org/vision/0.19/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn.html',
                  '[5] Repositorio del grupo. Datos, criterios, notebooks y resultados. https://github.com/javiersaguar/PIDS-Proyecto2']
        if self.modo!='fase1':
            refs+=[f'[{6+n}] {texto}' for n,(_,texto) in enumerate(REFS_B2)]
        for t in refs:
            self.p(t)
            self.doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.LEFT
        self.p('Los originales, XML, exclusiones y manifiestos están en el repositorio. Los HTML del EDA son material complementario; las figuras del cuerpo son exportaciones estáticas. Los experimentos y tablas de esta versión se han medido en validación, salvo las comprobaciones de integridad del aumento.')
        self.doc.core_properties.author='; '.join(AUTORES)
        self.doc.core_properties.last_modified_by='Javier Saguar'
        self.doc.core_properties.title={'completo':'Detección de RoboMasters Fases 1 y 2','fase1':'Detección de RoboMasters Fase 1','fase2':'Detección de RoboMasters Fase 2'}[self.modo]
        self.doc.core_properties.subject='PIDS Proyecto 2'
        self.doc.core_properties.comments=''
        update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');self.doc.settings.element.append(update)
        tmp=BytesIO();self.doc.save(tmp)
        nombre={'completo':'informe_completo_fases_1_2','fase1':'informe_fase1','fase2':'informe_fase2'}[self.modo]
        target=DESTINO/(nombre+'.docx')
        allowed={'word/document.xml','word/_rels/document.xml.rels','word/settings.xml','docProps/core.xml','[Content_Types].xml'}
        with ZipFile(TEMPLATE) as original,ZipFile(tmp) as generado,ZipFile(target,'w',ZIP_DEFLATED) as final:
            for name in original.namelist():final.writestr(name,generado.read(name) if name in allowed else original.read(name))
            for name in generado.namelist():
                if name not in original.namelist():final.writestr(name,generado.read(name))
        with ZipFile(TEMPLATE) as original,ZipFile(target) as final:
            for name in original.namelist():
                if name not in allowed:assert original.read(name)==final.read(name),name
        (DESTINO/(nombre+'.md')).write_text('\n'.join(self.md),encoding='utf-8')
        print(target)


def main():
    assert hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()==SHA_TEMPLATE
    DESTINO.mkdir(parents=True,exist_ok=True)
    modos=sys.argv[1:]  # sin argumentos no genera nada: fase1 tiene correcciones manuales que se perderían
    if not modos:
        print('Indica qué generar: fase1, fase2 o completo. Para la entrega 2 usa generar_entrega2.py.')
        return
    for modo in modos:
        informe=Informe(modo)
        if modo in ['fase1','completo']:informe.fase1()
        if modo=='completo':informe.page()
        if modo in ['fase2','completo']:informe.fase2()
        informe.terminar()


if __name__=='__main__':main()
