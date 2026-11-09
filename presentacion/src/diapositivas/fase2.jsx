import { motion, useReducedMotion } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Revela } from '../componentes/base.jsx';
import { Caja, Fotograma } from '../componentes/fotograma.jsx';
import { BarrasH, Ejes, escala, Lineas } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { AJUSTE_V1, ARQUITECTURAS, LOTES, TASAS, TEST_FINAL } from '../datos/cifras.js';
import generados from '../datos/generados.json';
import curvaPrPng from '@repo/docs/informes/figuras/curva_pr.png';
import precisionLatenciaPng from '@repo/docs/informes/figuras/precision_latencia.png';
import tasaPng from '@repo/docs/informes/figuras/tasa_aprendizaje.png';
import erroresPng from '@repo/docs/informes/figuras/errores_test.png';
import casosPng from '@repo/docs/informes/figuras/casos_validacion.png';
import incompletaPng from '@repo/docs/informes/figuras/etiqueta_incompleta.png';

const coma = (v, d = 2) => fmt(v, d);

// --- Separador ---------------------------------------------------------------------------------
export function Seccion2() {
  return (
    <Seccion numero="02" titulo="Modelo" fotos={[curvaPrPng, precisionLatenciaPng, tasaPng, erroresPng, casosPng]}
      lema="Montar el entrenamiento, ajustar lo que más importa y comparar siete detectores con las mismas reglas."
      puntos={['PyTorch y torchvision', '7 arquitecturas', '3 tasas', 'umbral en validación', 'test una sola vez']} />
  );
}

// --- Sistema de entrenamiento (C2.1) -------------------------------------------------------------------
const COLOR = { lote: 'var(--azul)', epoca: 'var(--acento)', una: 'var(--naranja)' };
const NODOS = {
  datos: { x: 0, y: 40, t: ['Datos de', 'entrenamiento'], g: 'lote' },
  carga: { x: 390, y: 40, t: ['Carga en lotes'], g: 'lote' },
  detector: { x: 780, y: 40, t: ['Detector'], g: 'lote' },
  perdida: { x: 1170, y: 40, t: ['Función de pérdida'], g: 'lote' },
  seleccion: { x: 390, y: 250, t: ['Selección', 'del modelo'], g: 'epoca' },
  evalval: { x: 780, y: 250, t: ['Evaluación en', 'validación'], g: 'epoca' },
  sgd: { x: 1170, y: 250, t: ['Optimizador SGD'], g: 'lote' },
  evaltest: { x: 0, y: 440, t: ['Evaluación', 'en test'], g: 'una' },
  datostest: { x: 390, y: 440, t: ['Datos de test'], g: 'una' },
  datosval: { x: 780, y: 440, t: ['Datos de', 'validación'], g: 'epoca' },
};
const ORDEN = ['datos', 'carga', 'detector', 'perdida', 'sgd', 'evalval', 'datosval', 'seleccion', 'datostest', 'evaltest'];
const ANCHO_NODO = 220;
const FLECHAS = [
  { d: 'M220,78 L386,78', g: 'lote', t: 'imágenes y cajas', tx: 303, ty: 62 },
  { d: 'M610,78 L776,78', g: 'lote', t: 'lotes de 8', tx: 693, ty: 62 },
  { d: 'M1000,78 L1166,78', g: 'lote', t: 'cajas y confianzas', tx: 1083, ty: 62 },
  { d: 'M1280,116 L1280,246', g: 'lote', t: 'gradientes', tx: 1292, ty: 186, a: 'start' },
  { d: 'M1186,250 L996,119', g: 'lote', t: 'pesos nuevos', tx: 1104, ty: 168, a: 'start' },
  { d: 'M860,116 L860,246', g: 'epoca', t: 'pesos de cada época', tx: 848, ty: 186, a: 'end' },
  { d: 'M920,440 L920,330', g: 'epoca', t: 'secuencias no vistas', tx: 932, ty: 392, a: 'start' },
  { d: 'M780,288 L614,288', g: 'epoca', t: 'AP@0,5 por época', tx: 697, ty: 272 },
  { d: 'M1000,300 L1166,300', g: 'epoca', t: 'pérdida de validación', tx: 1083, ty: 346 },
  { d: 'M440,326 L200,437', g: 'una', t: 'mejor modelo y umbral', tx: 330, ty: 368, a: 'end' },
  { d: 'M390,478 L224,478', g: 'una', t: 'otros grupos', tx: 307, ty: 462 },
];
const DUR = { lote: 1.3, epoca: 3.2, una: 5 };
export function Sistema() {
  const reducido = useReducedMotion();
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · El sistema" titulo="Cómo se entrena y se evalúa cada detector"
        subtitulo="Cada bloque es un módulo; cada flecha, los datos que pasa al siguiente. Unos se repiten en cada lote, otros en cada época y el test, una sola vez." />
      <div style={{ display: 'flex', gap: 26, marginBottom: 6 }} className="mono">
        {[['lote', 'Cada lote: entrenamiento'], ['epoca', 'Cada época: validación'], ['una', 'Una vez: test']].map(([g, t], i) => (
          <motion.span key={g} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 + i * 0.1 }}
            style={{ fontSize: 16, color: 'var(--suave)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <i style={{ width: 14, height: 14, border: `2px solid ${COLOR[g]}`, display: 'inline-block' }} />{t}
          </motion.span>
        ))}
      </div>
      <svg viewBox="-4 0 1400 530" style={{ width: '100%', flex: 1, minHeight: 0 }} role="img" aria-label="Esquema de bloques del entrenamiento">
        <defs>
          {Object.entries(COLOR).map(([g, c]) => (
            <marker key={g} id={`punta-${g}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={c} />
            </marker>
          ))}
        </defs>
        {FLECHAS.map((f, i) => (
          <g key={i}>
            <motion.path d={f.d} stroke={COLOR[f.g]} strokeWidth="2" fill="none" markerEnd={`url(#punta-${f.g})`}
              initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} transition={{ delay: 1.3 + i * 0.12, duration: 0.5 }} />
            <motion.text x={f.tx} y={f.ty} textAnchor={f.a || 'middle'} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              transition={{ delay: 1.6 + i * 0.12 }} style={{ font: 'italic 15px var(--mono)', fill: 'var(--suave)' }}>{f.t}</motion.text>
            {!reducido && (
              <circle r="5" fill={COLOR[f.g]} opacity="0.95" style={{ filter: `drop-shadow(0 0 6px ${COLOR[f.g]})` }}>
                <animateMotion dur={`${DUR[f.g]}s`} repeatCount="indefinite" path={f.d} begin={`${2.8 + (i % 4) * 0.25}s`} />
                <animate attributeName="opacity" values="0;0.95" dur="0.01s" begin={`${2.8 + (i % 4) * 0.25}s`} fill="freeze" />
              </circle>
            )}
          </g>
        ))}
        {ORDEN.map((k, i) => {
          const n = NODOS[k];
          return (
            <motion.g key={k} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.1, duration: 0.5, ease: CURVA }}>
              <rect x={n.x} y={n.y} width={ANCHO_NODO} height="76" rx="4" fill="var(--panel)" stroke={COLOR[n.g]} strokeWidth="2" />
              {n.t.map((l, j) => (
                <text key={l} x={n.x + ANCHO_NODO / 2} y={n.y + 38 + (j - (n.t.length - 1) / 2) * 24 + 7} textAnchor="middle"
                  style={{ font: '600 20px Geist, sans-serif', fill: 'var(--texto)' }}>{l}</text>
              ))}
            </motion.g>
          );
        })}
      </svg>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.6 }} style={{ margin: 0, fontSize: 19, color: 'var(--suave)' }}>
        Un lote son 8 imágenes y un paso; una época, una pasada por las 3184 imágenes, unos 400 pasos. El test no decide nada: solo mide.
      </motion.p>
    </div>
  );
}

// --- Una o dos etapas (C2.3) ----------------------------------------------------------------------------
function aleatorio(semilla) {
  let s = semilla;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}
function Propuestas({ cajas }) {
  const r = aleatorio(7);
  const props = Array.from({ length: 28 }, (_, i) => {
    const base = cajas[i % cajas.length];
    const cerca = i % 3 !== 2;
    const w = cerca ? base.w * (0.7 + r() * 0.7) : 0.06 + r() * 0.18;
    const h = cerca ? base.h * (0.7 + r() * 0.7) : 0.08 + r() * 0.2;
    const x = cerca ? base.x + base.w / 2 - w / 2 + (r() - 0.5) * base.w * 0.6 : r() * (1 - w);
    const y = cerca ? base.y + base.h / 2 - h / 2 + (r() - 0.5) * base.h * 0.6 : 0.15 + r() * (0.7 - h);
    return { x, y, w, h };
  });
  return props.map((p, i) => (
    <motion.div key={i} style={{ position: 'absolute', left: `${p.x * 100}%`, top: `${p.y * 100}%`, width: `${p.w * 100}%`, height: `${p.h * 100}%`,
      border: '1.5px dashed rgba(236,238,230,0.75)' }}
      initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0.9, 0] }}
      transition={{ delay: 0.8 + i * 0.035, duration: 2.4, times: [0, 0.1, 0.7, 1] }} />
  ));
}
function Anclas() {
  const cols = 24;
  const filas = 13;
  return Array.from({ length: cols * filas }, (_, k) => {
    const c = k % cols;
    const f = Math.floor(k / cols);
    return (
      <motion.span key={k} style={{ position: 'absolute', left: `${((c + 0.5) / cols) * 100}%`, top: `${((f + 0.5) / filas) * 100}%`,
        width: 4, height: 4, marginLeft: -2, marginTop: -2, borderRadius: '50%', background: 'var(--azul)' }}
        initial={{ opacity: 0, scale: 0 }} animate={{ opacity: [0, 1, 1, 0.25], scale: [0, 1.4, 1, 1] }}
        transition={{ delay: 0.8 + (c + f) * 0.025, duration: 1.6, times: [0, 0.2, 0.5, 1] }} />
    );
  });
}
export function Etapas() {
  const f = FOTOGRAMAS.objetivo;
  const pasos = [
    ['Dos etapas', 'Faster R-CNN', 'Una red de propuestas (RPN) sugiere unas mil regiones; después se recorta cada una, se clasifica y se ajusta su caja.'],
    ['Una etapa', 'RetinaNet · SSD', 'En cada posición de los mapas hay anclas de varios tamaños: se predicen la clase y el ajuste de todas a la vez.'],
  ];
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Arquitecturas" titulo="Detectores de una y de dos etapas"
        subtitulo="Todos parten de pesos preentrenados en COCO y casi todos añaden una FPN, que combina mapas de detalle y de contexto. Cambia cómo se buscan los robots." />
      <div className="cuerpo dos">
        {pasos.map(([t, m, d], i) => (
          <div key={t} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Fotograma foto={f} modo="nada">
              {i === 0 ? <Propuestas cajas={f.cajas} /> : <Anclas />}
              {f.cajas.map((c, k) => <Caja key={k} caja={c} retraso={i === 0 ? 3.0 + k * 0.15 : 2.4} rotulo="ROBOT" confianza={0.99 - k * 0.03} />)}
              <motion.div className="mono" style={{ position: 'absolute', right: 12, bottom: 10, fontSize: 14, background: 'rgba(12,13,11,0.75)', padding: '4px 8px' }}
                initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ delay: 0.8, duration: 2.2, times: [0, 0.1, 0.8, 1] }}>
                {i === 0 ? 'etapa 1 · propuestas' : 'anclas en toda la imagen'}
              </motion.div>
            </Fotograma>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 + i * 0.15 }}>
              <h3 style={{ margin: 0, fontSize: 28 }}>{t} <span className="mono suave" style={{ fontSize: 17, fontWeight: 400, marginLeft: 8 }}>{m}</span></h3>
              <p style={{ margin: '8px 0 0', color: 'var(--suave)', fontSize: 20 }}>{d}</p>
            </motion.div>
          </div>
        ))}
      </div>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.4 }} style={{ margin: '10px 0 0', fontSize: 20 }}>
        <span className="acento">En nuestras medidas</span>, con el mismo backbone, la diferencia de tiempo es pequeña: pesan más el backbone y el tamaño de la imagen.
      </motion.p>
    </div>
  );
}

// --- Hiperparámetros (C2.4–C2.6) -------------------------------------------------------------------------
export function Hiperparametros() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Hiperparámetros" titulo="Pruebas cortas antes de la cadena de entrenamientos"
        subtitulo="Tres épocas de Faster R-CNN v1 para fijar el lote y la tasa; el resto, con valores contrastados para ajuste fino de detectores." />
      <div className="cuerpo tres">
        <motion.div className="panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.6, ease: CURVA }}>
          <div className="etiqueta">Tamaño del lote</div>
          <h3 style={{ marginTop: 10 }}>8 imágenes</h3>
          <BarrasH anchoEtiqueta={44} retraso={0.7} paso={0.12} alto={34} textoNulo="sin memoria"
            datos={LOTES.map((l) => ({ etiqueta: l.lote, valor: l.ap, destacado: l.lote === '8' }))} />
          <p style={{ marginTop: 16, fontSize: 18 }}>AP@0,5 a las 3 épocas: los tres a menos de 0,4 pp. 8 es el mayor que cabe en 12 GB y da gradientes estables, con unos 400 pasos por época.</p>
        </motion.div>
        <motion.div className="panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45, duration: 0.6, ease: CURVA }}>
          <div className="etiqueta">Tasa de aprendizaje</div>
          <h3 style={{ marginTop: 10 }}>10<sup>−3</sup></h3>
          <BarrasH anchoEtiqueta={44} retraso={1.0} paso={0.14} alto={34} textoNulo="diverge: NaN"
            datos={TASAS.map((t) => ({ etiqueta: t.tasa, valor: t.ap, destacado: t.tasa === '10⁻³' }))} />
          <p style={{ marginTop: 16, fontSize: 18 }}>Muy baja, apenas avanza (0,03 de AP en 3 épocas); muy alta, la pérdida explota. Entre 10<sup>−4</sup> y 10<sup>−2</sup> cambia la velocidad, no el resultado.</p>
        </motion.div>
        <motion.div className="panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.6, ease: CURVA }}>
          <div className="etiqueta">Optimizador y programador</div>
          <h3 style={{ marginTop: 10 }}>SGD</h3>
          <Revela as="ul" className="lista" retraso={1.3} paso={0.15} style={{ fontSize: 19 }}>
            <Item as="li"><span><b>Momentum 0,9:</b> sigue la media de unos 10 lotes y suaviza el ruido.</span></Item>
            <Item as="li"><span><b>Weight decay 5·10<sup>−4</sup>:</b> penaliza los pesos grandes.</span></Item>
            <Item as="li"><span><b>Tasa ×0,1</b> tras 5 épocas sin mejorar la validación.</span></Item>
            <Item as="li"><span>Valores del artículo de Faster R-CNN y del tutorial de torchvision.</span></Item>
          </Revela>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.2 }} style={{ marginTop: 16, fontSize: 17, color: 'var(--tenue)' }}>
            Mejor estrategia: prueba de rango de la tasa, búsqueda logarítmica y paciencia ajustada a la época en que se estanca.
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}

// --- Primeros experimentos y sobreajuste ----------------------------------------------------------------------
function PuntosAjuste() {
  const ancho = 680;
  const alto = 330;
  const m = { l: 30, r: 40, t: 20, b: 50 };
  const sx = escala([0.915, 0.95], [m.l, ancho - m.r]);
  const fila = (i) => m.t + 26 + i * 68;
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} style={{ height: 'auto' }} role="img" aria-label="AP@0,5 en validación de los cuatro primeros experimentos">
      {[0.92, 0.93, 0.94, 0.95].map((t) => (
        <g key={t} className="rejilla">
          <line x1={sx(t)} x2={sx(t)} y1={m.t} y2={alto - m.b} />
          <text x={sx(t)} y={alto - m.b + 26} textAnchor="middle">{coma(t)}</text>
        </g>
      ))}
      {AJUSTE_V1.map((e, i) => (
        <g key={e.nombre}>
          <motion.text x={m.l} y={fila(i) - 16} style={{ fill: 'var(--texto)', fontFamily: 'Geist, sans-serif', fontSize: 18 }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 + i * 0.3 }}>{e.nombre}</motion.text>
          <motion.circle cy={fila(i) + 4} r="9" fill={i === 2 ? 'var(--acento)' : 'var(--texto)'}
            initial={{ cx: sx(0.915), opacity: 0 }} animate={{ cx: sx(e.ap), opacity: 1 }}
            transition={{ delay: 0.6 + i * 0.3, duration: 0.9, ease: CURVA }} />
          <motion.text y={fila(i) + 10} x={sx(e.ap) + 18} className="valor" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: 1.4 + i * 0.3 }}>{coma(e.ap, 4)} · época {e.epoca}</motion.text>
        </g>
      ))}
      <text x={(m.l + ancho - m.r) / 2} y={alto - 4} textAnchor="middle" style={{ fill: 'var(--tenue)' }}>AP@0,5 en validación · Faster R-CNN v1</text>
    </svg>
  );
}
export function Ajuste() {
  const s = generados.sobreajuste;
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Primeros experimentos" titulo="El aumento ayuda; las épocas de más, no"
        subtitulo="Con un único modelo se fijaron aumento, tasa y resolución. La validación deja de mejorar muy pronto mientras el entrenamiento sigue bajando." />
      <div className="cuerpo dos">
        <div className="panel" style={{ padding: '20px 24px' }}>
          <PuntosAjuste />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.6 }} style={{ fontSize: 18 }}>
            Aumento: +1,9 pp. A 1024 px sube 0,3 pp pero baja el AP estricto y tarda un 62 % más: se queda 800 px.
          </motion.p>
        </div>
        <div className="panel" style={{ padding: '20px 24px' }}>
          <div className="etiqueta" style={{ marginBottom: 4 }}>Pérdida por época · con aumento, tasa 10⁻³</div>
          <div style={{ height: 360 }}>
            <Lineas ancho={680} alto={360} dominioX={[1, 30]} dominioY={[0.05, 0.26]} ticksX={[1, 5, 10, 15, 20, 25, 30]}
              ticksY={[0.05, 0.1, 0.15, 0.2, 0.25]} fy={(v) => coma(v)} tituloX="época" m={{ l: 64, r: 120, t: 24, b: 56 }}
              series={[
                { nombre: 'validación', x: s.epoca, y: s.perdidaValidacion, color: 'var(--naranja)', retraso: 0.6, duracion: 2.2 },
                { nombre: 'entrenamiento', x: s.epoca, y: s.perdidaEntrenamiento, color: 'var(--azul)', retraso: 0.6, duracion: 2.2, discontinua: true },
              ]}
              extra={({ sx, sy, m, alto }) => (
                <g>
                  <motion.line x1={sx(5)} x2={sx(5)} y1={m.t} y2={alto - m.b} stroke="var(--acento)" strokeWidth="2"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.9 }} />
                  <motion.text x={sx(5) + 8} y={m.t + 14} style={{ fill: 'var(--acento)', fontSize: 15 }}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3 }}>mejor checkpoint (época 5)</motion.text>
                  <motion.circle cx={sx(4)} cy={sy(0.2212)} r="6" fill="none" stroke="var(--naranja)" strokeWidth="2"
                    initial={{ scale: 0 }} animate={{ scale: [0, 1.6, 1] }} transition={{ delay: 3.1, duration: 0.5 }} />
                </g>
              )} />
          </div>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.2 }} style={{ fontSize: 18 }}>
            Mínimo de validación en la época 4: hay sobreajuste, no faltan épocas. Por eso se guarda el mejor checkpoint de validación.
          </motion.p>
        </div>
      </div>
    </div>
  );
}

// --- Siete arquitecturas: precisión frente a tiempo ----------------------------------------------------------
export function Arquitecturas() {
  const ancho = 900;
  const alto = 560;
  const m = { l: 80, r: 40, t: 30, b: 70 };
  const sx = escala([3, 160], [m.l, ancho - m.r], true);
  const minY = 0.87;
  const syEscala = escala([minY, 0.96], [alto - m.b, m.t]);
  // SSDlite320 (0,682) queda fuera de la escala: se dibuja en el borde inferior con una flecha
  const sy = (v) => (v < minY ? alto - m.b - 4 : syEscala(v));
  const frontera = ['SSD300 VGG16', 'Faster R-CNN MobileNet', 'RetinaNet v2', 'Faster R-CNN v2']
    .map((n) => ARQUITECTURAS.find((a) => a.modelo === n));
  const orden = [...ARQUITECTURAS].sort((a, b) => a.ms - b.ms);
  const pos = { 'Faster R-CNN v2': [0, -22, 'middle'], 'RetinaNet v2': [-10, -12, 'end'], 'Faster R-CNN v1': [16, 6],
    'RetinaNet v1': [14, 24], 'Faster R-CNN MobileNet': [16, -10], 'SSD300 VGG16': [16, 6], SSDlite320: [16, -14] };
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Comparación" titulo="Siete detectores: precisión frente a tiempo"
        subtitulo="Mismo aumento, misma tasa (10⁻³), 12 épocas y el mejor checkpoint de validación. Tiempo por imagen en la GPU de entrenamiento (RTX 3060)." />
      <div className="cuerpo dos-asim" style={{ alignItems: 'center' }}>
        <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="AP@0,5 frente a milisegundos por imagen de siete detectores">
          <Ejes ancho={ancho} alto={alto} m={m} sx={sx} sy={syEscala} ticksX={[4, 10, 20, 50, 100]} ticksY={[0.88, 0.9, 0.92, 0.94, 0.96]}
            fx={(v) => `${v} ms`} fy={(v) => coma(v)} tituloX="milisegundos por imagen (escala logarítmica)" tituloY="AP@0,5 en validación" />
          <motion.path d={frontera.map((a, i) => `${i ? 'L' : 'M'}${sx(a.ms)},${sy(a.ap)}`).join('')} fill="none" stroke="var(--tenue)"
            strokeWidth="1.5" strokeDasharray="6 6" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 2.4, duration: 1.2 }} />
          {orden.map((a, i) => {
            const elegido = a.modelo === 'Faster R-CNN v2';
            const rapido = a.modelo === 'Faster R-CNN MobileNet';
            const color = elegido ? 'var(--acento)' : rapido ? 'var(--azul)' : '#8a9084';
            const [dx, dy, ancla] = pos[a.modelo];
            return (
              <g key={a.modelo}>
                <motion.circle cx={sx(a.ms)} cy={sy(a.ap)} r={elegido || rapido ? 11 : 8} fill={color} stroke="var(--fondo)" strokeWidth="2"
                  initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.5 + i * 0.22, type: 'spring', stiffness: 380, damping: 16 }} style={{ transformBox: 'fill-box', transformOrigin: 'center' }} />
                {elegido && (
                  // Pulso con SMIL: anima el radio sin transformaciones, así no se desplaza
                  <circle cx={sx(a.ms)} cy={sy(a.ap)} r="11" fill="none" stroke="var(--acento)" strokeWidth="2" opacity="0">
                    <animate attributeName="r" values="11;30;30" keyTimes="0;0.7;1" dur="2s" begin="2.2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.9;0;0" keyTimes="0;0.7;1" dur="2s" begin="2.2s" repeatCount="indefinite" />
                  </circle>
                )}
                <motion.text x={sx(a.ms) + dx} y={sy(a.ap) + dy} textAnchor={ancla || 'start'}
                  style={{ fill: elegido || rapido ? 'var(--texto)' : 'var(--suave)', fontWeight: elegido || rapido ? 600 : 400, fontSize: 16 }}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 + i * 0.22 }}>
                  {a.corto} · {coma(a.ap, 3)}{a.ap < minY ? ' ↓ fuera de escala' : ''}
                </motion.text>
              </g>
            );
          })}
        </svg>
        <Revela style={{ display: 'grid', gap: 18 }} retraso={2.4} paso={0.2}>
          <Item className="panel" style={{ borderColor: 'var(--acento-oscuro)' }}>
            <div className="etiqueta acento">Modelo final</div>
            <h3 style={{ marginTop: 8 }}>Faster R-CNN v2</h3>
            <p>El mejor AP@0,5 en validación (0,951) y en test (0,952). Unos 100 ms por imagen en GPU.</p>
          </Item>
          <Item className="panel">
            <div className="etiqueta" style={{ color: 'var(--azul)' }}>La alternativa rápida</div>
            <h3 style={{ marginTop: 8 }}>Faster R-CNN MobileNet</h3>
            <p>Seis veces más rápido por 2,3 pp menos. Candidato si el robot necesita más imágenes por segundo.</p>
          </Item>
          <Item as="p" style={{ margin: 0, fontSize: 18, color: 'var(--suave)' }}>
            La arquitectura pesa más que la tasa: con tres tasas, los tres mejores cambian menos de 0,3 pp.
          </Item>
        </Revela>
      </div>
    </div>
  );
}

// --- Resultado en test (C2.7) ------------------------------------------------------------------------------
export function Test() {
  const t = TEST_FINAL;
  const v2 = generados.curvaPr.faster_rcnn_v2;
  const v3 = generados.curvaPr.faster_rcnn_v3;
  const elegido = (c, u) => c.find((p) => Math.abs(p.umbral - u) < 1e-6);
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Evaluación final" titulo="En test, una sola vez: 0,952 de AP@0,5"
        subtitulo={`Faster R-CNN v2 sobre ${fmt(t.imagenes)} imágenes de otros grupos (${fmt(t.robots)} robots), con el umbral de confianza 0,95 fijado en validación.`} />
      <div className="cuerpo dos-asim-inv">
        <div style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[['AP@0,5', t.ap50, true], ['F1', t.f1], ['Precisión', t.precision], ['Exhaustividad', t.exhaustividad]].map(([n, v, a], i) => (
              <motion.div key={n} className="panel" style={{ padding: '14px 20px' }} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.12 }}>
                <div className="etiqueta">{n}</div>
                <div className={`cifra peque${a ? ' acento' : ''}`} style={{ marginTop: 6 }}><Contador valor={v} dec={3} retraso={0.4 + i * 0.12} /></div>
              </motion.div>
            ))}
          </div>
          <motion.div className="panel mono" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', textAlign: 'center', padding: '16px 10px' }}>
            {[['aciertos', t.tp, 'var(--acento)'], ['falsos positivos', t.fp, 'var(--rojo)'], ['robots perdidos', t.fn, 'var(--naranja)']].map(([n, v, c]) => (
              <div key={n}><div style={{ fontSize: 36, fontWeight: 600, color: c }}><Contador valor={v} retraso={1.1} /></div>
                <div style={{ fontSize: 14, color: 'var(--suave)' }}>{n}</div></div>
            ))}
          </motion.div>
          <motion.div className="panel" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }} style={{ padding: '18px 22px' }}>
            <div className="etiqueta" style={{ marginBottom: 10 }}>Dónde falla: AP@0,5 por tipo de robot</div>
            <BarrasH anchoEtiqueta={110} retraso={1.8} paso={0.2} alto={30}
              datos={[{ etiqueta: 'normales', valor: t.apNormales, destacado: true }, { etiqueta: 'difficult', valor: t.apDifficult, destacado: true, color: 'var(--naranja)' }]} />
            <p style={{ marginTop: 10, fontSize: 17 }}>{t.fnDifficult} de los {t.fn} robots perdidos son difficult: tapados, cortados, lejanos o movidos.</p>
          </motion.div>
        </div>
        <div className="panel" style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column' }}>
          <div className="etiqueta">Curva precisión-exhaustividad en test (IoU ≥ 0,5)</div>
          {/* La gráfica ocupa el alto que queda en el panel; así el texto de abajo no se sale */}
          <div style={{ flex: 1, minHeight: 0 }}>
          <Lineas ancho={760} alto={450} dominioX={[0.8, 0.98]} dominioY={[0.6, 0.98]} ticksX={[0.8, 0.85, 0.9, 0.95]}
            ticksY={[0.6, 0.7, 0.8, 0.9]} fx={(v) => coma(v)} fy={(v) => coma(v)} tituloX="exhaustividad" tituloY="precisión"
            m={{ l: 70, r: 30, t: 44, b: 64 }}
            series={[
              { nombre: 'Faster R-CNN v2', x: v2.map((p) => p.recall), y: v2.map((p) => p.precision), color: 'var(--acento)', ancho: 3,
                retraso: 0.8, duracion: 2, etiqueta: { texto: 'Faster R-CNN v2', dx: -14, dy: 5, ancla: 'end', en: 'inicio' } },
              { nombre: 'MobileNet', x: v3.map((p) => p.recall), y: v3.map((p) => p.precision), color: 'var(--azul)', discontinua: true,
                retraso: 1.2, duracion: 2, etiqueta: { texto: 'MobileNet', dx: -14, dy: 5, ancla: 'end', en: 'inicio' } },
            ]}
            extra={({ sx, sy }) => {
              const a = elegido(v2, 0.95);
              const b = elegido(v3, 0.55);
              return (
                <g>
                  {[[a, 'var(--acento)', 'umbral 0,95'], [b, 'var(--azul)', 'umbral 0,55']].map(([p, c, txt], i) => (
                    <g key={txt}>
                      <motion.circle cx={sx(p.recall)} cy={sy(p.precision)} r="9" fill="var(--fondo)" stroke={c} strokeWidth="3"
                        initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 3.2 + i * 0.2, type: 'spring' }}
                        style={{ transformBox: 'fill-box', transformOrigin: 'center' }} />
                      <motion.text x={sx(p.recall) + (i ? -14 : 14)} y={sy(p.precision) + (i ? 28 : -14)} textAnchor={i ? 'end' : 'start'}
                        style={{ fill: c, fontSize: 15 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.4 + i * 0.2 }}>{txt}</motion.text>
                    </g>
                  ))}
                </g>
              );
            }} />
          </div>
          <p style={{ margin: 0, fontSize: 17 }}>Cada punto es un umbral: al bajarlo se encuentran más robots, con más falsos positivos. El círculo es el umbral elegido en validación.</p>
        </div>
      </div>
    </div>
  );
}

// --- Análisis cualitativo ----------------------------------------------------------------------------------
export function Cualitativo() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 02 · Análisis cualitativo" titulo="Mirar las predicciones, no solo las métricas"
        subtitulo="Algunos falsos positivos eran robots sin etiquetar en validación; los fallos reales se concentran en difficult, robots lejanos y algunas secuencias." />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.35fr 1fr', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 18 }}>
          <motion.img src={casosPng} alt="Acierto completo y caso con más errores en validación" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.8, ease: CURVA }} style={{ width: '100%', borderRadius: 4, border: '1px solid var(--borde)', background: '#fff' }} />
          <motion.img src={incompletaPng} alt="Anotación incompleta y falsos positivos a 1024 píxeles" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7, duration: 0.8, ease: CURVA }} style={{ width: '56%', borderRadius: 4, border: '1px solid var(--borde)', background: '#fff' }} />
        </div>
        <Revela as="ul" className="lista" retraso={1.2} paso={0.25} style={{ fontSize: 21 }}>
          <Item as="li"><span><b>Acierto completo:</b> tres robots, uno difficult con confianza 0,51.</span></Item>
          <Item as="li"><span><b>Etiquetas incompletas:</b> cuatro robots y una sola caja en el XML; detectar los otros tres cuenta como error.</span></Item>
          <Item as="li"><span><b>Difficult:</b> 65 de los 83 robots perdidos por Faster R-CNN v1 en validación.</span></Item>
          <Item as="li"><span><b>Lejanos:</b> AP de objetos pequeños de 0,12 a 0,19; no había cajas de menos de 30 px.</span></Item>
          <Item as="li"><span><b>Errores reales:</b> una pierna y cajas solapadas sobre un mismo robot.</span></Item>
        </Revela>
      </div>
    </div>
  );
}
