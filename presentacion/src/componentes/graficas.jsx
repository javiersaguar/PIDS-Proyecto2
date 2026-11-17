import { easeInOut, motion, useReducedMotion } from 'framer-motion';
import { CURVA, fmt } from './base.jsx';
import { Esquinas } from './fotograma.jsx';

// --- barras horizontales (HTML) -----------------------------------------------------------------
// datos: [{ etiqueta, valor, texto?, destacado?, nulo? }]; min/max fijan la escala del eje.
// fijar: segundo en el que las esquinas se enganchan a la barra destacada. nuloTiembla: la etiqueta sin valor tiembla.
export function BarrasH({ datos, min = 0, max = 1, dec = 3, retraso = 0.3, paso = 0.12, alto = 46, anchoEtiqueta = 300,
  colorDestacado = 'var(--acento)', textoNulo = 'sin memoria', fijar, nuloTiembla = false }) {
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {datos.map((d, i) => {
        const frac = d.valor == null ? 0 : Math.max(0, Math.min(1, (d.valor - min) / (max - min)));
        return (
          <div key={d.etiqueta} style={{ display: 'grid', gridTemplateColumns: `${anchoEtiqueta}px 1fr`, alignItems: 'center', gap: 18 }}>
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: retraso + i * paso, duration: 0.5 }}
              style={{ textAlign: 'right', color: d.destacado ? 'var(--texto)' : 'var(--suave)', fontSize: 20, lineHeight: 1.15 }}>
              {d.etiqueta}
            </motion.div>
            <div style={{ position: 'relative', height: alto, display: 'flex', alignItems: 'center' }}>
              {d.valor == null ? (
                <motion.span className="mono" initial={{ opacity: 0 }} animate={{ opacity: 1, x: nuloTiembla ? [0, -5, 5, -4, 3, -1, 0] : 0 }}
                  transition={{ delay: retraso + i * paso + 0.3, x: { delay: retraso + i * paso + 0.9, duration: 0.45 } }}
                  style={{ display: 'inline-block', color: 'var(--rojo)', fontSize: 18, border: '1px dashed var(--rojo)', padding: '6px 10px', borderRadius: 2 }}>
                  {d.texto || textoNulo}
                </motion.span>
              ) : (
                <>
                  <motion.div initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
                    transition={{ delay: retraso + i * paso, duration: 0.9, ease: CURVA }}
                    style={{ width: `${Math.max(frac * 100, 0.6)}%`, height: '100%', transformOrigin: 'left',
                      background: d.color || (d.destacado ? colorDestacado : '#3b4037'), borderRadius: '0 4px 4px 0' }} />
                  <motion.span className="mono" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: retraso + i * paso + 0.6 }}
                    style={{ marginLeft: 14, fontSize: 21, fontWeight: 600, color: d.destacado ? 'var(--texto)' : 'var(--suave)', whiteSpace: 'nowrap' }}>
                    {d.texto || fmt(d.valor, dec)}
                  </motion.span>
                  {fijar != null && d.destacado && (
                    <Esquinas retraso={fijar} color={d.color || colorDestacado} tam={11} grosor={2}
                      style={{ left: -6, top: -5, bottom: -5, right: 'auto', width: `calc(${Math.max(frac * 100, 0.6)}% + 12px)` }} />
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// --- utilidades de escala para las gráficas SVG ---------------------------------------------------
export function escala([d0, d1], [r0, r1], log = false) {
  const f = log ? Math.log10 : (v) => v;
  return (v) => r0 + ((f(v) - f(d0)) / (f(d1) - f(d0))) * (r1 - r0);
}
const camino = (xs, ys, sx, sy) => xs.map((x, i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join('');

// Ejes con rejilla horizontal, ticks y títulos
export function Ejes({ ancho, alto, m, sx, sy, ticksX, ticksY, fx = (v) => v, fy = (v) => v, tituloX, tituloY }) {
  return (
    <g>
      <g className="rejilla">
        {ticksY.map((t) => <line key={t} x1={m.l} x2={ancho - m.r} y1={sy(t)} y2={sy(t)} />)}
      </g>
      <line className="eje" x1={m.l} x2={ancho - m.r} y1={alto - m.b} y2={alto - m.b} />
      {ticksX.map((t) => <text key={t} x={sx(t)} y={alto - m.b + 26} textAnchor="middle">{fx(t)}</text>)}
      {ticksY.map((t) => <text key={t} x={m.l - 12} y={sy(t) + 5} textAnchor="end">{fy(t)}</text>)}
      {tituloX && <text x={(m.l + ancho - m.r) / 2} y={alto - 6} textAnchor="middle" style={{ fill: 'var(--tenue)' }}>{tituloX}</text>}
      {tituloY && <text x={m.l - 12} y={m.t - 18} textAnchor="start" style={{ fill: 'var(--tenue)' }}>{tituloY}</text>}
    </g>
  );
}

// Puntos por los que pasa la punta de una línea mientras se dibuja (misma curva de tiempo que el trazo)
function recorrido(xs, ys, sx, sy, n = 44) {
  const p = xs.map((x, i) => [sx(x), sy(ys[i])]);
  const acum = [0];
  for (let i = 1; i < p.length; i += 1) acum.push(acum[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]));
  const cx = [];
  const cy = [];
  for (let k = 0; k <= n; k += 1) {
    const d = easeInOut(k / n) * acum[acum.length - 1];
    let j = 1;
    while (j < p.length - 1 && acum[j] < d) j += 1;
    const f = (d - acum[j - 1]) / (acum[j] - acum[j - 1] || 1);
    cx.push(p[j - 1][0] + (p[j][0] - p[j - 1][0]) * f);
    cy.push(p[j - 1][1] + (p[j][1] - p[j - 1][1]) * f);
  }
  return { cx, cy };
}
// Punto luminoso en la punta de la línea, como en un osciloscopio. punta: true | { r, hueca, fija }
function Punta({ s, sx, sy, retraso, duracion }) {
  const { cx, cy } = recorrido(s.x, s.y, sx, sy);
  const o = s.punta === true ? {} : s.punta;
  const transicion = { delay: retraso, duration: duracion, ease: 'linear' };
  const opacidad = (v) => ({ opacity: o.fija ? [0, v, v, v] : [0, v, v, 0] });
  const tiempos = { ...transicion, times: [0, 0.04, 0.94, 1] };
  return (
    <g>
      {!o.hueca && (
        <motion.circle r={(o.r || 4) * 2.4} fill={s.color} initial={{ cx: cx[0], cy: cy[0], opacity: 0 }}
          animate={{ cx, cy, ...opacidad(0.28) }} transition={{ ...transicion, opacity: tiempos }} />
      )}
      <motion.circle r={o.r || 4} fill={o.hueca ? 'var(--fondo)' : s.color} stroke={o.hueca ? s.color : 'none'} strokeWidth={o.hueca ? 3 : 0}
        initial={{ cx: cx[0], cy: cy[0], opacity: 0 }} animate={{ cx, cy, ...opacidad(1) }} transition={{ ...transicion, opacity: tiempos }} />
    </g>
  );
}

// --- líneas que se dibujan --------------------------------------------------------------------
// series: [{ nombre, x, y, color, ancho?, discontinua?, retraso?, etiqueta? ({dx,dy,texto}), punta? }]
export function Lineas({ series, dominioX, dominioY, ticksX, ticksY, fx, fy, tituloX, tituloY, ancho = 760, alto = 440,
  m = { l: 70, r: 30, t: 40, b: 64 }, duracion = 1.8, extra, logX = false }) {
  const sx = escala(dominioX, [m.l, ancho - m.r], logX);
  const sy = escala(dominioY, [alto - m.b, m.t]);
  const reducido = useReducedMotion();
  return (
    <svg className="grafica" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={series.map((s) => s.nombre).join(', ')}>
      <Ejes {...{ ancho, alto, m, sx, sy, ticksX, ticksY, fx, fy, tituloX, tituloY }} />
      {series.map((s) => {
        // La etiqueta va en el último punto o, con etiqueta.en = 'inicio', en el primero
        const ult = s.etiqueta?.en === 'inicio' ? 0 : s.x.length - 1;
        return (
          <g key={s.nombre}>
            <motion.path d={camino(s.x, s.y, sx, sy)} fill="none" stroke={s.color} strokeWidth={s.ancho || 2.5}
              strokeLinejoin="round" strokeLinecap="round" strokeDasharray={s.discontinua ? '7 6' : undefined}
              initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }}
              transition={{ delay: s.retraso || 0.3, duration: s.duracion || duracion, ease: 'easeInOut' }} />
            {s.etiqueta !== false && (
              <motion.text x={sx(s.x[ult]) + (s.etiqueta?.dx || 10)} y={sy(s.y[ult]) + (s.etiqueta?.dy || 5)}
                style={{ fill: s.colorTexto || 'var(--texto)', fontSize: 16, fontWeight: 600 }} textAnchor={s.etiqueta?.ancla || 'start'}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: (s.retraso || 0.3) + (s.duracion || duracion) }}>
                {s.etiqueta?.texto || s.nombre}
              </motion.text>
            )}
            {s.punta && !reducido && <Punta s={s} sx={sx} sy={sy} retraso={s.retraso || 0.3} duracion={s.duracion || duracion} />}
          </g>
        );
      })}
      {extra && extra({ sx, sy, m, ancho, alto })}
    </svg>
  );
}
