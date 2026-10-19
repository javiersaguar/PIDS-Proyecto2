# Explorador del dataset PIDS

## Plataforma y propósito
Página estática para explorar la distribución por vídeo, la evolución espacial y los robots por fotograma. Funciona sin conexión y al abrir indice.html directamente.

## Alcance
Solo se modifican archivos dentro de interactivos/. Los datos, las muestras de animación, las escalas de color y los cálculos originales se conservan. Los CSV contienen 808 imágenes, 1420 robots y 375 etiquetas difficult.

## Interfaz acordada
Tema claro y recorrido vertical continuo: las tres figuras y sus descripciones se muestran al bajar por la página. No hay menú, pestañas, navegación lateral, portada ni miniaturas. Los selectores dentro de las gráficas eligen vídeos o muestras; no cambian de página.

## Figuras
figuras.css y figuras.js presentan los gráficos existentes con títulos y contexto separados, controles HTML accesibles de reproducción, pausa, avance y selección de muestra. En móvil se apilan los dos mapas y los diez paneles de recuentos. Los marcos comunican su altura al índice y pausan la reproducción al quedar fuera de vista.

## Mantenimiento
Cada HTML de figura carga el estilo y comportamiento compartidos, sin duplicar sus datos. Se mantienen los enlaces a PNG, SVG, PDF y CSV. No hay dependencias de red ni compilación. El generador externo del notebook puede sobrescribir los HTML; su modificación queda fuera del alcance autorizado.
