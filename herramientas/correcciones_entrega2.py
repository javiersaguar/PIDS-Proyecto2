"""Correcciones de la revisión de la entrega 2 sobre los Bloques 1 y 2 de la memoria.

La memoria de la entrega 2 (docs/informes/informe_entrega2.docx) se editó a mano en Word y no
se toca. generar_entrega3.py hace una copia, le añade el Bloque 3 y llama a aplicar(), que:

- responde a los comentarios obligatorios C2.1 a C2.8 y a los opcionales del PDF corregido
  (PIDS_grupo2_entrega2.pdf, páginas 14 a 18);
- cambia la Figura 9 por un esquema de bloques y añade la curva precisión-exhaustividad como
  Figura 10, con lo que las figuras siguientes suben un número;
- pasa tasas, weight decay y mínimos del programador a notación científica;
- añade la columna del Bloque 3 al reparto y las referencias [22] a [28];
- sustituye la tabla de respuesta a la revisión por la de la entrega 2.

Los textos usan el formato de generar_entrega3.runs: **negrita**, __entradilla__ (cursiva
subrayada, como «Batch size (tamaño del lote).») y ^superíndice^. Cada búsqueda exige un
único párrafo o tabla que coincida, para que un cambio en la memoria de partida falle en vez
de corregir el sitio equivocado.
"""
import os
import re
from copy import deepcopy

from docx.oxml.ns import qn
from docx.shared import Cm
from docx.text.paragraph import Paragraph

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(RAIZ, 'docs', 'informes', 'figuras')


# --- textos ---------------------------------------------------------------------------------
DIFFICULT_VAL_TEST = (
    'Los difficult de validación y test los marcamos nosotros, porque venían todos sin marcar. Con los '
    'criterios de nuestras etiquetas (Tabla 4), se marcaron directamente los 48 robots de menos de 30 '
    'píxeles de ancho y se revisaron a ojo, recortados y ampliados, los 930 que estaban cortados por el '
    'borde, tapados al menos un 30 % por otro robot o poco nítidos; de ellos se marcaron 477. Las cajas '
    'no se tocaron. Así se puede medir el detector por separado en los casos difíciles, que es donde '
    'más falla (apartado 11).')

SISTEMA = [
    'La Figura 9 resume el sistema: cada bloque es un módulo y cada flecha, los datos que pasan al '
    'siguiente.',
    '**Datos de entrenamiento.** Reúne las imágenes originales y aumentadas con sus anotaciones y '
    'entrega cada imagen con la lista de sus robots: la posición de cada caja y su clase.',
    '**Carga en lotes.** Convierte cada imagen en una matriz de valores entre 0 y 1, baraja el '
    'conjunto en cada época y agrupa las imágenes en lotes de 8 con sus cajas.',
    '**Detector.** Normaliza y reescala cada imagen (apartado 9), extrae sus características y '
    'devuelve cajas candidatas con su confianza de ser un robot (apartado 8).',
    '**Función de pérdida.** Compara esas cajas con las anotadas y mide tres errores: el de las '
    'regiones propuestas, el de la clase (robot o fondo) y el de la posición de cada caja. Su suma es '
    'la pérdida, y la retropropagación calcula cuánto contribuye cada peso a ella: el gradiente.',
    '**Optimizador SGD [22].** Mueve cada peso en contra de su gradiente, con un paso proporcional a '
    'la tasa de aprendizaje, y devuelve los pesos nuevos al detector. Su programador baja la tasa '
    'cuando la pérdida de validación se estanca.',
    '**Evaluación en validación.** Al final de cada época aplica el detector, sin modificar sus pesos, '
    'a las imágenes de validación, de secuencias que no ha visto, y devuelve la pérdida de validación '
    'y el AP@0,5.',
    '**Selección del modelo.** Conserva los pesos de la época con mayor AP@0,5 y fija el umbral de '
    'confianza con el mejor F1 en validación (apartado 11.6).',
    '**Evaluación en test.** Aplica una sola vez el modelo elegido, con su umbral, a las imágenes de '
    'test y da las métricas finales (apartado 10).',
]

BACKBONE = (
    'Un detector está formado por un backbone, la red convolucional (ResNet-50 [11], MobileNetV3 [13] o '
    'VGG16 [14]) que extrae características de la imagen, y por las partes que localizan y clasifican los '
    'objetos. Se distingue el backbone porque se puede intercambiar entre modelos, influye mucho en el '
    'coste computacional y cuenta con pesos preentrenados.')
FPN = (
    'Casi todos añaden un cuello FPN [12] entre el backbone y esas partes. El backbone produce mapas '
    'de características cada vez más pequeños: los primeros conservan el detalle espacial y los '
    'últimos, más información sobre qué hay en la imagen. La FPN los recorre de arriba abajo: amplía '
    'cada mapa profundo al tamaño del nivel anterior y lo suma a ese nivel, adaptado con una convolución '
    'de 1 × 1. El resultado es una pirámide de mapas que tienen todos información sobre qué hay, cada '
    'uno con su resolución, y cada robot se busca en el nivel adecuado a su tamaño: los lejanos en los '
    'mapas grandes y los cercanos en los pequeños.')
ETAPAS = (
    'Los modelos son de dos etapas o de una (Tabla 12). Los de dos etapas, como Faster R-CNN [3], '
    'primero generan con una red de propuestas (RPN) unas mil regiones que pueden contener un objeto, '
    'y después recortan las características de cada región y las clasifican y ajustan una a una. Los de '
    'una etapa, como RetinaNet [9] y SSD [10], no usan propuestas: en cada posición de los mapas de '
    'características colocan cajas de referencia (anclas) de varios tamaños y predicen de una sola vez '
    'la clase y el ajuste de todas. Los de dos etapas suelen localizar mejor, porque la segunda etapa '
    'trabaja con pocas regiones ya filtradas; los de una etapa son más sencillos y, en general, más '
    'rápidos, pero deben distinguir unos pocos objetos entre decenas de miles de anclas de fondo, el '
    'desequilibrio que compensa la pérdida focal de RetinaNet. En nuestras medidas, con el mismo '
    'backbone, la diferencia de tiempo es pequeña (Tabla 16): pesa más el tamaño del backbone y de la '
    'imagen.')

LOTE = [
    '__Batch size (tamaño del lote).__ El gradiente de cada paso se calcula con las imágenes del lote y '
    'no con todo el conjunto, así que es una estimación del gradiente verdadero. Como es la media de '
    'los gradientes de cada imagen, su dispersión baja con la raíz cuadrada del tamaño del lote: con una '
    'imagen, cada paso sigue a esa imagen y la dirección cambia mucho de un paso a otro; con 32, las '
    'particularidades de cada imagen se compensan. Ese ruido tiene dos caras. Con moderación es bueno: '
    'actúa como regularización y ayuda a salir de mínimos estrechos, que generalizan peor [24], y un '
    'lote pequeño da además más actualizaciones por época. En exceso es malo, porque obliga a usar '
    'tasas bajas para que el entrenamiento no se vuelva inestable. Un lote grande da gradientes más '
    'fiables y aprovecha mejor la GPU, pero necesita más memoria, da menos pasos por época y suele '
    'requerir subir la tasa en proporción [25].',
    'En las pruebas cortas (Tabla 22, Anexo D), con lotes de 1 y 2 el AP@0,5 sube antes, porque hay '
    'más pasos por época, pero baja en la tercera época; con 8 sube de forma más regular, y los tres '
    'terminan a menos de 0,4 pp. Los lotes de 16 y 32 no caben en los 12 GB de la GPU. Se elige 8 porque '
    'es el mayor que cabe: da gradientes estables con la tasa de 10^−3^ y unos 400 pasos por época con '
    'las 3184 imágenes. Faster R-CNN v2 y el experimento a 1024 píxeles no caben con 8, así que usan '
    'microlotes de 4 y suman los gradientes de dos microlotes antes de cada paso: el lote efectivo '
    'sigue siendo 8. Se prueban, por orden, microlotes de 8, 4 y 2, que son los que dividen a 8, y se '
    'usa el primero que cabe. Con 6, los pasos tendrían 6 o 12 imágenes y no serían comparables con los '
    'del resto de modelos.',
]
TASA = (
    '__Learning rate (tasa de aprendizaje).__ Determina el tamaño de los pasos que se dan al '
    'actualizar los pesos. Una tasa demasiado alta hace que los pasos se pasen del mínimo: el '
    'entrenamiento se vuelve inestable y puede divergir, como con 10^−1^, cuya pérdida acaba en NaN '
    '(Tabla 23). Una tasa demasiado baja da pasos tan cortos que el modelo apenas avanza: necesita '
    'muchas más épocas para llegar al mismo resultado, puede quedarse estancado en zonas planas de la '
    'pérdida y, con un número de épocas fijo, acaba sin haber aprendido lo suficiente (infraajuste). Con '
    '10^−5^, tras tres épocas el AP@0,5 no llega a 0,03 (Tabla 23), y con 10^−4^ el mejor checkpoint '
    'llega en la época 29, frente a la 5 con 10^−3^. Con 2·10^−3^ el máximo llega en la época 1 o 2 y '
    'después el AP@0,5 baja más de 1 pp. Entre 10^−4^ y 10^−2^ la tasa cambia sobre todo la velocidad '
    'del entrenamiento, no su resultado (apartado 11.4). El programador reduce la tasa cuando la '
    'pérdida de validación deja de mejorar, aunque no siempre lo hace a tiempo para recuperar el mejor '
    'resultado (apartado 11.1).')
EPOCAS_VIEJO = 'Los primeros experimentos usaron 30 épocas y los siete modelos, 12 (15 con lr 0,0005).'
EPOCAS_NUEVO = ('Los primeros experimentos usaron 30 épocas y los experimentos de comparación entre '
                'modelos, 12 (15 con lr 5·10^−4^).')
OPTIMIZADOR = [
    '__Optimizador y programador.__ Se utiliza SGD [22], que actualiza los pesos con el gradiente de '
    'cada lote. El momentum (0,9) [23] acumula una media de los gradientes anteriores, de modo que cada '
    'paso sigue la dirección de unos diez lotes, 1/(1 − 0,9), y no solo la del último: suaviza el ruido '
    'de los lotes pequeños y acelera el avance en las direcciones que se repiten. El weight decay '
    '(5·10^−4^) resta en cada paso una fracción de cada peso; así penaliza los pesos grandes y limita el '
    'sobreajuste. Son los valores del artículo de Faster R-CNN [3] y del tutorial de torchvision para '
    'ajustar detectores [27], y no se cambiaron: por coste, solo se ajustó la tasa, el hiperparámetro '
    'al que el entrenamiento es más sensible. El programador multiplica la tasa por 0,1 cuando la pérdida '
    'de validación lleva 5 épocas sin mejorar. Ese margen evita reaccionar al ruido de una sola época, '
    'pero resultó largo: el mejor checkpoint llega entre las épocas 3 y 7 y la primera bajada, en la 11 '
    '(apartado 11.1).',
    'Una estrategia más sistemática para elegir estos valores sería: primero, una prueba de rango de '
    'la tasa [26], que entrena unos cientos de pasos subiendo la tasa de forma exponencial y elige un '
    'valor un orden de magnitud por debajo del que dispara la pérdida; después, una búsqueda corta en '
    'escala logarítmica alrededor de ese valor, comparando en validación, como la del Anexo D; y, por '
    'último, ajustar la paciencia del programador a la época en que se estanca la validación, aquí 2 o 3 '
    'épocas. El momentum y el weight decay se ajustarían al final, porque sus valores habituales suelen '
    'funcionar en el ajuste fino de detectores. No se probaron otros optimizadores, por lo que no se '
    'puede afirmar que SGD sea superior a las alternativas.',
]
PUNTOS = ('Las diferencias entre dos valores de AP, precisión o F1 se dan en puntos porcentuales (pp): '
          'de 0,9433 a 0,9465 hay 0,32 pp.')
CURVA = (
    'La Figura 10 muestra la curva del modelo final y la de Faster R-CNN MobileNet en test. Cada punto '
    'es un umbral de confianza: al bajarlo, el detector acepta más cajas, encuentra más robots (más '
    'exhaustividad) y comete más falsos positivos (menos precisión). Un detector ideal estaría en la '
    'esquina superior derecha. La curva del modelo final queda por encima y a la derecha de la de '
    'MobileNet en todo el recorrido; por eso su AP es mayor.')
PIE_CURVA = ('Figura 10. Curva precisión-exhaustividad en test (IoU ≥ 0,5), con umbrales de confianza de '
             '0,05 a 0,95. El círculo blanco marca el umbral fijado en validación.')

# Apartado 11: nombres que dicen qué cambia y tendencias en vez de valores (comentario opcional).
EXPERIMENTOS = (
    'Los experimentos se organizaron en tres fases. Primero, con un único modelo, Faster R-CNN v1 (el '
    'de partida que propone el enunciado), se fijaron los hiperparámetros para no multiplicar el coste: '
    'con y sin aumento de datos, tasa baja (10^−4^) o alta (10^−3^) e imagen normal o grande (apartados '
    '11.1 y 11.2). Después, con esos hiperparámetros, se compararon las siete arquitecturas (11.3) y '
    'se probaron tres tasas con las tres mejores (11.4). Por último, se comprobó con SSD300 si faltaban '
    'épocas (11.5) y se evaluó cada modelo en test una sola vez (11.6).')
TABLA14 = [
    ['Experimento', 'Mejor época', 'AP@0,5 al entrenar', 'AP@0,5 al evaluar', 'AP 0,50:0,95'],
    ['Sin aumento, tasa baja (10^−4^)'],
    ['Con aumento, tasa baja (10^−4^)'],
    ['Con aumento, tasa alta (10^−3^)'],
    ['Con aumento, tasa alta, imagen grande'],
]
PIE14 = ('Tabla 14. Experimentos de ajuste con Faster R-CNN v1 en validación, con el mejor checkpoint por '
         'AP@0,5. «Al entrenar» es el AP que se calcula al final de cada época y «al evaluar», el de la '
         'evaluación posterior de ese checkpoint.')
AUMENTO_TASA = (
    'El aumento de datos es lo que más mejora a Faster R-CNN v1, sobre todo en los robots difficult '
    '(Tabla 14), aunque parte de la mejora puede deberse a que el aumento cuadruplica las imágenes y las '
    'actualizaciones. Con la tasa alta, el AP@0,5 es el mismo, las cajas se ajustan algo mejor (AP '
    '0,50:0,95) y el mejor checkpoint llega seis veces antes, en la época 5 en vez de la 29.')
SOBREAJUSTE = (
    'Con la tasa alta, la pérdida de validación toca su mínimo en la época 4 y después sube, mientras la '
    'de entrenamiento sigue bajando (Figura 11): el modelo se ajusta cada vez más a las imágenes de '
    'entrenamiento y empeora en las que no ha visto, es decir, sobreajusta. Por eso se conserva el mejor '
    'checkpoint y no el último. El programador baja la tasa por primera vez en la época 11 (Figura 21, '
    'Anexo C), demasiado tarde para recuperar el mejor resultado.')
RESOLUCION = (
    'Los vídeos se graban a 1280 × 720 píxeles, igual que los de validación y test. Antes de analizar '
    'cada imagen, Faster R-CNN y RetinaNet la reescalan sin deformarla con dos límites: el lado corto '
    'pasa a 800 píxeles, salvo que entonces el largo supere los 1333. En una imagen de 16:9 manda el '
    'segundo límite y la imagen entra a 1333 × 750, apenas un 4 % más grande que la original. Como los '
    'robots lejanos seguían detectándose mal, se subieron los límites a 1024 y 1820, sin cambiar nada '
    'más: la imagen entra entonces a 1820 × 1024, un 86 % más de píxeles. Por memoria, este experimento '
    'usó microlotes de 4 imágenes con dos acumulaciones de gradientes.')
RESOLUCION_TABLA = ('Imágenes de 1280 × 720. Faster R-CNN y RetinaNet las reescalan a 1333 × 750 (lado '
                    'corto a 800 salvo que el largo pase de 1333) y a 1820 × 1024 en el experimento de '
                    'resolución. SSD300 y SSDlite320, a 300 × 300 y 320 × 320.')
RESOLUCION_COMPARA = (
    'Con la imagen grande se detectan más robots pequeños y difficult, pero aparecen muchos más falsos '
    'positivos, las cajas se ajustan peor, baja el F1 y cada imagen tarda un 60 % más (Tabla 15).')
RESOLUCION_DECIDE = (
    'Con el criterio fijado de antemano, el AP@0,5, la ganancia es demasiado pequeña para compensar esos '
    'costes, así que se mantiene la imagen normal, que además gana en 7 de las 11 secuencias de '
    'validación.')
ARQUITECTURAS = (
    'Faster R-CNN v2 obtiene el mejor AP@0,5 (Tabla 16), aunque los cuatro modelos con ResNet-50 quedan '
    'a menos de 1,2 pp entre sí, una diferencia que no es concluyente con una sola semilla. Faster R-CNN '
    'llega a su máximo en pocas épocas y después empeora mientras la pérdida de entrenamiento sigue '
    'bajando: sobreajusta pronto. RetinaNet empieza más despacio, pero es más estable. SSD300 todavía '
    'mejoraba en la última época (apartado 11.5).')
LIGEROS = (
    'Los modelos ligeros cambian precisión por velocidad (Figura 13). Faster R-CNN MobileNet es seis veces '
    'más rápido que la v2 y pierde poco AP@0,5; SSDlite320 es el más rápido, pero con imágenes de '
    '320 × 320 pierde los robots lejanos.')
DIFFICULT_ARQ = ('Ninguna arquitectura resuelve los difficult: en todas, su AP@0,5 queda muy por debajo del de '
                 'los robots normales. Los 13 entrenamientos suman 21,8 horas de GPU.')
SIN_AUMENTO = (
    '__Pruebas sin aumento (Anexo D).__ A diferencia de lo que propone el enunciado, todos los modelos se '
    'entrenaron con aumento, que ya mejoraba Faster R-CNN v1 (apartado 11.1). Sin él, Faster R-CNN v2 '
    'sigue siendo la mejor (Tabla 21). Con Faster R-CNN v1, los lotes de 16 y 32 no caben en la memoria '
    'de la GPU (Tabla 22) y con una tasa de 10^−1^ el entrenamiento diverge (Tabla 23).')
TASAS = (
    'La tasa apenas cambia el AP@0,5 de los tres modelos (Tabla 17): las diferencias, de menos de 0,22 pp, '
    'son demasiado pequeñas para distinguirlas con una sola semilla. Se mantiene 10^−3^ porque iguala a '
    '5·10^−4^ en menos épocas. Con 2·10^−3^, Faster R-CNN llega a su máximo en una o dos épocas y después '
    'empeora mientras sube la pérdida de validación: inestabilidad y sobreajuste, no falta de '
    'entrenamiento.')
PERFIL = ('El perfil de aumento con sombras, llovizna y más imágenes difficult da prácticamente el mismo '
          'AP@0,5 que el aumento base, así que se mantiene el base.')
SSD40 = (
    'Las 28 épocas adicionales bajan la pérdida de entrenamiento, pero el AP@0,5 en validación no se mueve '
    'y la pérdida de validación sube desde la época 8, pese a las bajadas de la tasa: es el mismo '
    'sobreajuste que en Faster R-CNN (apartado 11.1), no falta de épocas. Solo mejora algo el ajuste de '
    'las cajas. Como triplica el tiempo, no se repitió con el resto de modelos, cuyo mejor checkpoint '
    'está entre las épocas 3 y 7.')
FINAL = (
    'Faster R-CNN v2 con tasa 10^−3^ es el modelo final: en test obtiene prácticamente el mismo AP@0,5 que '
    'en validación, muy alto en los robots normales y bastante más bajo en los difficult (Tabla 18). Con '
    'el umbral de 0,95 detecta 1606 de los 1721 robots (apartado 10), y su F1 queda a menos de 0,3 pp del '
    'mejor posible en test. En general, test confirma validación: los modelos con ResNet-50 apenas '
    'cambian y las SSD pierden más.')
RAPIDO = ('Para la demo, Faster R-CNN MobileNet es una alternativa más rápida: pierde algo de precisión, '
          'pero tarda seis veces menos por imagen.')

REPARTO_B3 = {
    'Integrante': 'Tareas del Bloque 3',
    'Javier Saguar': 'Demo del circuito: desplazamientos, puntería, disparo, ataques en marcha y robot '
                     'camuflado. Kit del rival móvil, interfaz del mando y memoria del Bloque 3.',
    'Alejandro Cuevas': 'Seguimiento de rivales en movimiento, barrido continuo de la torreta, memoria de '
                        'robots atacados y vigilancia del recorrido.',
}

REFERENCIAS = [
    '[22] H. Robbins y S. Monro. A Stochastic Approximation Method. The Annals of Mathematical Statistics, '
    '22(3), 1951. https://doi.org/10.1214/aoms/1177729586',
    '[23] I. Sutskever et al. On the importance of initialization and momentum in deep learning. ICML, 2013. '
    'https://proceedings.mlr.press/v28/sutskever13.html',
    '[24] N. S. Keskar et al. On Large-Batch Training for Deep Learning: Generalization Gap and Sharp Minima. '
    '2017. https://arxiv.org/abs/1609.04836',
    '[25] P. Goyal et al. Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour. 2017. '
    'https://arxiv.org/abs/1706.02677',
    '[26] L. N. Smith. Cyclical Learning Rates for Training Neural Networks. 2017. '
    'https://arxiv.org/abs/1506.01186',
    '[27] PyTorch. TorchVision Object Detection Finetuning Tutorial. '
    'https://docs.pytorch.org/tutorials/intermediate/torchvision_tutorial.html',
    '[28] DJI. RoboMaster SDK. Documentación. https://robomaster-dev.readthedocs.io/',
]

RESPUESTA = (
    'La Tabla 28 recoge los comentarios de la revisión de la entrega 2 y dónde se ha incorporado cada '
    'corrección. Las de la entrega 1 se recogieron en la memoria de la entrega 2.')
PIE_RESPUESTA = 'Tabla 28. Trazabilidad de las correcciones respecto a la entrega 2.'
FILAS_RESPUESTA = [
    ['#', 'Comentario recibido', 'Sección', 'Cambio realizado'],
    ['1', 'C2.1. Describir el sistema con un esquema de bloques de alto nivel (módulos y sus entradas y '
          'salidas) y explicar cómo cada módulo transforma sus datos.', '7',
     'La Figura 9 es ahora un esquema con solo los módulos y los datos que pasan entre ellos, y el texto '
     'explica qué hace cada módulo con sus entradas.'],
    ['2', 'C2.2. Citar SGD.', '7 y 9', 'Se citan SGD [22] y el momentum [23].'],
    ['3', 'C2.3. Explicar la diferencia entre modelos de una y dos etapas.', '8',
     'Nuevo párrafo: propuestas y clasificación región a región frente a predicción directa sobre anclas, '
     'con las ventajas de cada uno.'],
    ['4', 'C2.4. Profundizar en el batch size y usarlo para justificar el valor elegido.', '9',
     'Se explica por qué un lote pequeño da gradientes más variables, cuándo es bueno y cuándo malo [24, '
     '25], y se justifica el lote de 8 con las pruebas de la Tabla 22.'],
    ['5', 'C2.5. ¿Qué puede hacer una tasa de aprendizaje muy baja?', '9',
     'Convergencia lenta e infraajuste con un número fijo de épocas, con los ejemplos de 10^−5^ y 10^−4^.'],
    ['6', 'C2.6. Justificar momentum, weight decay y programador, o explicar una estrategia para elegirlos.',
     '9', 'Qué hace cada uno, de dónde salen los valores [3, 27], por qué la paciencia de 5 épocas resultó '
          'larga y una estrategia de ajuste con la prueba de rango de la tasa [26].'],
    ['7', 'C2.7. Añadir una imagen de la curva precisión-exhaustividad con resultados reales.', '10',
     'Nueva Figura 10: curvas en test del modelo final y de Faster R-CNN MobileNet.'],
    ['8', 'C2.8. Explicar las resoluciones (800/1333) frente a los 1280 × 720 de grabación.', '9 y 11.2',
     'Se explica el reescalado con lado corto y lado largo máximos: 1280 × 720 entra a 1333 × 750 y, en el '
     'experimento de resolución, a 1820 × 1024.'],
    ['9', '¿Se etiquetaron como difficult las imágenes de validación y test?', '7',
     'Sí: se explica cómo se marcaron sus 525 difficult, que venían sin marcar.'],
    ['10', 'Explicación deficiente de la FPN.', '8',
     'Se explica el recorrido de arriba abajo, las conexiones laterales y la elección del nivel según el '
     'tamaño del robot.'],
    ['11', '«Permite acelerar la convergencia del modelo».', '8', 'Corregido.'],
    ['12', '¿Por qué microlotes de 4 y no de 6?', '9',
     'Los microlotes deben dividir a 8 para que todos los pasos tengan 8 imágenes; 4 es el mayor que cabe.'],
    ['13', 'Usar notación científica.', '9, 11 y anexos',
     'Tasas, weight decay y mínimos del programador en notación científica.'],
    ['14', '¿«Puntos» = %?', '10', 'Se definen los puntos porcentuales (pp) y se usan en el Bloque 2.'],
    ['15', '«Los experimentos de comparación entre modelos».', '9', 'Corregido.'],
    ['16', 'Opcional: nombres autoexplicativos para los experimentos y tendencias en vez de valores exactos.',
     '11', 'Los experimentos de la Tabla 14 se nombran por lo que cambian y el apartado 11 compara '
           'tendencias; los valores quedan en las tablas.'],
]

# Notación científica: tasas, weight decay y mínimos del programador.
NOTACION = {'0,0001': ('10', '−4'), '0,0005': ('5·10', '−4'), '0,0010': ('10', '−3'),
            '0,0020': ('2·10', '−3'), '0,001': ('10', '−3'), '0,002': ('2·10', '−3'),
            '1e−10': ('10', '−10'), '1e−7': ('10', '−7'), '1e−5': ('10', '−5')}
PATRON_NOTACION = re.compile(r'(?<![\d,])(' + '|'.join(re.escape(k) for k in sorted(NOTACION, key=len, reverse=True))
                             + r')(?!\d)')


# --- utilidades ------------------------------------------------------------------------------
def texto(el):
    return ''.join(t.text or '' for t in el.iter(qn('w:t')))


class Memoria:
    def __init__(self, doc, xml):
        self.doc, self.x = doc, xml
        self.body = doc.element.body
        self.padre = doc.paragraphs[0]._parent

    def parrafo(self, inicio):
        hechos = [el for el in self.body if el.tag == qn('w:p') and texto(el).strip().startswith(inicio)]
        if len(hechos) != 1:
            raise SystemExit(f'Se esperaba un párrafo que empiece por «{inicio}» y hay {len(hechos)}')
        return hechos[0]

    def tabla(self, inicio):
        hechos = [el for el in self.body if el.tag == qn('w:tbl')
                  and texto(el.find(qn('w:tr'))).startswith(inicio)]
        if len(hechos) != 1:
            raise SystemExit(f'Se esperaba una tabla cuya cabecera empiece por «{inicio}» y hay {len(hechos)}')
        return hechos[0]

    def nuevo(self, t, estilo=None):
        if estilo == 'pie':
            return self.x.parrafo(t, 'Descripcin', '<w:keepLines/>')
        return self.x.parrafo(t)

    def sustituir(self, inicio, *textos, estilo=None):
        viejo = self.parrafo(inicio)
        for t in textos:
            viejo.addprevious(self.nuevo(t, estilo))
        viejo.getparent().remove(viejo)

    def detras(self, inicio, *textos, estilo=None):
        ancla = self.parrafo(inicio)
        for t in reversed(textos):
            ancla.addnext(self.nuevo(t, estilo))

    def quitar(self, inicio):
        el = self.parrafo(inicio)
        el.getparent().remove(el)

    def imagen(self, ruta, ancho_cm):
        el = self.x.parse_xml(f'<w:p {self.x.W}><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr></w:p>')
        Paragraph(el, self.padre).add_run().add_picture(ruta, width=Cm(ancho_cm))
        return el


def celda(tc, t, plantilla=None):
    """Cambia el texto de una celda conservando el formato de su primer run (o el de «plantilla»);
    admite ^superíndice^."""
    p = tc.find(qn('w:p'))
    rs = p.findall(qn('w:r'))
    if plantilla is not None:
        plantilla = deepcopy(plantilla)
    elif rs:
        plantilla = deepcopy(rs[0])
    else:
        # Celda vacía: run con el formato de la marca de párrafo
        plantilla = p.makeelement(qn('w:r'), {})
        marca = p.find(qn('w:pPr'))
        marca = marca.find(qn('w:rPr')) if marca is not None else None
        if marca is not None:
            plantilla.append(deepcopy(marca))
    for r in p.findall(qn('w:r')) + p.findall(qn('w:hyperlink')):
        p.remove(r)
    for parte, sup in trozos(t):
        p.append(run_como(plantilla, parte, sup))


def trozos(t):
    salida = []
    for parte in re.split(r'(\^[^^\s]+\^)', t):
        if parte:
            sup = parte.startswith('^') and parte.endswith('^') and len(parte) > 2
            salida.append((parte[1:-1] if sup else parte, sup))
    return salida


def run_como(plantilla, t, sup=False):
    r = deepcopy(plantilla)
    for hijo in list(r):
        if hijo.tag not in (qn('w:rPr'),):
            r.remove(hijo)
    rpr = r.find(qn('w:rPr'))
    if rpr is None:
        rpr = r.makeelement(qn('w:rPr'), {})
        r.insert(0, rpr)
    for v in rpr.findall(qn('w:vertAlign')):
        rpr.remove(v)
    if sup:
        va = rpr.makeelement(qn('w:vertAlign'), {qn('w:val'): 'superscript'})
        despues = [h for h in rpr if h.tag in (qn('w:rtl'), qn('w:cs'), qn('w:em'), qn('w:lang'),
                                               qn('w:eastAsianLayout'))]
        if despues:
            despues[0].addprevious(va)
        else:
            rpr.append(va)
    wt = r.makeelement(qn('w:t'), {})
    wt.text = t
    wt.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    r.append(wt)
    return r


def renumerar_figuras(body, desde, salto=1):
    """Sube el número de las figuras desde «desde» en pies, texto y tablas (no toca las B3.x)."""
    cambios = 0
    for p in body.iter(qn('w:p')):
        nodos = [t for t in p.iter(qn('w:t'))]
        completo = ''.join(t.text or '' for t in nodos)
        for m in reversed(list(re.finditer(r'Figura\s+(\d+)', completo))):
            n = int(m.group(1))
            if n < desde:
                continue
            ini, fin = m.span(1)
            pos = 0
            for t in nodos:
                largo = len(t.text or '')
                if pos <= ini and fin <= pos + largo:
                    a, b = ini - pos, fin - pos
                    t.text = t.text[:a] + str(n + salto) + t.text[b:]
                    cambios += 1
                    break
                pos += largo
            else:
                raise SystemExit(f'El número de «{m.group(0)}» está partido entre runs: {completo[:80]}')
    return cambios


def notacion_cientifica(body):
    """Parte cada run con una tasa en decimal en «mantisa» + superíndice."""
    cambios = 0
    for r in list(body.iter(qn('w:r'))):
        ts = r.findall(qn('w:t'))
        if len(ts) != 1 or not PATRON_NOTACION.search(ts[0].text or ''):
            continue
        segmentos, ultimo = [], 0
        for m in PATRON_NOTACION.finditer(ts[0].text):
            segmentos.append((ts[0].text[ultimo:m.start()], False))
            base, exp = NOTACION[m.group(1)]
            segmentos += [(base, False), (exp, True)]
            ultimo = m.end()
            cambios += 1
        segmentos.append((ts[0].text[ultimo:], False))
        for t, sup in segmentos:
            if t:
                r.addprevious(run_como(r, t, sup))
        r.getparent().remove(r)
    return cambios


def anadir_columna(tbl, valores, ancho_nueva):
    """Añade una columna al final con el formato de la última; valores por primera celda de cada fila.
    El texto de las filas usa el formato de la primera fila de datos, porque algunas celdas
    de la entrega 2 se editaron a mano con otro tamaño de letra."""
    filas = tbl.findall(qn('w:tr'))
    modelo = filas[1].findall(qn('w:tc'))[-1].find('.//' + qn('w:r'))
    grid = tbl.find(qn('w:tblGrid'))
    cols = grid.findall(qn('w:gridCol'))
    anchos = [int(c.get(qn('w:w'))) for c in cols]
    total = sum(anchos)
    escala = (total - ancho_nueva - anchos[0]) / (total - anchos[0])
    nuevos = [anchos[0]] + [int(a * escala) for a in anchos[1:]]
    nuevos.append(total - sum(nuevos))
    for c, a in zip(cols, nuevos):
        c.set(qn('w:w'), str(a))
    ultima = deepcopy(cols[-1])
    ultima.set(qn('w:w'), str(nuevos[-1]))
    grid.append(ultima)
    for i, tr in enumerate(filas):
        tcs = tr.findall(qn('w:tc'))
        if i and texto(tcs[-1]).strip():
            celda(tcs[-1], texto(tcs[-1]).strip(), modelo)      # mismo tamaño que el resto de la tabla
        nueva = deepcopy(tcs[-1])
        tr.append(nueva)
        for tc, a in zip(tcs + [nueva], nuevos):
            tcpr = tc.find(qn('w:tcPr'))
            tcw = tcpr.find(qn('w:tcW'))
            if tcw is None:
                tcw = tcpr.makeelement(qn('w:tcW'), {})
                tcpr.insert(0, tcw)
            tcw.set(qn('w:w'), str(a))
            tcw.set(qn('w:type'), 'dxa')
        clave = texto(tcs[0]).strip()
        celda(nueva, valores.get(clave, '[PENDIENTE]'), modelo if i else None)
        if clave not in valores:
            for r in nueva.iter(qn('w:r')):
                rpr = r.find(qn('w:rPr'))
                hl = rpr.makeelement(qn('w:highlight'), {qn('w:val'): 'yellow'})
                despues = [h for h in rpr if h.tag in [qn('w:' + n) for n in (
                    'u', 'effect', 'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs', 'em', 'lang', 'eastAsianLayout')]]
                despues[0].addprevious(hl) if despues else rpr.append(hl)


# --- aplicación -----------------------------------------------------------------------------
def aplicar(doc, xml):
    m = Memoria(doc, xml)
    body = m.body

    # La curva precisión-exhaustividad entra como Figura 10: las siguientes suben un número.
    print('Figuras renumeradas:', renumerar_figuras(body, desde=10))

    # 7. El pipeline de entrenamiento (C2.1, C2.2 y difficult de validación y test)
    m.detras('El entrenamiento se realiza con PyTorch', DIFFICULT_VAL_TEST)
    pie9 = m.parrafo('Figura 9.')
    viejo = pie9.getprevious()
    assert viejo.find('.//' + qn('w:drawing')) is not None, 'la Figura 9 debería ir justo antes de su pie'
    viejo.addprevious(m.imagen(os.path.join(FIG, 'sistema_entrenamiento.png'), 16.0))
    viejo.getparent().remove(viejo)
    m.sustituir('Figura 9.', 'Figura 9. Esquema de bloques del entrenamiento y de la evaluación: los módulos y '
                'los datos que pasa cada uno al siguiente.', estilo='pie')
    m.sustituir('La Figura 9 muestra el flujo de entrenamiento', *SISTEMA)
    m.quitar('Al terminar cada época, se evalúa el modelo')

    # 8. Modelos (C2.3, FPN y convergencia)
    m.sustituir('Un detector está formado por un backbone', BACKBONE, FPN, ETAPAS)
    p = m.parrafo('Todos los modelos utilizan transfer learning')
    viejo_fin = 'Además, permite alcanzar el mejor checkpoint en pocas épocas (apartado 11.3).'
    assert viejo_fin in texto(p)
    m.sustituir('Todos los modelos utilizan transfer learning',
                texto(p).replace(viejo_fin, 'Además, permite acelerar la convergencia del modelo (apartado 11.3).'))

    # 9. Hiperparámetros (C2.4, C2.5, C2.6, C2.8, notación y erratas)
    t13 = m.tabla('ParámetroValor aplicado')
    filas = {texto(tr.findall(qn('w:tc'))[0]).strip(): tr.findall(qn('w:tc'))[1] for tr in t13.findall(qn('w:tr'))}
    celda(filas['Épocas y tamaño (lote)'], '12 épocas (30 al inicio; 15 con lr 5·10^−4^); lote efectivo de 8 '
          'imágenes. Faster R-CNN v2 y el experimento a 1024 píxeles, microlotes de 4 × 2.')
    celda(filas['Optimizador'], 'SGD [22] con momentum de 0,9 [23] y weight decay de 5·10^−4^.')
    celda(filas['Resolución (entrada)'], RESOLUCION_TABLA)
    m.sustituir('Batch size (tamaño del lote).', *LOTE)
    m.sustituir('Learning rate (tasa de aprendizaje).', TASA)
    p = m.parrafo('Épocas.')
    assert EPOCAS_VIEJO in texto(p)
    m.sustituir('Épocas.', '__Épocas.__' + texto(p)[len('Épocas.'):].replace(EPOCAS_VIEJO, EPOCAS_NUEVO))
    m.sustituir('Optimizador y programador', *OPTIMIZADOR)

    # 10. Métricas (C2.7 y puntos porcentuales)
    p = m.parrafo('La AP (Average Precision) resume')
    m.sustituir('La AP (Average Precision) resume', texto(p).strip() + ' ' + PUNTOS)
    ancla = m.parrafo('La AP (Average Precision) resume')
    pie = m.nuevo(PIE_CURVA, 'pie')
    ancla.addnext(pie)
    pie.addprevious(m.imagen(os.path.join(FIG, 'curva_pr.png'), 15.0))
    ancla.addnext(m.nuevo(CURVA))

    # 11. Experimentos (comentario opcional) y resolución (C2.8)
    m.sustituir('Los experimentos se organizaron en tres fases', EXPERIMENTOS)
    t14 = m.tabla('ExperimentoMejor época')
    for tr, valores in zip(t14.findall(qn('w:tr')), TABLA14):
        for tc, v in zip(tr.findall(qn('w:tc')), valores):
            celda(tc, v)
    m.sustituir('Tabla 14.', PIE14, estilo='pie')
    m.sustituir('La Tabla 14 compara los cuatro primeros experimentos', AUMENTO_TASA)
    m.sustituir('Con un learning rate de 0,001', SOBREAJUSTE)
    m.sustituir('Como el rendimiento en objetos pequeños', RESOLUCION)
    m.sustituir('La Tabla 15 compara ambas resoluciones', RESOLUCION_COMPARA)
    m.sustituir('Aunque el modelo a 1024 píxeles', RESOLUCION_DECIDE)
    m.sustituir('Faster R-CNN v2 obtiene el mejor AP50', ARQUITECTURAS)
    m.sustituir('Los modelos ligeros sacrifican precisión', LIGEROS)
    m.sustituir('Los 13 entrenamientos suman', DIFFICULT_ARQ)
    m.sustituir('Pruebas sin aumento (Anexo D).', SIN_AUMENTO)
    m.sustituir('La tasa de aprendizaje apenas cambia el AP@0,5', TASAS)
    m.sustituir('También se comparó con los cambios de aumentación', PERFIL)
    m.sustituir('Las 28 épocas adicionales', SSD40)
    m.sustituir('Faster R-CNN v2 con lr 0,001 es el modelo final', FINAL)
    m.sustituir('Para la demo, Faster R-CNN MobileNet', RAPIDO)

    # Anexo D: tasas de la Tabla 23 que no son de la forma 0,00x
    t23 = m.tabla('TasaAP@0,5 en las épocas')
    for tr in t23.findall(qn('w:tr'))[1:]:
        tc = tr.findall(qn('w:tc'))[0]
        t = texto(tc).strip()
        if t in ('0,01', '0,1'):
            celda(tc, {'0,01': '10^−2^', '0,1': '10^−1^'}[t])

    # Reparto con la columna del Bloque 3
    reparto = m.tabla('IntegranteTareas del Bloque 1')
    anadir_columna(reparto, REPARTO_B3, ancho_nueva=2600)
    m.sustituir('Tabla 1. Reparto del trabajo', 'Tabla 1. Reparto del trabajo de los Bloques 1, 2 y 3 entre los '
                'cinco integrantes.', estilo='pie')

    # Referencias [22] a [28], detrás de la [21]
    ancla = m.parrafo('[21]')
    for t in reversed(REFERENCIAS):
        ancla.addnext(xml.parrafo(t, extra='<w:jc w:val="left"/>'))

    # Respuesta a la revisión de la entrega 2
    vieja = m.tabla('#Comentario recibido')
    vieja.addprevious(xml.tabla(FILAS_RESPUESTA))
    vieja.getparent().remove(vieja)
    m.sustituir('La Tabla 28 recoge', RESPUESTA)
    m.sustituir('Tabla 28.', PIE_RESPUESTA, estilo='pie')
    # Párrafos vacíos del final: con la tabla nueva pasarían a una página en blanco
    ultimo = body.findall(qn('w:p'))[-1]
    while not texto(ultimo).strip() and ultimo.find('.//' + qn('w:drawing')) is None:
        anterior = ultimo.getprevious()
        body.remove(ultimo)
        ultimo = anterior

    print('Tasas en notación científica:', notacion_cientifica(body))
    comprobar(body)


def comprobar(body):
    todo = [texto(p) for p in body.iter(qn('w:p'))]
    restos = [t for t in todo if PATRON_NOTACION.search(t)]
    if restos:
        raise SystemExit('Quedan tasas sin notación científica: ' + ' | '.join(r[:80] for r in restos))
    pies = [int(m.group(1)) for t in todo for m in [re.match(r'Figura (\d+)\. ', t)] if m]
    if pies != list(range(1, len(pies) + 1)):
        raise SystemExit(f'Los pies de figura no van seguidos: {pies}')
    print(f'Comprobado: {len(pies)} figuras numeradas del 1 al {len(pies)} y sin tasas en decimal')
