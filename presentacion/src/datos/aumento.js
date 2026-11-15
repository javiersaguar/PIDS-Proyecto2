// Generado por herramientas/figuras_aumento.py: no editar a mano.
// Cada transformación aplicada sola, con sus cajas. usada: true (perfil del modelo final), false (no se usó).
import a_original from '@repo/docs/informes/figuras/aumento/00_original.jpg';
import a_volteo from '@repo/docs/informes/figuras/aumento/01_volteo.jpg';
import a_alejar from '@repo/docs/informes/figuras/aumento/02_alejar.jpg';
import a_acercar from '@repo/docs/informes/figuras/aumento/03_acercar.jpg';
import a_girar from '@repo/docs/informes/figuras/aumento/04_girar.jpg';
import a_brillo from '@repo/docs/informes/figuras/aumento/05_brillo.jpg';
import a_gamma from '@repo/docs/informes/figuras/aumento/06_gamma.jpg';
import a_tono from '@repo/docs/informes/figuras/aumento/07_tono.jpg';
import a_canales from '@repo/docs/informes/figuras/aumento/08_canales.jpg';
import a_movimiento from '@repo/docs/informes/figuras/aumento/09_movimiento.jpg';
import a_jpeg from '@repo/docs/informes/figuras/aumento/10_jpeg.jpg';
import a_ruido from '@repo/docs/informes/figuras/aumento/11_ruido.jpg';
import a_resolucion from '@repo/docs/informes/figuras/aumento/12_resolucion.jpg';
import a_sombra from '@repo/docs/informes/figuras/aumento/13_sombra.jpg';
import a_lluvia from '@repo/docs/informes/figuras/aumento/14_lluvia.jpg';
import a_postes from '@repo/docs/informes/figuras/aumento/15_postes.jpg';
import a_dif_oscuro from '@repo/docs/informes/figuras/aumento/16_dif_oscuro.jpg';
import a_dif_movido from '@repo/docs/informes/figuras/aumento/17_dif_movido.jpg';
import a_barras from '@repo/docs/informes/figuras/aumento/18_barras.jpg';
import a_volteo_v from '@repo/docs/informes/figuras/aumento/19_volteo_v.jpg';
import a_giro90 from '@repo/docs/informes/figuras/aumento/20_giro90.jpg';
import a_perspectiva from '@repo/docs/informes/figuras/aumento/21_perspectiva.jpg';
import a_recorte from '@repo/docs/informes/figuras/aumento/22_recorte.jpg';
import a_desenfoque from '@repo/docs/informes/figuras/aumento/23_desenfoque.jpg';
import a_intercambio from '@repo/docs/informes/figuras/aumento/24_intercambio.jpg';

export const AUMENTO_IMAGENES = [
  { clave: 'original', titulo: "Original", usada: null, src: a_original, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'volteo', titulo: "Volteo horizontal", usada: true, src: a_volteo, "fila": 0, cajas: [{"x": 0.4289, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.6008, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.6523, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'alejar', titulo: "Alejar ×0,6", usada: true, src: a_alejar, "fila": 1, cajas: [{"x": 0.507, "y": 0.4592, "w": 0.0356, "h": 0.065, "difficult": false}, {"x": 0.3922, "y": 0.4583, "w": 0.0473, "h": 0.0675, "difficult": false}, {"x": 0.2769, "y": 0.4408, "w": 0.1317, "h": 0.1783, "difficult": false}] },
  { clave: 'acercar', titulo: "Acercar ×1,25", usada: true, src: a_acercar, "fila": 1, cajas: [{"x": 0.5146, "y": 0.4149, "w": 0.0742, "h": 0.1354, "difficult": false}, {"x": 0.2754, "y": 0.4132, "w": 0.0986, "h": 0.1406, "difficult": false}, {"x": 0.0352, "y": 0.3767, "w": 0.2744, "h": 0.3715, "difficult": false}] },
  { clave: 'girar', titulo: "Desplazar y girar 6°", usada: true, src: a_girar, "fila": 2, cajas: [{"x": 0.5907, "y": 0.4743, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.4004, "y": 0.5065, "w": 0.0788, "h": 0.1128, "difficult": false}, {"x": 0.2128, "y": 0.4992, "w": 0.219, "h": 0.2984, "difficult": false}] },
  { clave: 'brillo', titulo: "Brillo y contraste", usada: true, src: a_brillo, "fila": 3, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'gamma', titulo: "Gamma, más oscuro", usada: true, src: a_gamma, "fila": 3, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'tono', titulo: "Tono y saturación", usada: true, src: a_tono, "fila": 4, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'canales', titulo: "Desplazamiento RGB", usada: true, src: a_canales, "fila": 4, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'movimiento', titulo: "Desenfoque de movimiento", usada: true, src: a_movimiento, "fila": 5, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'jpeg', titulo: "Compresión JPEG, calidad 35", usada: true, src: a_jpeg, "fila": 6, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'ruido', titulo: "Ruido de sensor", usada: true, src: a_ruido, "fila": 6, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'resolucion', titulo: "Menor resolución ×0,5", usada: true, src: a_resolucion, "fila": 6, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'sombra', titulo: "Sombra · V04, exterior", usada: true, src: a_sombra, "fila": 7, cajas: [{"x": 0.7039, "y": 0.3708, "w": 0.2055, "h": 0.2986, "difficult": false}, {"x": 0.3516, "y": 0.3931, "w": 0.0539, "h": 0.1069, "difficult": false}, {"x": 0.0008, "y": 0.4417, "w": 0.1172, "h": 0.3111, "difficult": true}] },
  { clave: 'lluvia', titulo: "Llovizna · V04, exterior", usada: true, src: a_lluvia, "fila": 7, cajas: [{"x": 0.7039, "y": 0.3708, "w": 0.2055, "h": 0.2986, "difficult": false}, {"x": 0.3516, "y": 0.3931, "w": 0.0539, "h": 0.1069, "difficult": false}, {"x": 0.0008, "y": 0.4417, "w": 0.1172, "h": 0.3111, "difficult": true}] },
  { clave: 'postes', titulo: "Postes con textura", usada: true, src: a_postes, "fila": 8, cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'dif_oscuro', titulo: "Difficult · más oscuro", usada: true, src: a_dif_oscuro, "fila": 9, cajas: [{"x": 0.3375, "y": 0.1667, "w": 0.1719, "h": 0.2708, "difficult": true}, {"x": 0.5195, "y": 0.1944, "w": 0.0547, "h": 0.1181, "difficult": true}, {"x": 0.4609, "y": 0.2083, "w": 0.0453, "h": 0.0833, "difficult": true}] },
  { clave: 'dif_movido', titulo: "Difficult · más movido", usada: true, src: a_dif_movido, "fila": 9, cajas: [{"x": 0.3375, "y": 0.1667, "w": 0.1719, "h": 0.2708, "difficult": true}, {"x": 0.5195, "y": 0.1944, "w": 0.0547, "h": 0.1181, "difficult": true}, {"x": 0.4609, "y": 0.2083, "w": 0.0453, "h": 0.0833, "difficult": true}] },
  { clave: 'barras', titulo: "Barras lisas", usada: false, src: a_barras, "motivo": "una barra lisa no parece una pata de silla: el modelo final usa postes con textura", cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'volteo_v', titulo: "Volteo vertical", usada: false, src: a_volteo_v, "motivo": "el robot nunca está boca abajo", cajas: [{"x": 0.5117, "y": 0.4597, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4569, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.3014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'giro90', titulo: "Giro de 90°", usada: false, src: a_giro90, "motivo": "el robot nunca aparece de lado", cajas: [{"x": 0.4617, "y": 0.3736, "w": 0.0609, "h": 0.1056, "difficult": false}, {"x": 0.4609, "y": 0.6792, "w": 0.0633, "h": 0.1403, "difficult": false}, {"x": 0.4445, "y": 0.7708, "w": 0.1672, "h": 0.2292, "difficult": false}] },
  { clave: 'perspectiva', titulo: "Perspectiva", usada: false, src: a_perspectiva, "motivo": "las cajas que devuelve no coinciden con el robot", cajas: [{"x": 0.2751, "y": 0.69, "w": 0.0384, "h": 0.2006, "difficult": false}, {"x": 0.1585, "y": 0.6877, "w": 0.0513, "h": 0.208, "difficult": false}, {"x": 0.0349, "y": 0.6345, "w": 0.1449, "h": 0.3655, "difficult": false}] },
  { clave: 'recorte', titulo: "Recorte 640×480", usada: false, src: a_recorte, "motivo": "ensancha los robots un 33 % y pierde el 14 % de las cajas", cajas: [{"x": 0.9516, "y": 0.3229, "w": 0.0484, "h": 0.1625, "difficult": false}, {"x": 0.5687, "y": 0.3208, "w": 0.1578, "h": 0.1687, "difficult": false}, {"x": 0.1844, "y": 0.2771, "w": 0.4391, "h": 0.4458, "difficult": false}] },
  { clave: 'desenfoque', titulo: "Desenfoque uniforme", usada: false, src: a_desenfoque, "motivo": "no se parece al desenfoque real, que es de movimiento", cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
  { clave: 'intercambio', titulo: "Intercambio de canales", usada: false, src: a_intercambio, "motivo": "da colores que la cámara nunca dará", cajas: [{"x": 0.5117, "y": 0.4319, "w": 0.0594, "h": 0.1083, "difficult": false}, {"x": 0.3203, "y": 0.4306, "w": 0.0789, "h": 0.1125, "difficult": false}, {"x": 0.1281, "y": 0.4014, "w": 0.2195, "h": 0.2972, "difficult": false}] },
];
