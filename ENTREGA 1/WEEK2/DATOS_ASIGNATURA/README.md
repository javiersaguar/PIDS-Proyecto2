# Datos de la asignatura: validación y test

Imágenes de otros grupos y años (`PIDS2023` a `PIDS2025`) que da la asignatura para
validar y medir el detector. Se entrena solo con nuestros vídeos; estas imágenes no se
aumentan.

| Conjunto | Secuencias | Imágenes | Robots | `difficult` |
|---|---:|---:|---:|---:|
| `data_val` | 11 | 672 | 1561 | 255 (16 %) |
| `data_test` | 13 | 718 | 1721 | 270 (16 %) |

## Qué se ha cambiado respecto a lo que dio la asignatura

- **Solo están las imágenes con `.xml`.** Las 401 que venían sin etiquetar se dejaron
  fuera: no se sabe si no tienen robots o si quedaron sin anotar.
- **Se quitó el campo `<path>`** de los `.xml`, que guardaba rutas de los ordenadores de
  sus autores.
- **Se marcaron los `difficult`** (14/10/2026). Venían todos a 0. **Las cajas no se han
  tocado**: solo cambia el campo `difficult`.

## Cómo se marcaron los `difficult`

Con los criterios de nuestras propias etiquetas (regla R6 de
[`docs/criterios_anotacion.md`](../../../docs/criterios_anotacion.md)), para poder
evaluar el modelo por separado con los robots difíciles:

1. **Automático:** los robots de **menos de 30 px de ancho** (48).
2. **Revisión a ojo** de los 930 robots con algún indicio, cada uno recortado y
   ampliado:
   - **cortados por el borde** de la imagen;
   - **tapados** por otro robot más cercano (al menos un 30 % de la caja);
   - **poco nítidos** (varianza del Laplaciano del recorte por debajo del 35 % de la
     mediana de su secuencia).

   Se marcaron 477: robots **muy movidos**, de los que se ve **menos de la mitad**
   (tapados o cortados) o **muy oscuros**. No se marcaron los robots grandes, completos
   y nítidos aunque toquen el borde, ni los ligeramente movidos.

En total son 525 `difficult`. El resto de robots no tenía ningún indicio y se dejó
como estaba.

Como las cajas son de otros grupos, pueden no seguir nuestros criterios en las antenas
o en los robots muy cortados. Parte del error que se mida puede venir de ahí y no del
modelo.
