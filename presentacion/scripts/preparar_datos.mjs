// Prepara los datos de la presentación a partir de los ficheros del repositorio.
//
//   node scripts/preparar_datos.mjs        (o npm run datos)
//
// Escribe:
// - src/datos/generados.json: robots por vídeo (de los XML), curvas precisión-exhaustividad en test,
//   pérdidas y AP por época de Faster R-CNN v1 y AP por época de las siete arquitecturas;
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
for (const lote of lotes) {
  for (const carpeta of fs.readdirSync(path.join(ANOTACION, lote)).filter((d) => d.startsWith('ROBOMASTER_VIDEO_'))) {
    const v = 'V' + carpeta.slice(-2);
    const etiquetas = path.join(ANOTACION, lote, carpeta, 'labels');
    const fila = (porVideo[v] = { video: v, imagenes: 0, robots: 0, difficult: 0 });
    for (const f of fs.readdirSync(etiquetas).filter((n) => n.endsWith('.xml'))) {
      const { cajas } = leerXml(path.join(etiquetas, f));
      fila.imagenes += 1;
      fila.robots += cajas.length;
      fila.difficult += cajas.filter((c) => c.difficult).length;
    }
  }
}
const videos = Object.values(porVideo).sort((a, b) => a.video.localeCompare(b.video));
const total = videos.reduce((t, v) => ({ imagenes: t.imagenes + v.imagenes, robots: t.robots + v.robots,
  difficult: t.difficult + v.difficult }), { imagenes: 0, robots: 0, difficult: 0 });
if (total.imagenes !== 808 || total.robots !== 1420 || total.difficult !== 375) {
  throw new Error(`Los recuentos no cuadran con la memoria: ${JSON.stringify(total)}`);
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
fs.writeFileSync(path.join(salida, 'generados.json'), JSON.stringify({ videos, total, curvaPr, sobreajuste, arquitecturas },
  null, 1) + '\n');
fs.writeFileSync(path.join(salida, 'fotogramas.js'),
  '// Generado por scripts/preparar_datos.mjs: no editar a mano.\n' + importaciones.join('\n') +
  '\n\nexport const FOTOGRAMAS = {\n' + fotogramas.join('\n') + '\n};\n');
console.log('Vídeos:', videos.map((v) => `${v.video} ${v.robots}/${v.difficult}`).join(' · '));
console.log('Escritos generados.json y fotogramas.js en', salida);
