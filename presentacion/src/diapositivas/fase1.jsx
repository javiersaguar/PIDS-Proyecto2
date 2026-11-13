import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Revela } from '../componentes/base.jsx';
import { Caja, Fotograma } from '../componentes/fotograma.jsx';
import { BarrasH, Ejes, escala } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { AUMENTO_IMAGENES } from '../datos/aumento.js';
import { ANOTACION, CRITERIOS, DATASET, INTERVALOS, RECOGIDA } from '../datos/cifras.js';
import generados from '../datos/generados.json';

const F = FOTOGRAMAS;
export const VIDEOS = [F.v01, F.v02, F.v03, F.v04, F.v05, F.v06, F.v07, F.v08, F.v09, F.v10];

// --- Separador ---------------------------------------------------------------------------------
export function Seccion1() {
  return (
    <Seccion numero="01" titulo="Datos" fotos={VIDEOS}
      lema="Antes de entrenar, grabamos nuestros vídeos, decidimos qué es un robot y analizamos los datos."
      puntos={['10 vídeos', '808 imágenes', '1420 robots', 'análisis exploratorio', 'aumento ×4']} />
  );
}

// --- Recogida -----------------------------------------------------------------------------------
const EMBUDO = [
  { v: RECOGIDA.videos, t: 'vídeos grabados con el RoboMaster', d: '1280 × 720 · 30 fps · interior y exterior' },
  { v: RECOGIDA.segundos, dec: 1, t: 'segundos de grabación', d: 'vestíbulo, aulas, pasillo y exterior' },
  { v: RECOGIDA.fotogramas, t: 'fotogramas', d: 'de uno al siguiente (1/30 s) casi no cambia nada' },
  { v: RECOGIDA.imagenes, t: 'imágenes para anotar', d: 'una de cada 24 fotogramas (0,79 s)', acento: true },
];
export function Recogida() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Recolección" titulo="Las imágenes con las que entrenamos" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 10 }}>
          {EMBUDO.map((e, i) => (
            <motion.div key={e.t} initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.35 + i * 0.4, duration: 0.6, ease: CURVA }}
              style={{ display: 'grid', gridTemplateColumns: '250px 1fr', alignItems: 'center', gap: 22, padding: '14px 0',
                borderBottom: i < EMBUDO.length - 1 ? '1px dashed var(--borde)' : 'none',
                marginLeft: i * 26 }}>
              <span className={`cifra media${e.acento ? ' acento' : ''}`} style={{ textAlign: 'right' }}>
                <Contador valor={e.v} dec={e.dec || 0} retraso={0.35 + i * 0.4} duracion={1.2} />
              </span>
              <div>
                <div style={{ fontSize: 23, fontWeight: 600 }}>{e.t}</div>
                <div style={{ fontSize: 18, color: 'var(--suave)' }}>{e.d}</div>
              </div>
            </motion.div>
          ))}
        </div>
        <div className="panel">
          <div className="etiqueta" style={{ marginBottom: 6 }}>¿Cada cuántos fotogramas guardamos una imagen?</div>
          <p style={{ fontSize: 18, marginBottom: 22 }}>Porcentaje de imágenes casi iguales a la anterior según el intervalo elegido.</p>
          <BarrasH anchoEtiqueta={210} max={12} dec={1} retraso={0.9} paso={0.14} alto={44}
            datos={INTERVALOS.map((d) => ({ etiqueta: `cada ${d.intervalo} · ${fmt(d.imagenes)} img`, valor: d.duplicadas,
              texto: `${fmt(d.duplicadas, 1)} %`, destacado: d.intervalo === 24 }))} />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.2 }}
            style={{ marginTop: 22, fontSize: 19, color: 'var(--texto)' }}>
            Con una de cada <span className="acento mono">24</span> casi no hay repetidas (1,4 %) y quedan unos 1420 robots: una cantidad razonable para anotar entre cinco.
          </motion.p>
        </div>
      </div>
    </div>
  );
}

// --- Anotación ----------------------------------------------------------------------------------
// Uso del campo difficult: train.ipynb lo lee pero entrena con todos; test.ipynb mide aparte (como PASCAL VOC).
const DIFFICULT_USO = [
  ['Entrenan igual', 'Ni los quitamos ni les bajamos el peso: si no, la red aprendería que esos robots son fondo.'],
  ['Métricas aparte', 'AP de todos, solo normales y solo difficult. Modelo final: 0,966 frente a 0,692.'],
  ['Guían las decisiones', 'El aumento sube su AP de 0,55 a 0,63, y a igual AP elegimos el mejor en difficult.'],
];
export function Anotacion() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Anotación" titulo="Qué consideramos un robot" />
      <div className="cuerpo dos-asim">
        <div>
          <Fotograma foto={F.anotacion} modo="anotacion" retraso={0.6} paso={0.35} />
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }}
            className="mono" style={{ display: 'flex', gap: 28, marginTop: 14, fontSize: 16, color: 'var(--suave)' }}>
            <span><span style={{ display: 'inline-block', width: 26, height: 0, borderTop: '3px solid var(--acento)', verticalAlign: 'middle', marginRight: 8 }} />robot</span>
            <span><span style={{ display: 'inline-block', width: 26, height: 0, borderTop: '3px dashed var(--naranja)', verticalAlign: 'middle', marginRight: 8 }} />difficult: cortado por el borde</span>
            <span style={{ marginLeft: 'auto' }}>V04 · exterior · fotograma 1416</span>
          </motion.div>
          <Revela className="panel" retraso={2.1} paso={0.18} style={{ marginTop: 18, padding: '16px 22px' }}>
            <Item className="etiqueta" style={{ marginBottom: 10, color: 'var(--naranja)' }}>Para qué marcamos los difficult</Item>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 22 }}>
              {DIFFICULT_USO.map(([t, d]) => (
                <Item key={t}>
                  <b style={{ fontSize: 18 }}>{t}</b>
                  <p style={{ margin: '4px 0 0', fontSize: 16, lineHeight: 1.35, color: 'var(--suave)' }}>{d}</p>
                </Item>
              ))}
            </div>
          </Revela>
        </div>
        <div style={{ display: 'grid', gap: 20, alignContent: 'start' }}>
          <Revela className="panel" retraso={0.5} paso={0.1} style={{ padding: '22px 26px' }}>
            <Item className="etiqueta" style={{ marginBottom: 6 }}>Reglas que fijamos por escrito antes de anotar</Item>
            {CRITERIOS.map(([t, d]) => (
              <Item key={t} style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: 14, padding: '7px 0', fontSize: 19 }}>
                <span className="mono acento" style={{ fontSize: 16, paddingTop: 2 }}>{t}</span>
                <span className="suave">{d}</span>
              </Item>
            ))}
          </Revela>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.3 }}>
              <div className="cifra peque"><Contador valor={ANOTACION.robots} retraso={1.3} /></div>
              <div className="cifra-pie">robots anotados, <Contador valor={ANOTACION.difficult} retraso={1.4} /> de ellos difficult (26,4 %), y 41 imágenes sin robots</div>
            </motion.div>
            <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.5 }}>
              <div className="cifra peque acento"><Contador valor={ANOTACION.iouAnotadores} dec={2} retraso={1.5} /></div>
              <div className="cifra-pie">coincidencia media (IoU) de nuestras cajas en las mismas 20 imágenes difíciles</div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- EDA ------------------------------------------------------------------------------------------
function BarrasVideos() {
  const datos = generados.videos;
  const max = 200;
  const alto = 330;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${datos.length}, 1fr)`, gap: 12, alignItems: 'end', height: alto + 60 }}>
      {datos.map((v, i) => {
        const normales = v.robots - v.difficult;
        return (
          <div key={v.video} style={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', height: '100%', justifyContent: 'flex-end' }}>
            <motion.div className="mono" style={{ textAlign: 'center', fontSize: 16, fontWeight: 600, marginBottom: 6 }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 + i * 0.07 }}>{v.robots}</motion.div>
            <motion.div style={{ display: 'flex', flexDirection: 'column', gap: 2, transformOrigin: 'bottom' }}
              initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: 0.4 + i * 0.07, duration: 0.9, ease: CURVA }}>
              <div style={{ height: (v.difficult / max) * alto, background: 'var(--naranja)', borderRadius: '4px 4px 0 0' }} />
              <div style={{ height: (normales / max) * alto, background: '#4f5a49' }} />
            </motion.div>
            <div className="mono" style={{ textAlign: 'center', fontSize: 15, color: 'var(--suave)', marginTop: 8 }}>{v.video}</div>
          </div>
        );
      })}
    </div>
  );
}
const DOMINIO = [
  ['Robots por imagen', '1,76', '2,32', '2,40'],
  ['Robots difficult', '26,4 %', '16,3 %', '15,7 %'],
  ['Robots de menos de 50 px', '3,9 %', '11,3 %', '9,1 %'],
  ['Imágenes exteriores', '26,4 %', '19,9 %', '1,1 %'],
];
export function Eda() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Análisis exploratorio" titulo="Nuestros vídeos vs. los de la asignatura" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span className="etiqueta">Robots anotados por vídeo</span>
            <span className="mono" style={{ fontSize: 14, color: 'var(--suave)', display: 'flex', gap: 16 }}>
              <span><i style={{ display: 'inline-block', width: 12, height: 12, background: '#4f5a49', marginRight: 6 }} />normales</span>
              <span><i style={{ display: 'inline-block', width: 12, height: 12, background: 'var(--naranja)', marginRight: 6 }} />difficult</span>
            </span>
          </div>
          <BarrasVideos />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }} style={{ marginTop: 14, fontSize: 18 }}>
            Cada vídeo tiene una cantidad distinta de robots difíciles (de 17 en V04 a 65 en V08), así que medimos aparte cómo los detecta el modelo.
          </motion.p>
        </div>
        <div className="panel">
          <div className="etiqueta" style={{ marginBottom: 18 }}>Nuestros vídeos frente a los de la asignatura</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr repeat(3, 1fr)', rowGap: 4, fontSize: 19 }}>
            {['', 'Nuestros vídeos', 'Validación', 'Test'].map((c) => <div key={c} className="mono" style={{ fontSize: 14, color: 'var(--tenue)', paddingBottom: 10, textAlign: c ? 'right' : 'left' }}>{c}</div>)}
            {DOMINIO.map((fila, i) => fila.map((c, j) => (
              <motion.div key={`${i}-${j}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 + i * 0.25 + j * 0.06 }}
                className={j ? 'mono' : ''} style={{ padding: '12px 0', borderTop: '1px solid var(--borde)', textAlign: j ? 'right' : 'left',
                  color: j === 1 ? 'var(--acento)' : j ? 'var(--texto)' : 'var(--suave)' }}>{c}</motion.div>
            )))}
          </div>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2 }} style={{ marginTop: 22, fontSize: 19, color: 'var(--texto)' }}>
            En validación y test hay más robots por imagen y más pequeños. Por eso el aumento aleja los robots (hasta ×0,6) y probamos a darle al modelo la imagen más grande.
          </motion.p>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.4 }} style={{ marginTop: 14, fontSize: 19, color: 'var(--texto)' }}>
            Cada imagen se parece sobre todo a otras de su mismo vídeo (<span className="mono acento">74 %</span> de los casos): por eso validamos con vídeos de otros grupos, no con los nuestros.
          </motion.p>
        </div>
      </div>
    </div>
  );
}

// --- EDA: dónde aparecen los robots y de qué tamaño ----------------------------------------------------
// Datos de los XML (scripts/preparar_datos.mjs), comprobados con los apartados 4.2 a 4.4 de la memoria
const EDA = generados.eda;
const PUNTO = '#9aa592';
function Leyenda({ items }) {
  return (
    <span className="mono" style={{ fontSize: 14, color: 'var(--suave)', display: 'flex', gap: 16 }}>
      {items.map(([t, c]) => (
        <span key={t}><i style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 5, background: c, marginRight: 6 }} />{t}</span>
      ))}
    </span>
  );
}
const difficultEncima = (filas) => [...filas].sort((a, b) => a[2] - b[2]);

function MapaCentros() {
  const W = 640, H = 360;
  const [f0, f1] = EDA.franja;
  return (
    <svg className="grafica" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Centro de las 1420 cajas sobre una imagen de 16:9">
      <rect x="0.5" y="0.5" width={W - 1} height={H - 1} fill="#0f110e" stroke="var(--borde)" />
      <motion.rect x="1" width={W - 2} y={f0 * H} height={(f1 - f0) * H} fill="var(--acento)"
        initial={{ opacity: 0 }} animate={{ opacity: 0.09 }} transition={{ delay: 1.5, duration: 0.6 }} />
      {[f0, f1].map((v) => (
        <motion.line key={v} x1="1" x2={W - 1} y1={v * H} y2={v * H} stroke="var(--acento)" strokeWidth="1.5" strokeDasharray="6 6"
          initial={{ opacity: 0 }} animate={{ opacity: 0.85 }} transition={{ delay: 1.5, duration: 0.6 }} />
      ))}
      <line x1={EDA.centroXMedio * W} x2={EDA.centroXMedio * W} y1="1" y2={H - 1} stroke="var(--tenue)" strokeDasharray="3 6" />
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 1 }}>
        {difficultEncima(EDA.centros).map(([x, y, d], i) => (
          <circle key={i} cx={x * W} cy={y * H} r={d ? 3.2 : 2.6} fill={d ? 'var(--naranja)' : PUNTO} fillOpacity={d ? 0.85 : 0.4} />
        ))}
      </motion.g>
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.9 }}>
        <text x={W - 12} y={f0 * H + 22} textAnchor="end" style={{ fill: 'var(--acento)', fontWeight: 600, paintOrder: 'stroke', stroke: '#0f110e', strokeWidth: 6, strokeLinejoin: 'round' }}>80 % de los robots</text>
        <text x={EDA.centroXMedio * W + 8} y={H - 12} style={{ fill: 'var(--suave)', paintOrder: 'stroke', stroke: '#0f110e', strokeWidth: 6, strokeLinejoin: 'round' }}>centro medio · {fmt(EDA.centroXMedio, 2)}</text>
      </motion.g>
    </svg>
  );
}

// Medianas por franja, de la memoria (4.4): base por encima de 360, entre 360 y 480 y por debajo de 480
const FRANJAS_TAMANO = [[255, 'lejos', '79 × 71'], [420, 'media', '121 × 107'], [600, 'cerca', '283 × 252']];
function Perspectiva() {
  const ancho = 640, alto = 410, m = { l: 58, r: 18, t: 72, b: 56 };
  const sx = escala([150, 720], [m.l, ancho - m.r]);
  const sy = escala([15, 800], [alto - m.b, m.t], true);
  // Recta de log(alto) frente a la base, por mínimos cuadrados
  const xs = EDA.perspectiva.map((p) => p[0]);
  const ys = EDA.perspectiva.map((p) => Math.log10(p[1]));
  const mx = xs.reduce((s, v) => s + v, 0) / xs.length, my = ys.reduce((s, v) => s + v, 0) / ys.length;
  const a = xs.reduce((s, v, i) => s + (v - mx) * (ys[i] - my), 0) / xs.reduce((s, v) => s + (v - mx) ** 2, 0);
  const recta = (x) => 10 ** (my + a * (x - mx));
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="Alto de cada caja frente a la posición de su base">
      <Ejes ancho={ancho} alto={alto} m={m} sx={sx} sy={sy} ticksX={[200, 300, 400, 500, 600, 700]} ticksY={[25, 50, 100, 200, 400]}
        tituloX="base de la caja (px desde arriba) → más cerca" tituloY="alto (px)" />
      {[360, 480].map((v) => <line key={v} x1={sx(v)} x2={sx(v)} y1={32} y2={alto - m.b} stroke="var(--tenue)" strokeDasharray="3 6" />)}
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 1 }}>
        {difficultEncima(EDA.perspectiva).map(([b, h, d], i) => (
          <circle key={i} cx={sx(b)} cy={sy(h)} r={d ? 3 : 2.5} fill={d ? 'var(--naranja)' : PUNTO} fillOpacity={d ? 0.8 : 0.4} />
        ))}
      </motion.g>
      <motion.line x1={sx(160)} x2={sx(715)} y1={sy(recta(160))} y2={sy(recta(715))} stroke="var(--acento)" strokeWidth="2.5"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.4, duration: 1 }} />
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2 }}>
        {FRANJAS_TAMANO.map(([x, t, v]) => (
          <text key={t} x={sx(x)} y={22} textAnchor="middle"><tspan style={{ fill: 'var(--tenue)' }}>{t} · </tspan>
            <tspan className="valor">{v}</tspan></text>
        ))}
        <text x={sx(712)} y={sy(28)} textAnchor="end" style={{ fill: 'var(--acento)', fontWeight: 600 }}>correlación {fmt(EDA.rPerspectiva, 2)}</text>
      </motion.g>
    </svg>
  );
}

export function EdaPosicion() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Análisis exploratorio" titulo="Dónde aparecen los robots y de qué tamaño" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        <div className="panel" style={{ display: 'grid', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="etiqueta">Centro de las 1420 cajas</span>
            <Leyenda items={[['normal', PUNTO], ['difficult', 'var(--naranja)']]} />
          </div>
          <MapaCentros />
          <Revela as="ul" className="lista" retraso={2.2} paso={0.3} style={{ fontSize: 18, gap: 10 }}>
            <Item as="li"><span><b>A media altura y por igual a los dos lados:</b> volteo horizontal sí; desplazamiento vertical, solo ±5 %.</span></Item>
            <Item as="li"><span><b>Los difficult, hacia los bordes:</b> son el <span className="mono acento">{EDA.borde.pctDifficult} %</span> de las
              cajas que tocan el borde, frente al {EDA.borde.pctDifficultResto} % del resto.</span></Item>
          </Revela>
        </div>
        <div className="panel" style={{ display: 'grid', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="etiqueta">Tamaño según la posición</span>
            <span className="mono" style={{ fontSize: 14, color: 'var(--tenue)' }}>{fmt(EDA.perspectiva.length)} cajas sin cortar</span>
          </div>
          <Perspectiva />
          <Revela as="ul" className="lista" retraso={2.6} paso={0.3} style={{ fontSize: 18, gap: 10 }}>
            <Item as="li"><span><b>Cuanto más cerca, más abajo y más grande:</b> la cámara va a ras de suelo. Por eso la escala del aumento
              no deforma el robot ni lo saca de su franja.</span></Item>
          </Revela>
        </div>
      </div>
    </div>
  );
}

// --- EDA: forma, solapamiento y nitidez ------------------------------------------------------------
function Forma() {
  const ancho = 400, alto = 370, m = { l: 50, r: 34, t: 34, b: 48 };
  const sx = escala([20, 1000], [m.l, ancho - m.r], true);
  const sy = escala([20, 1000], [alto - m.b, m.t], true);
  const lineas = [[1, '1:1'], [0.5, '2:1'], [2, '1:2']];
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="Ancho frente a alto de las 1420 cajas">
      <Ejes ancho={ancho} alto={alto} m={m} sx={sx} sy={sy} ticksX={[30, 100, 300, 1000]} ticksY={[30, 100, 300, 1000]}
        tituloX="ancho (px)" />
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 1 }}>
        {difficultEncima(EDA.forma).map(([w, h, d], i) => (
          <circle key={i} cx={sx(w)} cy={sy(h)} r={d ? 2.6 : 2.2} fill={d ? 'var(--naranja)' : PUNTO} fillOpacity={d ? 0.8 : 0.4} />
        ))}
      </motion.g>
      {lineas.map(([k, t], i) => {
        const x0 = Math.max(20, 20 / k), x1 = Math.min(1000, 1000 / k);
        return (
          <motion.g key={t} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4 + i * 0.2 }}>
            <line x1={sx(x0)} x2={sx(x1)} y1={sy(x0 * k)} y2={sy(x1 * k)} stroke={k === 1 ? 'var(--acento)' : 'var(--tenue)'}
              strokeWidth={k === 1 ? 2 : 1.5} strokeDasharray={k === 1 ? undefined : '5 5'} />
            <text x={sx(x1) + (k === 2 ? -6 : 6)} y={sy(x1 * k) + 5} textAnchor={k === 2 ? 'end' : 'start'}
              style={{ fill: k === 1 ? 'var(--acento)' : 'var(--suave)' }}>{t}</text>
          </motion.g>
        );
      })}
      <text x={m.l - 12} y={12} style={{ fill: 'var(--tenue)' }}>alto (px)</text>
    </svg>
  );
}

function Solape() {
  const ancho = 400, alto = 370, m = { l: 18, r: 18, t: 40, b: 48 };
  const sx = escala([0, 1], [m.l, ancho - m.r]);
  // Gráfico de puntos: cada pareja que se toca, apilada en su intervalo de 0,02 de IoU
  const pilas = {};
  const puntos = EDA.solape.positivos.map((v) => {
    const k = Math.min(49, Math.floor(v / 0.02));
    pilas[k] = (pilas[k] || 0) + 1;
    return { x: sx(k * 0.02 + 0.01), y: alto - m.b - 6 - (pilas[k] - 1) * 8.5 };
  });
  const sinTocarse = EDA.solape.parejas - EDA.solape.seTocan;
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="IoU de las parejas de robots que se tocan">
      <line className="eje" x1={m.l} x2={ancho - m.r} y1={alto - m.b} y2={alto - m.b} />
      {[0, 0.25, 0.5, 0.75, 1].map((t) => <text key={t} x={sx(t)} y={alto - m.b + 26} textAnchor="middle">{String(t).replace('.', ',')}</text>)}
      <text x={(m.l + ancho - m.r) / 2} y={alto - 6} textAnchor="middle" style={{ fill: 'var(--tenue)' }}>IoU entre dos robots de la misma imagen</text>
      {puntos.map((p, i) => (
        <motion.circle key={i} cx={p.x} cy={p.y} r="3.6" fill="var(--azul)" initial={{ opacity: 0, cy: p.y - 20 }} animate={{ opacity: 0.9, cy: p.y }}
          transition={{ delay: 0.5 + i * 0.012, duration: 0.4 }} />
      ))}
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }}>
        <line x1={sx(0.5)} x2={sx(0.5)} y1={m.t + 18} y2={alto - m.b} stroke="var(--rojo)" strokeWidth="2" strokeDasharray="6 5" />
        <text x={sx(0.5) + 8} y={m.t + 32} style={{ fill: 'var(--rojo)' }}>la NMS borra</text>
        <text x={sx(0.5) + 8} y={m.t + 50} style={{ fill: 'var(--rojo)' }}>a partir de 0,5</text>
        <text x={sx(EDA.solape.max)} y={m.t + 92} textAnchor="middle" style={{ fill: 'var(--azul)' }}>máx. {fmt(EDA.solape.max, 2)}</text>
        <line x1={sx(EDA.solape.max)} x2={sx(EDA.solape.max)} y1={m.t + 100} y2={alto - m.b - 14} stroke="var(--azul)" strokeDasharray="2 4" />
        <text x={m.l} y={m.t + 4} style={{ fill: 'var(--suave)' }}><tspan className="valor">{sinTocarse}</tspan> parejas no se tocan;</text>
        <text x={m.l} y={m.t + 24} style={{ fill: 'var(--suave)' }}><tspan className="valor">{EDA.solape.seTocan}</tspan> sí</text>
      </motion.g>
    </svg>
  );
}

function Nitidez() {
  const ancho = 400, alto = 370, m = { l: 14, r: 14, t: 60, b: 48 };
  const sy = escala([0, 60], [alto - m.b, m.t]);
  const paso = (ancho - m.l - m.r) / 4;
  const etiquetas = ['menos nítidas', '', '', 'más nítidas'];
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label="Porcentaje de robots difficult según la nitidez de la imagen">
      <line className="eje" x1={m.l} x2={ancho - m.r} y1={alto - m.b} y2={alto - m.b} />
      {EDA.nitidez.map((q, i) => {
        const x = m.l + i * paso + paso * 0.2, w = paso * 0.6;
        return (
          <g key={i}>
            <motion.rect x={x} width={w} rx="4" fill="var(--naranja)" fillOpacity={i === 0 ? 1 : 0.55}
              initial={{ y: sy(0), height: 0 }} animate={{ y: sy(q.pctDifficult), height: sy(0) - sy(q.pctDifficult) }}
              transition={{ delay: 0.5 + i * 0.15, duration: 0.8, ease: CURVA }} />
            <motion.text x={x + w / 2} y={sy(q.pctDifficult) - 10} textAnchor="middle" className="valor" style={{ fontSize: 18 }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 + i * 0.15 }}>{Math.round(q.pctDifficult)} %</motion.text>
            <text x={x + w / 2} y={alto - m.b + 24} textAnchor="middle">{`${i + 1}.º`}</text>
            {etiquetas[i] && <text x={i ? ancho - m.r : m.l} y={alto - 8} textAnchor={i ? 'end' : 'start'} style={{ fill: 'var(--tenue)' }}>{etiquetas[i]}</text>}
          </g>
        );
      })}
      <text x={m.l} y={m.t - 22} style={{ fill: 'var(--tenue)', fontSize: 13 }}>robots difficult, por cuartos de nitidez</text>
    </svg>
  );
}

const PANELES_CAJAS = [
  { t: 'Forma', cifra: fmt(EDA.aspectoMediano, 2), pie: 'ancho / alto mediano', Grafica: Forma, leyenda: true,
    texto: <>Casi cuadradas a cualquier tamaño y entre 1:2 y 2:1, como las anclas del detector: el <span className="mono acento">99,6 %</span> encaja con IoU ≥ 0,5. Dejamos las anclas por defecto.</> },
  { t: 'Robots juntos', cifra: fmt(EDA.solape.max, 2), pie: 'IoU máximo entre dos robots', Grafica: Solape,
    texto: <>De {EDA.solape.parejas} parejas de robots en la misma imagen, ninguna se solapa más de {fmt(EDA.solape.max, 2)}: la NMS a 0,5 no borra un robot que esté junto a otro.</> },
  { t: 'Nitidez', cifra: `${Math.round(EDA.nitidez[0].pctDifficult)} %`, pie: 'difficult en las imágenes menos nítidas', Grafica: Nitidez,
    texto: <>Dentro de cada vídeo, cuanto más movida la imagen, más difficult: son robots movidos. Por eso el aumento añade desenfoque de movimiento.</> },
];
export function EdaCajas() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Análisis exploratorio" titulo="Cómo son las cajas y por qué hay robots difíciles" />
      <div className="cuerpo tres" style={{ alignItems: 'stretch', gap: 24 }}>
        {PANELES_CAJAS.map((p, i) => (
          <motion.div key={p.t} className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '20px 22px' }}
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 + i * 0.2, duration: 0.5, ease: CURVA }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <span className="etiqueta">{p.t}</span>
              {p.leyenda && <Leyenda items={[['normal', PUNTO], ['difficult', 'var(--naranja)']]} />}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span className="cifra peque acento">{p.cifra}</span>
              <span style={{ fontSize: 16, color: 'var(--suave)' }}>{p.pie}</span>
            </div>
            <p.Grafica />
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 + i * 0.3 }}
              style={{ margin: 0, fontSize: 17, lineHeight: 1.45, color: 'var(--texto)' }}>{p.texto}</motion.p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// --- Aumento y depuración ----------------------------------------------------------------------------
// Transformaciones del perfil robusto_v1, el del entrenamiento de todos los modelos de la cadena (incluido el final):
// el aumentador de ENTREGA 1/WEEK1/data_aug.ipynb y las ampliaciones de herramientas/aumento_robusto.py.
const LISTA_AUMENTO = [
  { g: 'Geometría', t: 'Volteo horizontal', p: '50 %', d: 'el rival puede estar a cualquier lado' },
  { g: 'Geometría', t: 'Escala ×0,6 a ×1,25', p: '70 %', d: 'robots más lejanos o cortados' },
  { g: 'Geometría', t: 'Desplazamiento y giro ±6°', p: '70 %', d: 'la cámara se inclina al acelerar' },
  { g: 'Color', t: 'Brillo, contraste o gamma', p: '50 %', d: 'otras luces y otras horas' },
  { g: 'Color', t: 'Tono, saturación o canales', p: '30 %', d: 'balance de blancos de otra cámara' },
  { g: 'Calidad', t: 'Desenfoque de movimiento', p: '15 %', d: 'robot o cámara en marcha' },
  { g: 'Calidad', t: 'JPEG, ruido o menos resolución', p: '30 %', d: 'vídeo comprimido de otros grupos' },
  { g: 'Extra', t: 'Sombras y llovizna en exteriores', p: '25 · 15 %', d: 'V04 y V09, grabados al aire libre' },
  { g: 'Extra', t: 'Tapar hasta un 25 % del robot', p: '15 %', d: 'robots detrás de obstáculos' },
  { g: 'Extra', t: 'Oscurecer o mover los difficult', p: '50 %', d: 'más ejemplos de los que más falla' },
];
const COLOR_GRUPO = { Geometría: 'var(--azul)', Color: 'var(--naranja)', Calidad: '#c9a7ff', Extra: 'var(--acento)' };
const NO_USADAS = AUMENTO_IMAGENES.filter((x) => x.usada === false);

function AumentoEnVivo({ i }) {
  const t = AUMENTO_IMAGENES[i];
  const primeraNoUsada = AUMENTO_IMAGENES.findIndex((x) => x.usada === false);
  return (
    <div>
      <div className="fotograma" style={{ background: '#3a3d38' }}>
        <AnimatePresence initial={false}>
          <motion.img key={t.clave} src={t.src} alt={`Aumento de datos: ${t.titulo}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            exit={{ opacity: 0 }} transition={{ duration: 0.35 }}
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
        </AnimatePresence>
        <div key={`${t.clave}-cajas`} style={{ position: 'absolute', inset: 0 }}>
          {t.cajas.map((c, k) => <Caja key={k} caja={c} tipo={c.difficult ? 'difficult' : 'robot'} retraso={0.2 + k * 0.08} mostrarRotulo={false} />)}
        </div>
        <span className={`chip${t.usada === false ? '' : ' on'}`} style={{ position: 'absolute', left: 14, top: 14, zIndex: 3 }}>{t.titulo}</span>
        {t.usada !== null && (
          <span className="chip" style={{ position: 'absolute', right: 14, top: 14, zIndex: 3, fontWeight: 600,
            color: 'var(--fondo)', background: t.usada ? 'var(--acento)' : 'var(--rojo)', borderColor: 'transparent' }}>
            {t.usada ? 'se usó' : 'no se usó'}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', gap: 4, marginTop: 10 }}>
        {AUMENTO_IMAGENES.map((x, k) => (
          <div key={x.clave} style={{ flex: 1, height: 4, marginLeft: k === primeraNoUsada ? 10 : 0, transition: 'background .3s',
            background: k === i ? (x.usada === false ? 'var(--rojo)' : 'var(--acento)') : (x.usada === false ? '#4a2c2c' : 'var(--borde)') }} />
        ))}
      </div>
      <p style={{ margin: '10px 0 0', minHeight: 50, fontSize: 18, lineHeight: 1.4, color: 'var(--suave)' }}>
        {t.usada === null && 'Cada transformación, aplicada sola con el código del aumento: las cajas se mueven con la imagen.'}
        {t.usada === true && <><b style={{ color: 'var(--texto)' }}>Se usó para entrenar:</b> {LISTA_AUMENTO[t.fila].d}.</>}
        {t.usada === false && <><b style={{ color: 'var(--rojo)' }}>No se usó:</b> {t.motivo}.</>}
      </p>
    </div>
  );
}

export function Aumento() {
  const [i, setI] = useState(0);
  const reducido = useReducedMotion();
  useEffect(() => {
    if (reducido) return undefined;
    const id = setInterval(() => setI((n) => (n + 1) % AUMENTO_IMAGENES.length), 1600);
    return () => clearInterval(id);
  }, [reducido]);
  const actual = AUMENTO_IMAGENES[i];
  const flujo = [
    { v: DATASET.originales, t: 'originales' },
    { v: DATASET.depuradas, t: 'tras depurar', d: 'quitamos 11 casi repetidas y 1 mal anotada' },
    { v: DATASET.total, t: 'para entrenar', d: `cada imagen y 3 versiones aumentadas · ${fmt(DATASET.cajasTotal)} robots`, acento: true },
  ];
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Aumento y depuración" titulo="Más imágenes sin grabar escenas nuevas" />
      <div className="cuerpo" style={{ gridTemplateColumns: '0.95fr 1.05fr', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 14 }}>
          <AumentoEnVivo i={i} />
          <div className="panel" style={{ display: 'grid', gridTemplateColumns: '0.8fr auto 1fr auto 1.2fr', alignItems: 'start', gap: 12, padding: '16px 22px' }}>
            {flujo.map((f, k) => [
              <motion.div key={f.t} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 + k * 0.45 }}>
                <div className={`cifra peque${f.acento ? ' acento' : ''}`}><Contador valor={f.v} retraso={1.2 + k * 0.45} duracion={1} /></div>
                <div style={{ fontSize: 18, color: 'var(--texto)', marginTop: 4 }}>{f.t}</div>
                {f.d && <div style={{ fontSize: 15, color: 'var(--suave)', lineHeight: 1.3 }}>{f.d}</div>}
              </motion.div>,
              k < flujo.length - 1 && (
                <motion.span key={`f${k}`} className="mono acento" style={{ fontSize: 26, paddingTop: 4 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: 1.4 + k * 0.45 }}>{k === 1 ? '×4' : '→'}</motion.span>
              ),
            ])}
          </div>
        </div>
        <div className="panel" style={{ padding: '14px 24px 16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.08fr 92px 1fr', gap: 14, paddingBottom: 6 }}>
            {['Se usaron', 'Prob.', 'Para qué'].map((c) => <span key={c} className="etiqueta">{c}</span>)}
          </div>
          <Revela retraso={0.4} paso={0.08}>
            {LISTA_AUMENTO.map((x, k) => {
              const activa = actual.usada === true && actual.fila === k;
              return (
                <Item key={x.t} style={{ display: 'grid', gridTemplateColumns: '1.08fr 92px 1fr', gap: 14, alignItems: 'baseline', padding: '7px 8px',
                  margin: '0 -8px', borderTop: '1px solid var(--borde)', transition: 'background .3s, box-shadow .3s',
                  background: activa ? 'var(--panel-2)' : 'transparent', boxShadow: activa ? 'inset 3px 0 0 var(--acento)' : 'none' }}>
                  <span style={{ fontSize: 17, color: 'var(--texto)' }}>
                    <i style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 5, background: COLOR_GRUPO[x.g], marginRight: 10, verticalAlign: 'middle' }} />{x.t}
                  </span>
                  <span className="mono" style={{ fontSize: 15, color: 'var(--suave)' }}>{x.p}</span>
                  <span style={{ fontSize: 16, color: 'var(--suave)' }}>{x.d}</span>
                </Item>
              );
            })}
          </Revela>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4 }}
            style={{ borderTop: '1px solid var(--borde)', paddingTop: 10 }}>
            <div className="etiqueta">No se usaron</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
              {NO_USADAS.map((x) => {
                const activa = actual.clave === x.clave;
                return (
                  <span key={x.clave} className="chip" style={{ fontSize: 14, padding: '4px 9px', transition: 'all .3s',
                    color: activa ? 'var(--fondo)' : 'var(--suave)', background: activa ? 'var(--rojo)' : 'transparent',
                    borderColor: activa ? 'var(--rojo)' : 'var(--borde)' }}>{x.titulo}</span>
                );
              })}
            </div>
          </motion.div>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.2 }} style={{ margin: '12px 0 0', fontSize: 17, lineHeight: 1.4, color: 'var(--texto)' }}>
            Con aumento, Faster R-CNN v1 pasa de <span className="mono">0,923</span> a <span className="mono acento">0,942</span> de AP@0,5 en validación.
            Los extras (en verde) no lo cambian (<span className="mono">0,943</span> con y sin ellos), pero se entrenaron con ellos todos los modelos, también el final.
          </motion.p>
        </div>
      </div>
    </div>
  );
}
