---
name: Gráficas interactivas PIDS
description: Tres figuras en un recorrido claro y continuo.
colors:
  background: "#ffffff"
  text: "#233342"
  muted: "#526576"
  accent: "#245e9b"
  accent-hover: "#194b80"
  line: "#dce3e9"
  control-border: "#a9b8c5"
  control-hover: "#e5edf5"
  grid: "#e6edf2"
  soft: "#f3f6f9"
  error: "#9b2929"
typography:
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "15px"
    lineHeight: 1.7
  title:
    fontSize: "clamp(32px, 3.2vw, 42px)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-.03em"
  section:
    fontSize: "25px"
  section-mobile:
    fontSize: "23px"
  chart-title:
    fontSize: "24px"
  chart-title-mobile:
    fontSize: "21px"
  intro:
    fontSize: "16px"
  compact:
    fontSize: "14px"
  help:
    fontSize: "13px"
  caption:
    fontSize: "12px"
  axis:
    fontSize: "11px"
rounded:
  toolbar: "8px"
  control: "6px"
---

# Diseño de las gráficas

## Overview
Página clara y de lectura continua. Las tres figuras aparecen en el orden distribución, evolución y recuentos. Se eliminan los menús de navegación y las pestañas por petición explícita; los únicos selectores pertenecen a los datos de las figuras.

## Colors
Fondo blanco continuo y texto oscuro. Azul para la reproducción, los enlaces y el foco. Superficie suave para agrupar los controles. Las paletas cálidas, las frecuencias y los ceros blancos de los mapas conservan su significado original.

## Typography
Familia de sistema. El título principal, los títulos de sección, las descripciones y las ayudas tienen jerarquías diferenciadas. Las descripciones ocupan hasta 70 caracteres de ancho. Los recuentos y la posición de reproducción usan cifras tabulares.

## Layout
Contenido centrado de hasta 1160 px. En escritorio, cada título se alinea a la izquierda de su descripción; la figura ocupa el ancho completo debajo. El encabezado sigue la misma alineación. Separación generosa entre figuras, con contexto y controles agrupados junto a su gráfico.

A 800 px se apilan título y descripción. A 560 px los controles se distribuyen en dos filas, los mapas se apilan y los recuentos pasan a una columna de diez paneles. Los ejes normalizados conservan sus límites y proporción 16:9. Cada marco comunica su altura para evitar recortes y desplazamiento horizontal.

## Elevation & Depth
Superficies planas, sin sombras ni tarjetas. Divisores finos separan las figuras; el fondo suave agrupa únicamente los controles. No hay animaciones decorativas; el movimiento corresponde al recorrido real de las muestras.

## Components
- Reproducción: botón azul que alterna Reproducir y Pausar; muestra su estado mediante texto y aria-pressed.
- Avance: botones de muestra anterior y siguiente, deshabilitados en los extremos.
- Recorrido: rango nativo accesible por teclado, con posición y descripción de la muestra.
- Vídeo: selector nativo que salta a la secuencia correspondiente.
- Contexto: conserva los recuentos y el intervalo procedentes del título original; evita repetir el título de sección dentro del marco.
- Exportaciones: enlaces discretos bajo cada figura; las hojas temporales se identifican como V01.
- Carga y error: texto de estado con reintento y acceso directo cuando no carga un marco.

## Do's and Don'ts
- Mantener las tres figuras visibles en el recorrido vertical.
- Conservar la escala científica, las muestras y la unidad junto a los datos.
- Conservar foco visible y controles nativos, también sin servidor.
- No añadir navegación, portada, miniaturas ni métricas que aparten de la lectura de las figuras.
