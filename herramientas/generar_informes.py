"""Rellena copias de PIDS-template.docx sin modificar la plantilla ni sus estilos.

Requiere python-docx, lxml y Pillow. Los PDF se exportan y revisan por separado.
"""
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import os
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
SHA_TEMPLATE='e05f22eed16ea28bd2cab409d0d37c1274ff563232d53dc9b523a3ee016c7f4b'


class Informe:
    def __init__(self, modo):
        self.modo=modo;self.doc=Document(TEMPLATE);self.nfig=0;self.ntabla=0
        self.md=['# Memoria del proyecto '+{'fase1':'Fase 1','fase2':'Fase 2','completo':'Fases 1 y 2'}[modo]+'\n',
                 'Autores: '+', '.join(AUTORES)+'\n']
        self.nueva_pagina=False
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
                 'Pendiente de confirmación', '2026/2027']
        for row,text in zip(portada.rows,valores):
            row.cells[1].text=text
            for p in row.cells[1].paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:r.font.size=Pt(10)
        self.p('Contenido actualizado el 16 de octubre de 2026. Grupo 2 según el usuario pids2; confirmar identificación administrativa y fecha de entrega.')
        self.page()
        self.h('Respuesta a la revisión anterior')
        self.p('No aplica a la primera entrega. No hay comentarios docentes incorporados en esta versión de trabajo.')
        self.h('Reparto del trabajo')
        if self.modo=='fase1':
            self.p('Reparto a partes iguales entre los cinco integrantes: cada uno asume un lote de extracción, anotación y revisión cruzada, y un área transversal del Bloque 1.')
            self.table(['Integrante','Tareas del Bloque 1'],[
                ['Javier Saguar','Lote A (vídeos 01-02): extracción, anotación y revisión cruzada. Organización del repositorio y fichas de los vídeos.'],
                ['Alejandro Cuevas','Lote B (vídeos 03-04): extracción, anotación y revisión cruzada. Análisis exploratorio de los datos (EDA).'],
                ['Mónica Fernández','Lote C (vídeos 05-06): extracción, anotación y revisión cruzada. Calibración y criterios de anotación.'],
                ['Pedro José Orrego','Lote D (vídeos 07-08): extracción, anotación y revisión cruzada. Aumento de datos.'],
                ['Daniel Naval','Lote E (vídeos 09-10): extracción, anotación y revisión cruzada. Depuración del dataset.']],widths=[3.5,12.5],size=9)
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

    def p(self,text):
        self.doc.add_paragraph(text);self.md.append(text+'\n')
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
            for cell,text,w in zip(t.add_row().cells,row,widths):cell.text=str(text);cell.width=Cm(w)
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
                    p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                    p.paragraph_format.line_spacing=1.05
                    for r in p.runs:
                        r.font.name='Calibri';r.font.size=Pt(size)
                        if ri==0:r.bold=True;r.font.color.rgb=RGBColor(255,255,255)
        self.md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
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
        self.h('7. El pipeline de entrenamiento')
        self.p('Se entrena sobre 3184 imágenes con aumento base o sobre las 796 originales. Validación contiene 672 imágenes de 11 secuencias externas, con 1561 robots, 255 difficult y ningún negativo. Test contiene 718 imágenes y se reserva para evaluar el modelo definitivo una sola vez; no hay resultados de test en este informe.')
        self.fig(FIG/'pipeline.png','Flujo realmente usado para ajustar pesos y seleccionar el checkpoint con validación.',maxheight=8)
        self.p('La imagen se carga en RGB, se pasa a tensor en [0,1] y el modelo normaliza y escala internamente. Los primeros experimentos usan lote físico 8; res1024 acumula dos microbatches de 4 antes de actualizar. Una época recorre todo entrenamiento. Se suman las pérdidas de RPN, clasificación y regresión; SGD actualiza los pesos mediante retropropagación.')
        self.p('Las cajas difficult también participan en el entrenamiento: sin_difficult elimina el flag del diccionario que se entrega al detector, no sus cajas. Para la pérdida de validación se usa no_grad; para las detecciones y AP, eval. Cada época se guarda model_last y solo se reemplaza model_best cuando sube AP@0,5.')
        self.h('8. Modelos')
        self.p('Se ha probado Faster R-CNN ResNet-50 con FPN [3,4], una red de dos etapas: el RPN propone regiones y la cabeza clasifica y ajusta sus cajas. Se inicializa con COCO y se sustituye la cabeza por fondo y robot. FPN combina escalas, relevante para objetivos a distancias diferentes. No se ha realizado todavía una comparación de arquitecturas.')
        self.p('El código contempla Faster R-CNN v2 y una variante MobileNet, entre otras. Los resultados de COCO no predicen la ganancia en nuestros datos. Cualquier comparación futura debe medir precisión y latencia para el uso en el robot.')
        self.page();self.h('9. Hiperparámetros')
        self.table(['Parámetro','Valor aplicado'],[['Épocas / lote efectivo / semilla','30 / 8 / 0; res1024: microbatch 4 × 2'],['Optimizador','SGD; momentum 0,9; weight decay 0,0005'],['Tasa inicial','0,0001 en originales; 0,001 en lr001 y res1024'],['Programador','ReduceLROnPlateau con pérdida de validación'],['Bajada / paciencia / mínimo','×0,1 / 5 épocas / 1e−10'],['Resolución del detector','800/1333; res1024: 1024/1820'],['Datos aumentados','Originales y 3 copias; mismo aumento base'],['Checkpoint seleccionado','Mayor AP@0,5 en validación'],['Entorno','PyTorch 2.4.1; torchvision 0.19.1; RTX 3060 12 GB']],widths=[5.7,10.3])
        self.caption('Configuración común de los experimentos medidos.',tipo='Tabla')
        self.p('La tasa 0,001 se ensayó como salto de diez veces manteniendo los otros parámetros. No se añadieron warmup, otra arquitectura ni los perfiles nuevos de aumento. Cambiar una variable facilita interpretar el resultado, aunque una sola semilla no mide su variabilidad.')
        self.h('10. Métricas')
        self.p('IoU es la intersección entre caja predicha y real dividida por su unión. Con IoU≥0,5 y confianza≥0,5 se emparejan detecciones por confianza: acierto TP, detección sin pareja FP y robot sin pareja FN. Precisión es TP/(TP+FP), exhaustividad TP/(TP+FN) y F1 la media armónica de ambas.')
        self.p('AP resume la curva precisión–exhaustividad al variar confianza. AP@0,5 fija IoU en 0,5; AP@0,75 exige cajas más ajustadas; AP 0,50:0,95 promedia umbrales de IoU de 0,50 a 0,95. Al haber una clase, la media entre clases coincide con su AP. En los grupos normales/difficult se ignoran las anotaciones y detecciones emparejadas del otro grupo.')
        self.p('AP small usa la categoría de área de COCO, no el criterio de ancho <30 px de nuestra anotación. El AP de grupos y el recall a confianza fija responden a preguntas distintas. Además, las etiquetas incompletas de validación pueden penalizar detecciones correctas como FP; no se interpreta el recuento como error visual confirmado.')
        self.page();self.h('11. Experimentos')
        self.h('11.1. Comparación del aumento y de la tasa',2)
        self.table(['Experimento','Mejor época','AP50 historial','AP50 evaluación','AP evaluación'],[['Sin aumento lr 0,0001','20','0,9229','0,9228','0,5809'],['Aumento base lr 0,0001','29','0,9425','0,9416','0,6081'],['Aumento base lr 0,001','5','0,9432','0,9433','0,6302'],['lr 0,001 res1024','2','0,9464','0,9465','0,6047']],widths=[5.4,2.2,2.8,2.8,2.8],size=9)
        self.caption('Mejor checkpoint por AP50. AP sin sufijo es AP 0,50:0,95. El historial y la evaluación final se mantienen separados.',tipo='Tabla')
        self.p('El aumento base mejora especialmente difficult: AP50 de 0,5518 a 0,6341. La comparación a igual número de épocas incluye cuatro veces más imágenes y actualizaciones con aumento; no permite atribuir toda la diferencia solo a las transformaciones. La ejecución con lr001 conserva ese mismo conjunto de 3184 imágenes.')
        self.fig(WEEK/'comparaciones/lr001/curvas_comparadas.png','Pérdidas y AP por época. Los puntos señalan los checkpoints elegidos por AP50.',maxheight=11)
        self.p('Con lr001 se alcanza AP50=0,943169 en la época 5; la referencia llega a 0,942506 en la 29. Es aprendizaje más rápido y solo +0,066 puntos en el mejor AP50 del historial. La ejecución completa terminó el 15/10 a las 22:13, incluida la validación, con salida 0.')
        self.page();self.h('11.2. Curvas y resultado del cambio de tasa',2)
        self.p('La pérdida de validación mínima aparece en la época 4, 0,221198, y sube hasta 0,241296 en la 30 mientras la de entrenamiento baja a 0,065661. El AP50 final cae a 0,933178. Hay indicios de sobreajuste después del óptimo temprano: se conserva model_best de la época 5 y no model_last.')
        self.fig(WEEK/'comparaciones/lr001/lr_comparado.png','Tasa usada en cada época. Las bajadas de ReduceLROnPlateau no recuperan el óptimo temprano.',maxheight=5.7)
        self.p('En lr001 se usa 0,001 en épocas 1–10, 0,0001 en 11–16, 0,00001 en 17–22, 0,000001 en 23–28 y 0,0000001 en 29–30. La tasa del experimento con aumento original no bajó. Más épocas con esta ejecución no solucionaron la pérdida de validación.')
        self.table(['Métrica en validación','lr 0,0001','lr 0,001','Cambio pp'],[['AP50 todos','0,9416','0,9433','+0,17'],['AP 0,50:0,95 todos','0,6081','0,6302','+2,21'],['AP75 todos','0,7146','0,7460','+3,14'],['AP50 normales','0,9664','0,9740','+0,76'],['AP50 difficult','0,6341','0,6462','+1,21'],['AP small','0,1074','0,1182','+1,08']],widths=[7,3,3,3],size=9)
        self.caption('Evaluación final de los mejores checkpoints con el mismo procedimiento y conjunto.',tipo='Tabla')
        self.p('El cambio de tasa mejora sobre todo el ajuste de cajas. AP50 ya era alto y su incremento es pequeño. La ganancia modesta en objetos pequeños motivó el experimento de resolución de los apartados 11.5 y 11.6.')
        self.page();self.h('11.3. Errores umbral y coste de inferencia',2)
        self.table(['Confianza e IoU ≥0,5','lr 0,0001','lr 0,001','res1024'],[['TP / FN','1478 / 83','1478 / 83','1493 / 68'],['FN normales / difficult','20 / 63','18 / 65','12 / 56'],['FP frente a etiquetas','210','190','324'],['Precisión','0,8756','0,8861','0,8217'],['Recall total','0,9468','0,9468','0,9564'],['Recall difficult','0,7529','0,7451','0,7804'],['F1','0,9098','0,9155','0,8840']],widths=[6.4,3.2,3.2,3.2],size=9)
        self.caption('Recuento a un umbral fijo; no debe confundirse con el AP.',tipo='Tabla')
        self.p('El cambio de tasa reduce 20 FP y detecta dos normales adicionales, pero pierde dos difficult más; el TP total no cambia. Que AP difficult suba a 0,6462 mientras baja su recall a confianza 0,5 es compatible: el AP recorre confianzas y también depende de la ordenación y las cajas.')
        self.fig(WEEK/'resultados_test/faster_rcnn_v1_aug_lr001_val/umbral_confianza.png','Precisión exhaustividad y F1 de lr001 en la rejilla de confianzas de validación.',maxheight=8.5)
        self.p('El mejor F1 muestreado pasa de 0,95 a 0,85 con lr001 y vuelve a 0,95 con res1024. La rejilla termina en 0,95 y no determina el óptimo exacto. A confianza 0,5, res1024 detecta 15 robots más, nueve difficult, pero añade 134 FP y reduce F1. La latencia individual sube de 75,1 a 121,6 ms; no incluye captura, red ni actuación.')
        self.page();self.h('11.4. Comparación por secuencia',2)
        self.table(['Secuencia','AP50 antes','AP50 lr001','FN antes → después'],[['2023 GR04 0008','0,9876','0,9886','2 → 2'],['2024 GR02 0001','0,9393','0,9380','1 → 0'],['2024 GR02 0007','0,9877','0,9873','1 → 1'],['2024 GR02 0008','0,9864','0,9782','0 → 0'],['2024 GR04 0002','0,9817','0,9844','0 → 0'],['2024 GR04 0003','0,8131','0,8096','6 → 6'],['2025 GR01 0002','0,9719','0,9775','2 → 3'],['2025 GR01 0010','0,9049','0,9404','4 → 1'],['2025 GR03 0007','0,9661','0,9678','8 → 9'],['2025 GR03 0011','0,8465','0,8473','30 → 28'],['2025 GR04 0011','0,9280','0,9290','29 → 33']],widths=[5.1,3,3,4.9],size=9)
        self.caption('Secuencias de validación comparadas con las mismas etiquetas.',tipo='Tabla')
        self.fig(WEEK/'comparaciones/lr001/secuencias_comparadas.png','Cambio de AP50 por secuencia en puntos porcentuales.',maxheight=7.8)
        self.p('AP50 mejora en 7 de 11 secuencias y baja en 4. GR01_0010 de 2025 gana 3,55 puntos y reduce sus FN de 4 a 1. En GR04_0011 de 2025 aumentan de 29 a 33 los FN y de 25 a 28 los difficult perdidos. GR04_0003 de 2024 sigue perdiendo sus seis difficult; el cambio de tasa no resuelve ese caso.')
        self.resolucion()
        self.page();self.h('12. Análisis cualitativo')
        self.p('La inspección de las predicciones distingue errores del detector y carencias de las etiquetas. En la figura siguiente se ven cuatro robots, pero el XML de GR02_0001/frame_0444 de 2024 contiene una sola caja. Una detección correcta de los otros tres puede contarse como FP. No se modifican las etiquetas para conservar la comparación.')
        self.fig(FIG/'etiqueta_incompleta.png','Caso confirmado de anotación incompleta. La caja azul es la única del XML.',maxheight=8.7)
        self.p('Esto limita la interpretación de los 190 FP de lr001 y los 324 de res1024, y de precisión, F1 y AP. No se ha cuantificado la extensión del problema ni se atribuyen todos los FP a omisiones. GR02_0001 pasa de 49 a 71 FP frente a etiquetas; no son necesariamente errores visuales nuevos.')
        self.fig(WEEK/'comparaciones/res1024/ejemplo_errores_res1024.png','Res1024 en PIDS2025_GR03_0011/frame_0600: TP 4, FP 4 y FN 1 frente a las etiquetas; rojo indica detección sin pareja.',width=12,maxheight=6)
        self.p('La muestra de res1024 incluye una caja roja sobre una pierna y varias cajas solapadas en torno a un objetivo: las etiquetas omitidas no explican todos los errores. Los difficult concentran 65/83 FN de lr001 y 56/68 de res1024. Su recall al umbral 0,5 mejora, pero no su AP50 agregado; el flag agrupa tamaños, oclusión y movimiento.')
        self.page();self.h('12.1. Conclusiones y trabajo pendiente',2)
        self.p('Se conserva provisionalmente lr=0,001 a resolución 800/1333 y el checkpoint de la época 5 como referencia: mejora AP agregado, ajuste de cajas y FP frente a lr=0,0001, con una latencia similar. La diferencia de +0,17 puntos en AP50 con una única semilla no prueba una mejora estable; tampoco hay mejora uniforme en difficult al umbral fijo.')
        self.p('Se han completado cuatro entrenamientos y su evaluación en validación. La resolución mayor aporta +7,04 puntos de AP small y reduce 15 FN, pero aumenta FP y latencia y baja AP 0,50:0,95 en el checkpoint seleccionado. Se conserva lr001 a resolución original como referencia por su equilibrio; res1024 queda como alternativa si prima detectar pequeños y se acepta ese coste.')
        self.p('La selección por AP50 tiene consecuencias: en res1024 el máximo AP 0,50:0,95 del historial está en la época 5, no en la 2 elegida. No se ha reevaluado otro checkpoint ni se concluye que la resolución empeore siempre el ajuste de cajas. Una semilla y el cambio de microbatch impiden aislar completamente su efecto.')
        self.p('Falta comparar arquitecturas y evaluar el modelo definitivo en test; la fase 2 sigue siendo un avance. Como experimento posterior se plantea una ampliación dirigida a difficult, con los demás parámetros fijos. Los perfiles de sombras, lluvia y oclusión están preparados, pero no participan en estos resultados. Se limita la selección sobre validación y test se reserva para una única evaluación final.')

    def resolucion(self):
        self.page();self.h('11.5. Resolución y evolución del entrenamiento',2)
        self.p('La propuesta de Alejandro se ejecutó desde COCO con lr=0,001 y aumento base, elevando min_size/max_size de 800/1333 a 1024/1820. Un frame pasa aproximadamente de 1333 × 750 a 1820 × 1024, un 86 % más de píxeles. Para memoria se usaron microbatch 4 y acumulación 2, frente a lote físico 8. No son idénticos numéricamente: pueden cambiar propuestas y redondeos.')
        self.fig(WEEK/'comparaciones/res1024/curvas_comparadas.png','Misma semilla y datos. Los puntos marcan el máximo AP50 de cada historial, no el máximo AP promedio.',maxheight=10)
        self.p('El mejor AP50 de res1024 es 0,946440 en la época 2. Su AP 0,50:0,95 es 0,605390; el máximo de esta otra métrica aparece en la época 5, con 0,632233 y AP50 0,942070. Se respeta el criterio predefinido AP50 y se evalúa model_best de la época 2, sin seleccionar retrospectivamente por otra métrica.')
        self.p('La pérdida de validación mínima es 0,215909 en la época 3 y termina en 0,232343, mientras la de entrenamiento baja a 0,073149. El AP50 final cae a 0,933510. Hay indicios de sobreajuste y estancamiento tras el óptimo temprano. ReduceLROnPlateau usa 0,001 en 1–9, 0,0001 en 10–15, 1e−5 en 16–21, 1e−6 en 22–27 y 1e−7 en 28–30; no recupera el máximo.')
        self.p('Entrenamiento y validación finalizaron el 16/10 hacia las 08:45 Europe/Madrid, salida 0, unas nueve horas desde el lanzamiento. El máximo de 8482 MiB reservados corresponde al preflight, no a una medición del pico de las 30 épocas. Se conservan conjuntos, scheduler y aumento; no se ha evaluado test.')
        self.page();self.h('11.6. Resultado y coste de la resolución',2)
        self.table(['Mejor por AP50 en validación','lr001 800','lr001 1024','Cambio pp'],[['AP50 todos','0,9433','0,9465','+0,32'],['AP 0,50:0,95 todos','0,6302','0,6047','−2,55'],['AP75 todos','0,7460','0,6990','−4,70'],['AP50 difficult','0,6462','0,6282','−1,80'],['AP small','0,1182','0,1886','+7,04'],['AP large','0,6919','0,6459','−4,60']],widths=[7,3,3,3],size=9)
        self.caption('Evaluación final del checkpoint seleccionado. El historial se presenta por separado.',tipo='Tabla')
        self.fig(WEEK/'comparaciones/res1024/precision_y_coste.png','La mejora de pequeños convive con retrocesos en otras métricas y mayor latencia individual.',maxheight=5.3)
        self.p('La inferencia individual tarda 121,6 frente a 75,1 ms, +61,9 %, aproximadamente 8,2 frente a 13,3 imágenes/s solo de inferencia. En lote son 120,5 frente a 72,7 ms/imagen, pero con lotes distintos de 4 y 8. La comparación individual es más directa; ninguna cifra mide la demo completa.')
        self.fig(WEEK/'comparaciones/res1024/secuencias_comparadas.png','Cambio de AP50 frente a lr001 a resolución original; escala en puntos porcentuales.',maxheight=5.5)
        self.p('AP50 mejora en 4 secuencias, baja en 6 y empata en una. GR03_0011 de 2025 gana 4,16 puntos y reduce FN de 28 a 22. GR04_0011 de 2025 reduce FN de 33 a 25, pero FP sube de 28 a 58. GR01_0002 de 2025 pierde 1,20 puntos. GR04_0003 de 2024 sigue perdiendo sus seis difficult. El CSV complementario conserva todas las secuencias.')

    def terminar(self):
        if self.modo=='completo':
            self.page()
            for title in ['13. Módulos del robot','14. El circuito','15. Estrategia de búsqueda y detección','16. Funcionalidades adicionales','17. La demostración final','18. Limitaciones y trabajo futuro']:
                self.h(title);self.p('Pendiente del Bloque 3. No se han realizado ni medido todavía estas funciones en el circuito definitivo.')
        self.page();self.h('Referencias')
        for t in ['[1] labelImg. Herramienta de anotación PascalVOC. https://github.com/HumanSignal/labelImg',
                  '[2] Albumentations 1.4.18. Código de transformaciones. https://github.com/albumentations-team/albumentations/tree/1.4.18',
                  '[3] S. Ren et al. Faster R-CNN Towards Real-Time Object Detection with Region Proposal Networks. 2015. https://arxiv.org/abs/1506.01497',
                  '[4] torchvision 0.19. Faster R-CNN ResNet-50 FPN. https://docs.pytorch.org/vision/0.19/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn.html',
                  '[5] Repositorio del grupo. Datos, criterios, notebooks y resultados. https://github.com/javiersaguar/PIDS-Proyecto2']:
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
    for modo in ['fase1','fase2','completo']:
        informe=Informe(modo)
        if modo in ['fase1','completo']:informe.fase1()
        if modo=='completo':informe.page()
        if modo in ['fase2','completo']:informe.fase2()
        informe.terminar()


if __name__=='__main__':main()
