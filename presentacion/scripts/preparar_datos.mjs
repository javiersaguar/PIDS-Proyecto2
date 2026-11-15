// Prepara los datos de la presentación a partir de los ficheros del repositorio.
//
//   node scripts/preparar_datos.mjs        (o npm run datos)
//
// Escribe:
// - src/datos/generados.json: robots por vídeo (de los XML), curvas precisión-exhaustividad en test,
//   pérdidas y AP por época de Faster R-CNN v1, AP por época de las siete arquitecturas y el EDA de las cajas
//   (posición, tamaño, forma, solapamiento y nitidez), comprobado con las cifras de la memoria;
// - src/datos/fotogramas.js: los fotogramas elegidos (importados desde el repositorio) con sus cajas.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(aqui, '..', '..');
const salida = path.resolve(aqui, '..', 'src', 'datos');
const ANOTACION = path.join(repo, 'ENTREGA 1', 'WEEK1', 'ANOTACION');
const TEST = path.join(repo, 'ENTREGA 1', 'WEEK2', 'resultados_test');

// --- anotaciones VOC -------------------------------------------------------------------------
function leerXml(ruta) {
  const xml = fs.readFileSync(ruta, 'utf8');
  const num = (txt, etiqueta) => Number((txt.match(new RegExp(`<${etiqueta}>([^<]*)</${etiqueta}>`)) || [])[1]);
  const ancho = num(xml, 'width');
  const alto = num(xml, 'height');
  const cajas = [...xml.matchAll(/<object>([\s\S]*?)<\/object>/g)].map(([, o]) => ({
    x: num(o, 'xmin') / ancho,
    y: num(o, 'ymin') / alto,
    w: (num(o, 'xmax') - num(o, 'xmin')) / ancho,
    h: (num(o, 'ymax') - num(o, 'ymin')) / alto,
    difficult: num(o, 'difficult') === 1,
  }));
  return { ancho, alto, cajas };
}

const lotes = fs.readdirSync(ANOTACION).filter((d) => /^[A-E]_/.test(d));
const porVideo = {};
const imagenesEda = [];   // cajas en píxeles de cada imagen, para el EDA
for (const lote of lotes) {
  for (const carpeta of fs.readdirSync(path.join(ANOTACION, lote)).filter((d) => d.startsWith('ROBOMASTER_VIDEO_'))) {
    const v = 'V' + carpeta.slice(-2);
    const etiquetas = path.join(ANOTACION, lote, carpeta, 'labels');
    const fila = (porVideo[v] = { video: v, imagenes: 0, robots: 0, difficult: 0 });
    for (const f of fs.readdirSync(etiquetas).filter((n) => n.endsWith('.xml'))) {
      const { ancho, alto, cajas } = leerXml(path.join(etiquetas, f));
      fila.imagenes += 1;
      fila.robots += cajas.length;
      fila.difficult += cajas.filter((c) => c.difficult).length;
      imagenesEda.push({ ancho, alto, cajas: cajas.map((c) => ({ x0: c.x * ancho, y0: c.y * alto, x1: (c.x + c.w) * ancho,
        y1: (c.y + c.h) * alto, d: c.difficult })) });
    }
  }
}
const videos = Object.values(porVideo).sort((a, b) => a.video.localeCompare(b.video));
const total = videos.reduce((t, v) => ({ imagenes: t.imagenes + v.imagenes, robots: t.robots + v.robots,
  difficult: t.difficult + v.difficult }), { imagenes: 0, robots: 0, difficult: 0 });
if (total.imagenes !== 808 || total.robots !== 1420 || total.difficult !== 375) {
  throw new Error(`Los recuentos no cuadran con la memoria: ${JSON.stringify(total)}`);
}

// --- EDA: posición, tamaño, forma, solapamiento y nitidez (como en eda.ipynb, apartados 4.2 a 4.4) ---------
const redondea = (v, d = 3) => +v.toFixed(d);
function correlacion(a, b) {
  const ma = a.reduce((s, v) => s + v, 0) / a.length;
  const mb = b.reduce((s, v) => s + v, 0) / b.length;
  let sab = 0, saa = 0, sbb = 0;
  a.forEach((v, i) => { sab += (v - ma) * (b[i] - mb); saa += (v - ma) ** 2; sbb += (b[i] - mb) ** 2; });
  return sab / Math.sqrt(saa * sbb);
}
const percentil = (xs, p) => { const s = [...xs].sort((a, b) => a - b); const k = (s.length - 1) * p; const i = Math.floor(k);
  return s[i] + (s[Math.min(i + 1, s.length - 1)] - s[i]) * (k - i); };
const todasCajas = imagenesEda.flatMap((im) => im.cajas.map((c) => ({ ...c, w: c.x1 - c.x0, h: c.y1 - c.y0,
  borde: c.x0 <= 1 || c.y0 <= 1 || c.x1 >= im.ancho - 1 || c.y1 >= im.alto - 1, ancho: im.ancho, alto: im.alto })));
const libres = todasCajas.filter((c) => !c.borde);   // la perspectiva se mide sin las cajas cortadas por el borde
const tocan = todasCajas.filter((c) => c.borde);
const pctDif = (cs) => (100 * cs.filter((c) => c.d).length) / cs.length;
const iou = (a, b) => {
  const ix = Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0));
  const iy = Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));
  return (ix * iy) / ((a.x1 - a.x0) * (a.y1 - a.y0) + (b.x1 - b.x0) * (b.y1 - b.y0) - ix * iy);
};
const parejas = imagenesEda.flatMap((im) => im.cajas.flatMap((a, i) => im.cajas.slice(i + 1).map((b) => iou(a, b))));
// Nitidez relativa (varianza del laplaciano frente a la mediana de su vídeo), de resultados_eda/metricas_imagenes.csv
const [cabMetricas, ...filasMetricas] = fs.readFileSync(path.join(repo, 'ENTREGA 1', 'WEEK1', 'resultados_eda',
  'metricas_imagenes.csv'), 'utf8').trim().split(/\r?\n/);
const camposMetricas = cabMetricas.split(',');
const metricas = filasMetricas.map((l) => Object.fromEntries(l.split(',').map((v, i) => [camposMetricas[i], v])))
  .map((r) => ({ robots: +r.robots, difficult: +r.difficult, rel: +r.nitidez_rel, vecina: r.vecina_mismo_video === 'True' }))
  .filter((r) => r.robots > 0);
const cortes = [0.25, 0.5, 0.75].map((p) => percentil(metricas.map((r) => r.rel), p));
const cuartil = (r) => cortes.filter((c) => r.rel > c).length;
const nitidez = [0, 1, 2, 3].map((q) => { const rs = metricas.filter((r) => cuartil(r) === q);
  return { imagenes: rs.length, pctDifficult: redondea((100 * rs.reduce((s, r) => s + r.difficult, 0)) / rs.reduce((s, r) => s + r.robots, 0), 1) }; });
const centrosY = todasCajas.map((c) => (c.y0 + c.y1) / 2 / c.alto);
const eda = {
  centros: todasCajas.map((c) => [redondea((c.x0 + c.x1) / 2 / c.ancho), redondea((c.y0 + c.y1) / 2 / c.alto), c.d ? 1 : 0]),
  franja: [redondea(percentil(centrosY, 0.1), 2), redondea(percentil(centrosY, 0.9), 2)],
  centroXMedio: redondea(todasCajas.reduce((s, c) => s + (c.x0 + c.x1) / 2 / c.ancho, 0) / todasCajas.length, 2),
  perspectiva: libres.map((c) => [Math.round(c.y1), Math.round(c.h), c.d ? 1 : 0]),
  rPerspectiva: redondea(correlacion(libres.map((c) => c.y1), libres.map((c) => Math.log(c.h))), 2),
  forma: todasCajas.map((c) => [Math.round(c.w), Math.round(c.h), c.d ? 1 : 0]),
  rForma: redondea(correlacion(todasCajas.map((c) => Math.log(c.w)), todasCajas.map((c) => Math.log(c.h))), 2),
  aspectoMediano: redondea(percentil(todasCajas.map((c) => c.w / c.h), 0.5), 2),
  borde: { cajas: tocan.length, pctDifficult: Math.round(pctDif(tocan)), pctDifficultResto: Math.round(pctDif(todasCajas.filter((c) => !c.borde))) },
  solape: { parejas: parejas.length, seTocan: parejas.filter((v) => v > 0).length, max: redondea(Math.max(...parejas), 2),
    positivos: parejas.filter((v) => v > 0).map((v) => redondea(v)).sort((a, b) => a - b) },
  nitidez,
};
// Las mismas cifras que la memoria (apartados 4.2 a 4.4 y Anexo C)
const esperado = { rPerspectiva: 0.68, rForma: 0.94, aspectoMediano: 1.11, franja: '0.37,0.58', centroXMedio: 0.5,
  borde: '61,23', solape: '809,92,0.26', nitidez: '55,11' };
const obtenido = { rPerspectiva: eda.rPerspectiva, rForma: eda.rForma, aspectoMediano: eda.aspectoMediano, franja: eda.franja.join(','),
  centroXMedio: eda.centroXMedio, borde: `${eda.borde.pctDifficult},${eda.borde.pctDifficultResto}`,
  solape: `${eda.solape.parejas},${eda.solape.seTocan},${eda.solape.max}`,
  nitidez: `${Math.round(nitidez[0].pctDifficult)},${Math.round(nitidez[3].pctDifficult)}` };
for (const k of Object.keys(esperado)) {
  if (String(esperado[k]) !== String(obtenido[k])) throw new Error(`EDA: ${k} da ${obtenido[k]}, la memoria dice ${esperado[k]}`);
}

// --- fotogramas elegidos -----------------------------------------------------------------------
const ELEGIDOS = {
  portada: ['03', 1632], anotacion: ['04', 1416], objetivo: ['07', 360],
  v01: ['01', 1056], v02: ['02', 648], v03: ['03', 1632], v04: ['04', 1416], v05: ['05', 480],
  v06: ['06', 1176], v07: ['07', 360], v08: ['08', 1608], v09: ['09', 528], v10: ['10', 720],
};
const importaciones = [];
const fotogramas = [];
for (const [clave, [video, frame]] of Object.entries(ELEGIDOS)) {
  const lote = lotes.find((l) => fs.existsSync(path.join(ANOTACION, l, `ROBOMASTER_VIDEO_${video}`)));
  const nombre = `frame_${String(frame).padStart(4, '0')}`;
  const base = path.join(ANOTACION, lote, `ROBOMASTER_VIDEO_${video}`);
  const { cajas } = leerXml(path.join(base, 'labels', `${nombre}.xml`));
  const relativa = path.relative(repo, path.join(base, 'images', `${nombre}.jpg`)).split(path.sep).join('/');
  importaciones.push(`import ${clave} from '@repo/${relativa}';`);
  fotogramas.push(`  ${clave}: { src: ${clave}, video: 'V${video}', frame: ${frame}, cajas: ${JSON.stringify(cajas.map(
    (c) => ({ ...c, x: +c.x.toFixed(4), y: +c.y.toFixed(4), w: +c.w.toFixed(4), h: +c.h.toFixed(4) })))} },`);
}

// --- curvas precisión-exhaustividad en test -------------------------------------------------
function leerCsv(ruta) {
  const [cabecera, ...filas] = fs.readFileSync(ruta, 'utf8').trim().split(/\r?\n/);
  const campos = cabecera.split(',');
  return filas.map((l) => Object.fromEntries(l.split(',').map((v, i) => [campos[i], Number(v)])));
}
const curvaPr = Object.fromEntries(['faster_rcnn_v2', 'faster_rcnn_v3'].map((m) => [m,
  leerCsv(path.join(TEST, `${m}_aug_robusto_v1_lr001_test`, 'umbral_confianza.csv'))
    .map(({ umbral, precision, recall }) => ({ umbral, precision, recall }))]));

// --- curvas por época de la web del Bloque 2 ---------------------------------------------------
function leerWeb(fichero, variable) {
  const contexto = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(repo, 'web', 'Bloque2', fichero), 'utf8'), contexto);
  return contexto.window[variable];
}
const epocas = leerWeb('datos.js', 'PIDS_BLOQUE2').epocas.data;
// Grupo de cuatro trazas de «Con aumento · lr 0,001» (tercera opción del desplegable)
const grupo = epocas.slice(8, 12);
const sobreajuste = {
  experimento: 'Faster R-CNN v1 con aumento, tasa 10^-3',
  epoca: grupo[0].x,
  perdidaEntrenamiento: grupo[0].y,
  perdidaValidacion: grupo[1].y,
  ap50: grupo[2].y,
};
const arquitecturas = leerWeb('datos_cadena.js', 'PIDS_CADENA').arquitecturas.variantes['0'].data
  .filter((d) => d.x.length > 1)
  .map((d) => ({ modelo: d.name, epoca: d.x, ap50: d.y.map((v) => +v.toFixed(4)) }));

fs.mkdirSync(salida, { recursive: true });
fs.writeFileSync(path.join(salida, 'generados.json'), JSON.stringify({ videos, total, curvaPr, sobreajuste, arquitecturas, eda },
  null, 1).replace(/\[\s+([-\d.,\s]+?)\s+\]/g, (_, v) => `[${v.replace(/\s+/g, '')}]`) + '\n');
fs.writeFileSync(path.join(salida, 'fotogramas.js'),
  '// Generado por scripts/preparar_datos.mjs: no editar a mano.\n' + importaciones.join('\n') +
  '\n\nexport const FOTOGRAMAS = {\n' + fotogramas.join('\n') + '\n};\n');
console.log('Vídeos:', videos.map((v) => `${v.video} ${v.robots}/${v.difficult}`).join(' · '));
console.log('Escritos generados.json y fotogramas.js en', salida);
