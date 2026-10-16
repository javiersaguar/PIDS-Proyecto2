# Informes sobre la plantilla oficial

Contenido actualizado el **15/10/2026**, después de finalizar entrenamiento y
validación de `faster_rcnn_v1_aug_lr001`.

| Versión | Word editable | PDF | Contenido |
|---|---|---|---|
| Completa | [Word](informe_completo_fases_1_2.docx) | [PDF](informe_completo_fases_1_2.pdf) | Fases 1 y 2 con lo medido; conserva la estructura pendiente de fase 3 |
| Solo fase 1 | [Word](informe_fase1.docx) | [PDF](informe_fase1.pdf) | Datos, anotación, EDA, aumento y depuración; siete páginas de cuerpo |
| Solo fase 2 | [Word](informe_fase2.docx) | [PDF](informe_fase2.pdf) | Pipeline, modelo, hiperparámetros, métricas, experimentos y análisis cualitativo; ocho páginas de cuerpo |

La copia de fase 2 es una extracción de trabajo solicitada para revisar ese bloque.
La segunda entrega oficial es **incremental** y debe incluir también la fase 1
corregida. Los PDF contienen 11, 12 y 20 páginas totales respectivamente para fase 1,
fase 2 y completa: portada, reparto, índice y referencias no se cuentan como cuerpo.
Las fases 1 y 2 suman quince páginas de cuerpo en la completa.

Se conserva Calibri 11, interlineado 1,15, geometría, cabecera y pie de la plantilla.
Las figuras van incrustadas; no requieren archivos externos para abrir el Word.
El índice y la paginación se verifican en el PDF. En Word se pueden actualizar con
F9 si se cambia el contenido. La plantilla original permanece sin modificar.

También se proporcionan [versión Markdown completa](informe_completo_fases_1_2.md),
[fase 1](informe_fase1.md) y [fase 2](informe_fase2.md), para revisar diferencias en Git.

## Resultados incorporados

- `lr001`: mejor época 5, AP@0,5 de 0,9433 y AP 0,50:0,95 de 0,6302 en evaluación
  final de validación. AP@0,5 de difficult 0,6462; 190 FP y 83 FN a confianza 0,5.
- Curvas comparadas, cambios por secuencia, búsqueda del umbral y latencia.
- Anotación incompleta confirmada en `PIDS2024_GR02_0001/frame_0444.jpg`:
  cuatro robots visibles y una sola caja XML. No se alteran esas etiquetas.
- Perfiles nuevos de aumento distinguidos de los resultados del aumento base.

La fase 2 **no está cerrada**: falta comparar arquitecturas y evaluar el modelo
definitivo en test. No se presentan propuestas de resolución, lluvia u oclusión
texturada como resultados entrenados. Falta confirmar fecha de entrega, número
administrativo del grupo y reparto final con todos los integrantes.

## Regeneración

Con `python-docx`, `lxml`, Pillow y las figuras disponibles:

```bash
python herramientas/generar_informes.py
python herramientas/comparar_entrenamientos.py
```

El primer comando crea las tres copias Word y Markdown; no sobreescribe la
plantilla ni exporta por sí solo PDF. Para obtener los PDF, actualizar los campos
y exportar desde Word, comprobando otra vez todas las páginas. Las figuras
específicas de maquetación están en `figuras/`; las curvas y los resultados del
laboratorio conservan sus rutas en `ENTREGA 1/WEEK2/`.
