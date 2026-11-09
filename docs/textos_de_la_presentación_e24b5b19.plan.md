---
name: Textos de la presentación
overview: Reescribir los textos de la presentación para que cada título diga de qué va la diapositiva, quitar las descripciones bajo el título y pasar esa información al contenido. Se eliminan la diapositiva del equipo y la de decisiones de entrenamiento.
todos:
  - id: portada-reto
    content: Quitar el lema de la portada, agrandar los nombres y reescribir la diapositiva del caso
    status: pending
  - id: quitar-diapos
    content: Eliminar las diapositivas de equipo y de decisiones, y guardar el dato del 74 % en el análisis
    status: pending
  - id: titulos
    content: Cambiar títulos del resto, quitar subtítulos y pasar esa información al contenido
    status: pending
  - id: verificar
    content: Recorrer la presentación y comprobar que el texto cabe y se entiende
    status: pending
isProject: false
---

# Textos que se entiendan

Se mantiene la estructura visual (gráficas, fotos, animaciones y el esquema datos / modelo / robot). Cambia el texto: el título dice qué se está contando y la frase de debajo del título desaparece. Lo que esa frase aportaba pasa a un pie, una viñeta o el panel que ya está en la diapositiva. El índice (tecla G) usa los mismos títulos.

## Portada

En [presentacion/src/diapositivas/inicio.jsx](presentacion/src/diapositivas/inicio.jsx), quitar «Del vídeo al disparo: datos propios, un detector y un robot.» Dejar el título **Detección de RoboMasters**, la línea de la asignatura, el indicador REC y el reloj. Los cinco nombres pasan a un cuerpo mayor (de 16 px a unos 24 px), en el hueco de esa frase.

## El caso y cómo lo resolvimos

Misma diapositiva, misma foto a la izquierda y las tres tarjetas a la derecha. Título: **El caso: recorrer un circuito, ver a los rivales y dispararles.** Sin subtítulo.

Las tarjetas dejan de ser una etiqueta más un pie y pasan a contar, en primera persona del plural, qué hicimos:

- **Datos.** La asignatura dio validación y test. El entrenamiento lo grabamos nosotros: diez vídeos, 808 imágenes y 1420 robots anotados.
- **Modelo.** Entrenamos un detector y lo comparamos con otras seis arquitecturas, siete en total, con las mismas reglas. Faster R-CNN v2 llega a 0,952 de AP@0,5 en test.
- **Robot.** Ese detector va en el portátil conectado al RoboMaster. Cada imagen tarda unos 2,3 s, así que el robot se para a mirar antes de disparar.

Las cifras grandes se quedan.

## Dos diapositivas fuera

- **Equipo** («Cinco personas, criterios comunes…»): se quita de [presentacion/src/diapositivas/index.js](presentacion/src/diapositivas/index.js) y se borra el componente. Los nombres siguen en la portada.
- **Decisiones** («Del análisis a las decisiones del entrenamiento»): se quita. Casi todo ya está en el análisis, el aumento o el test. El único dato que no aparece en otro sitio —el 74 % de las imágenes más parecidas son del mismo vídeo, y por eso se valida con secuencias de otros grupos— se añade como una frase en la diapositiva del análisis.

## Resto de diapositivas

En [fase1.jsx](presentacion/src/diapositivas/fase1.jsx), [fase2.jsx](presentacion/src/diapositivas/fase2.jsx), [fase3.jsx](presentacion/src/diapositivas/fase3.jsx) y [cierre.jsx](presentacion/src/diapositivas/cierre.jsx) se quita el `subtitulo` de `Cabecera` y el título pasa a decir el tema. Los separadores de fase (Datos, Modelo, Robot) se quedan; su lema ya es una frase y solo se afina el tono.

Títulos nuevos:

- **Las imágenes con las que entrenamos** (el embudo 10 vídeos → 643,8 s → 19 508 fotogramas → 808 imágenes, y por qué una de cada 24).
- **Qué consideramos un robot** (criterios y la calibración de las 20 imágenes).
- **Nuestros vídeos y los de la asignatura no se parecen.**
- **Más imágenes sin grabar escenas nuevas.**
- **Cómo entrenamos cada detector y cómo lo medimos** (la leyenda de colores ya explica lote, época y test).
- **Dos formas de buscar el robot en la imagen.**
- **Cómo elegimos el lote y la tasa de aprendizaje.**
- **Qué mejoró al primer modelo, y cuándo dejó de mejorar.**
- **Los siete detectores, en precisión y en tiempo.**
- **El resultado en imágenes que el modelo no había visto** (el 0,952 sigue como cifra, no como título).
- **Dónde acierta el detector y dónde se equivoca.**
- **Cómo conectamos el detector al robot.**
- **El recorrido que tiene que hacer el robot** (la leyenda azul / naranja pasa al mapa).
- **Por qué veía al rival y no disparaba.**
- **Disparar sin detener el robot** (los 12,5 s siguen en la barra).
- **Un disfraz no basta: el aliado se marca en verde.**
- **Mover el robot a mano desde el navegador.**
- **Qué ya funciona y qué falta probar en el laboratorio.**
- **Qué nos llevamos de cada fase.** Se quita el aviso de «borrador» del subtítulo; queda en las notas del presentador.

No se tocan cifras, gráficas ni animaciones. Las notas de quien presenta se actualizan para que no citen las dos diapositivas eliminadas.

## Comprobación

Arrancar la presentación y recorrer las diapositivas afectadas: que el texto quepa en 1600×900, que el índice coincida y que portada, caso, datos, anotación y análisis se lean como una explicación seguida.