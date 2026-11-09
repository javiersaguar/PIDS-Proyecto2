import { useEffect, useMemo, useState } from 'react';
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Paso, Revela } from '../componentes/base.jsx';
import { Caja } from '../componentes/fotograma.jsx';
import { BarrasH } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { CAMUFLAJE, CIRCUITO, PRESUPUESTO, SOPORTES } from '../datos/cifras.js';
import laboratorioJpg from '@repo/docs/informes/figuras/bloque3/laboratorio.jpg';
import mandoJpg from '@repo/docs/informes/figuras/bloque3/mando.jpg';
import detectiveJpg from '@repo/docs/informes/figuras/senuelo/detective.jpg';
import aliadoJpg from '@repo/docs/informes/figuras/senuelo/aliado_s1.jpg';
import circuitoPng from '@repo/docs/informes/figuras/circuito_demo.png';

// Una de las tres imágenes de la cámara del robot de la figura del laboratorio (sin su pie)
function Laboratorio({ i, style }) {
  return (
    <div role="img" aria-label={['Rival detectado y centrado', 'Foto del robot en su caja', 'Imagen corrupta del vídeo'][i]}
      style={{ aspectRatio: '760 / 428', backgroundImage: `url(${laboratorioJpg})`, backgroundSize: '303.16% auto',
        backgroundPosition: `${i * 50}% 0`, backgroundRepeat: 'no-repeat', borderRadius: 4, border: '1px solid var(--borde)', ...style }} />
  );
}

// --- Separador ---------------------------------------------------------------------------------
export function Seccion3() {
  return (
    <Seccion numero="03" titulo="Robot" color="var(--rojo)" fotos={[laboratorioJpg, mandoJpg, circuitoPng, detectiveJpg, aliadoJpg]}
      lema="Llevamos el detector al RoboMaster: recorrer el circuito, encontrar a los rivales y dispararles."
      puntos={['SDK en Python 3.8', 'circuito por tramos', 'puntería por pasos', 'ataque en marcha', 'robot camuflado', 'mando']} />
  );
}

// --- Integración: portátil, wifi y robot -------------------------------------------------------------
function Latencia() {
  const reducido = useReducedMotion();
  return (
    <div className="panel" style={{ padding: '22px 26px' }}>
      <div className="etiqueta" style={{ marginBottom: 14 }}>Lo que tarda una imagen, a escala real</div>
      {[
        { n: 'CPU del portátil del laboratorio', s: 2.3, c: 'var(--rojo)', t: '2,2–2,4 s' },
        { n: 'Lo que pediría ver y moverse a la vez', s: 0.1, c: 'var(--acento)', t: '0,1 s · 10 imágenes/s' },
      ].map((b, i) => (
        <div key={b.n} style={{ display: 'grid', gridTemplateColumns: '330px 1fr', alignItems: 'center', gap: 16, marginTop: i ? 12 : 0 }}>
          <span style={{ fontSize: 19, color: 'var(--suave)', textAlign: 'right' }}>{b.n}</span>
          <div style={{ position: 'relative', height: 30, background: 'var(--panel-2)', borderRadius: 2 }}>
            <motion.div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${(b.s / 2.5) * 100}%`, background: b.c, transformOrigin: 'left', borderRadius: '0 3px 3px 0' }}
              initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
              transition={{ delay: 1.2, duration: reducido ? 0 : b.s, ease: 'linear', repeat: reducido ? 0 : Infinity, repeatDelay: 2.5 - b.s + 0.8 }} />
            <span className="mono" style={{ position: 'absolute', left: `calc(${(b.s / 2.5) * 100}% + 10px)`, top: 4, fontSize: 16, whiteSpace: 'nowrap' }}>{b.t}</span>
          </div>
        </div>
      ))}
      <p style={{ marginTop: 16, fontSize: 23, color: 'var(--texto)' }}>
        Más de 20 veces más lento de lo que haría falta: el robot se para a mirar.
      </p>
    </div>
  );
}
function Enlace() {
  const reducido = useReducedMotion();
  const caja = (titulo, lineas, x) => (
    <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + x * 0.25, duration: 0.6, ease: CURVA }}
      style={{ padding: '20px 24px' }}>
      <h3 style={{ fontSize: 24 }}>{titulo}</h3>
      <ul className="lista" style={{ fontSize: 21, gap: 8 }}>{lineas.map((l) => <li key={l}><span>{l}</span></li>)}</ul>
    </motion.div>
  );
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 230px 1fr', alignItems: 'center' }}>
      {caja('Portátil', ['SDK oficial: obliga a Python 3.8', 'Sin GPU: el detector va en CPU', 'Robot simulado para probar'], 0)}
      <div style={{ position: 'relative', height: 120 }}>
        <svg viewBox="0 0 230 120" style={{ width: '100%', height: '100%' }} aria-hidden>
          <line x1="10" x2="220" y1="40" y2="40" stroke="var(--acento)" strokeDasharray="4 6" />
          <line x1="10" x2="220" y1="80" y2="80" stroke="var(--azul)" strokeDasharray="4 6" />
          <text x="115" y="28" textAnchor="middle" style={{ font: '14px var(--mono)', fill: 'var(--acento)' }}>vídeo 1280 × 720</text>
          <text x="115" y="106" textAnchor="middle" style={{ font: '14px var(--mono)', fill: 'var(--azul)' }}>órdenes</text>
          {!reducido && [0, 1, 2].map((k) => (
            <g key={k}>
              <rect width="14" height="9" y="35.5" fill="var(--acento)">
                <animate attributeName="x" from="210" to="10" dur="1.4s" begin={`${1 + k * 0.47}s`} repeatCount="indefinite" />
              </rect>
              <circle r="4" cy="80" fill="var(--azul)">
                <animate attributeName="cx" from="12" to="218" dur="1.4s" begin={`${1.2 + k * 0.47}s`} repeatCount="indefinite" />
              </circle>
            </g>
          ))}
        </svg>
        <div className="mono" style={{ position: 'absolute', left: 0, right: 0, top: 48, textAlign: 'center', fontSize: 13, color: 'var(--tenue)' }}>wifi</div>
      </div>
      {caja('RoboMaster EP', ['Chasis mecanum: 0,5 m/s', 'Torreta: 30 °/s', 'Cámara y emisor de infrarrojos'], 1)}
    </div>
  );
}
export function Integracion() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Integración" titulo="Cómo conectamos el detector al robot" />
      <div style={{ display: 'grid', gap: 26 }}>
        <Enlace />
        <Latencia />
        <Revela style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }} retraso={1.6} paso={0.12}>
          {[['Topes', '0,5 m/s y 30 °/s'], ['Órdenes que caducan', 'Sin órdenes, se para'],
            ['Final seguro', 'Para y guarda evidencias']].map(([t, d]) => (
            <Item key={t} className="panel" style={{ padding: '16px 20px' }}><b style={{ fontSize: 22 }}>{t}</b><p style={{ fontSize: 20, marginTop: 4 }}>{d}</p></Item>
          ))}
        </Revela>
      </div>
    </div>
  );
}

// --- El circuito ------------------------------------------------------------------------------------
const ESC = 112;
const px = ([x, y]) => [70 + x * ESC, 40 + (y + 2.4) * ESC];
function longitudes(puntos) {
  const tramos = puntos.slice(1).map((p, i) => Math.hypot(p[0] - puntos[i][0], p[1] - puntos[i][1]));
  return { tramos, total: tramos.reduce((a, b) => a + b, 0) };
}
function puntoEn(puntos, { tramos, total }, f) {
  let d = f * total;
  for (let i = 0; i < tramos.length; i += 1) {
    if (d <= tramos[i]) {
      const t = tramos[i] ? d / tramos[i] : 0;
      return [puntos[i][0] + (puntos[i + 1][0] - puntos[i][0]) * t, puntos[i][1] + (puntos[i + 1][1] - puntos[i][1]) * t];
    }
    d -= tramos[i];
  }
  return puntos[puntos.length - 1];
}
function Mapa() {
  const { puntos, ataques, rivales } = CIRCUITO;
  const largos = useMemo(() => longitudes(puntos), [puntos]);
  const progreso = useMotionValue(0);
  const reducido = useReducedMotion();
  useEffect(() => {
    if (reducido) { progreso.set(1); return undefined; }
    const c = animate(progreso, [0, 1], { delay: 2.4, duration: 14, ease: 'linear', repeat: Infinity, repeatDelay: 1.2 });
    return () => c.stop();
  }, [progreso, reducido]);
  const x = useTransform(progreso, (f) => px(puntoEn(puntos, largos, f))[0]);
  const y = useTransform(progreso, (f) => px(puntoEn(puntos, largos, f))[1]);
  const d = puntos.map((p, i) => `${i ? 'L' : 'M'}${px(p).join(',')}`).join('');
  const p1 = px([2.85, 0]);
  return (
    <svg viewBox="0 0 1000 470" style={{ width: '100%' }} role="img" aria-label="Recorrido de la demo">
      <g className="rejilla">
        {Array.from({ length: 9 }, (_, i) => <line key={i} x1={70 + i * ESC} x2={70 + i * ESC} y1="20" y2="450" stroke="var(--borde)" strokeDasharray="2 6" />)}
      </g>
      {Array.from({ length: 9 }, (_, i) => <text key={i} x={70 + i * ESC} y="466" textAnchor="middle" style={{ font: '13px var(--mono)', fill: 'var(--tenue)' }}>{i} m</text>)}
      {/* líneas de tiro desde P1 */}
      {[rivales[0], rivales[1]].map((r, i) => (
        <motion.line key={r.nombre} x1={p1[0]} y1={p1[1]} x2={px([r.x, r.y])[0]} y2={px([r.x, r.y])[1]} stroke="var(--rojo)" strokeDasharray="5 5" strokeWidth="1.5"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.8 + i * 0.2, duration: 0.5 }} />
      ))}
      <motion.path d={d} fill="none" stroke="var(--azul)" strokeWidth="4" strokeLinejoin="round"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.4, duration: 2, ease: 'easeInOut' }} />
      {ataques.map((k) => (
        <motion.path key={k} d={`M${px(puntos[k]).join(',')}L${px(puntos[k + 1]).join(',')}`} stroke="var(--naranja)" strokeWidth="9" strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 0.9 }} transition={{ delay: 2.2, duration: 0.6 }} />
      ))}
      {rivales.map((r, i) => {
        const [cx, cy] = px([r.x, r.y]);
        const mueve = r.hastaX != null;
        // Rótulo a la derecha si está abajo (no choca con el eje) y desplazado si hay una línea del recorrido cerca
        const [dx, dy, ancla] = r.y > 0 ? [26, 5, 'start'] : r.nombre.startsWith('Rival 3') ? [-14, -22, 'start'] : [0, -22, 'middle'];
        return (
          <motion.g key={r.nombre} initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.4 + i * 0.15, type: 'spring', stiffness: 300, damping: 15 }} style={{ transformBox: 'fill-box', transformOrigin: 'center' }}>
            <motion.g animate={mueve ? { x: [0, (r.hastaX - r.x) * ESC, 0] } : {}}
              transition={mueve ? { duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 2.4 } : {}}>
              <rect x={cx - 17} y={cy - 13} width="34" height="26" rx="5" fill={r.camuflado ? 'none' : 'var(--rojo)'} stroke="var(--rojo)" strokeWidth="2.5"
                strokeDasharray={r.camuflado ? '5 4' : undefined} />
              <text x={cx + dx} y={cy + dy} textAnchor={ancla} style={{ font: '600 15px var(--mono)', fill: 'var(--rojo)' }}>{r.nombre}</text>
            </motion.g>
          </motion.g>
        );
      })}
      {[[[0, 0], 'salida', 0, 24, 'middle'], [[2.85, 0], 'P1', 0, 30, 'middle'], [[8, -0.7], 'baile final', 4, -20, 'end']].map(([p, t, dx, dy, ancla]) => (
        <g key={t}>
          <circle cx={px(p)[0]} cy={px(p)[1]} r="6" fill="var(--texto)" />
          <text x={px(p)[0] + dx} y={px(p)[1] + dy} textAnchor={ancla} style={{ font: '600 15px var(--mono)', fill: 'var(--texto)' }}>{t}</text>
        </g>
      ))}
      {/* Leyenda: azul, desplazamientos; naranja, ataques sin parar */}
      <g style={{ font: '600 15px var(--mono)' }}>
        <line x1="80" x2="116" y1="372" y2="372" stroke="var(--azul)" strokeWidth="4" />
        <text x="126" y="377" style={{ fill: 'var(--suave)' }}>desplazamiento</text>
        <line x1="80" x2="116" y1="402" y2="402" stroke="var(--naranja)" strokeWidth="9" strokeLinecap="round" />
        <text x="126" y="407" style={{ fill: 'var(--suave)' }}>ataque sin parar</text>
      </g>
      <motion.g style={{ x, y }}>
        <rect x="-14" y="-11" width="28" height="22" rx="5" fill="var(--acento)" />
        <circle r="18" fill="none" stroke="var(--acento)" strokeOpacity="0.4" strokeWidth="2" />
      </motion.g>
    </svg>
  );
}
export function Circuito() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Circuito" titulo="El recorrido que tiene que hacer el robot" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.55fr 1fr', alignItems: 'start' }}>
        <div className="panel" style={{ padding: '14px 18px' }}><Mapa /></div>
        <Revela style={{ display: 'grid', gap: 14 }} retraso={0.8} paso={0.18}>
          <Item className="panel" style={{ padding: '18px 22px' }}>
            <div className="etiqueta">P1 · medido el 05/11</div>
            <p style={{ color: 'var(--texto)', marginTop: 6 }}>2,85 m a 0,5 m/s en unos 6 s. Torreta a 90°: rival 1; a −90°: el robot camuflado.</p>
          </Item>
          <Item className="panel" style={{ padding: '18px 22px' }}>
            <div className="etiqueta">R1 y R2 · ataques en marcha</div>
            <p style={{ color: 'var(--texto)', marginTop: 6 }}>Las ruedas mecanum retroceden y van de lado sin girar el chasis: 1,25 m hacia atrás disparando al rival 2, que se mueve, y 2 m hacia el rival 3, en alto.</p>
          </Item>
          <Item className="panel" style={{ padding: '18px 22px', borderColor: 'var(--acento-oscuro)' }}>
            <div className="etiqueta acento">Primer problema del laboratorio</div>
            <p style={{ marginTop: 6 }}>La orden por distancia del SDK sube cualquier velocidad menor de 0,5 a su mínimo interno: el robot iba a 0,06 m/s. Ahora se envían órdenes de velocidad 20 veces por segundo con la odometría, frena en los últimos 17 cm y para a 1 cm.</p>
          </Item>
        </Revela>
      </div>
    </div>
  );
}

// --- Puntería y el fallo de la cámara (fragmentos) -------------------------------------------------------
function Cola({ arreglado }) {
  const reducido = useReducedMotion();
  const [n, setN] = useState(0);
  useEffect(() => {
    if (reducido) { setN(64); return undefined; }
    setN(0);
    const id = setInterval(() => setN((v) => (v >= 64 ? 64 : v + 1)), 55);
    return () => clearInterval(id);
  }, [arreglado, reducido]);
  const [ultima, setUltima] = useState(0);
  useEffect(() => {
    if (!arreglado || reducido) return undefined;
    const id = setInterval(() => setUltima((v) => v + 1), 420);
    return () => clearInterval(id);
  }, [arreglado, reducido]);
  if (arreglado) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, alignItems: 'center' }}>
        <motion.div key={ultima} initial={{ scale: 0.9, opacity: 0.4 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.25 }}
          style={{ width: 150, height: 84, border: '3px solid var(--acento)', borderRadius: 3, display: 'grid', placeItems: 'center',
            background: 'var(--acento-oscuro)', font: '600 16px var(--mono)', color: 'var(--acento)' }}>
          imagen {ultima + 1}
        </motion.div>
        <div style={{ fontSize: 19, color: 'var(--suave)' }}>Un hilo lee el vídeo sin parar y guarda <b style={{ color: 'var(--texto)' }}>solo la última imagen</b>. Cada análisis espera a una tomada después del último giro, con la torreta quieta.</div>
      </div>
    );
  }
  const llena = n >= 64;
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(16, 1fr)', gap: 4 }}>
        {Array.from({ length: 64 }, (_, i) => (
          <div key={i} style={{ height: 22, borderRadius: 2, transition: 'background .2s, border-color .2s',
            background: i < n ? (llena ? 'rgba(255,133,133,0.55)' : `rgba(124,180,255,${0.25 + 0.6 * (i / 64)})`) : 'transparent',
            border: `1px solid ${i < n ? 'transparent' : 'var(--borde)'}` }} />
        ))}
      </div>
      <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 15, color: llena ? 'var(--rojo)' : 'var(--suave)' }}>
        <span>{llena ? '← el modelo lee esta: la más vieja' : 'el SDK guarda cada imagen en una cola…'}</span>
        <span>{n} / 64</span>
      </div>
      <motion.p initial={false} animate={{ opacity: llena ? 1 : 0.25 }} style={{ fontSize: 19, marginTop: 12, color: 'var(--suave)' }}>
        Mientras el modelo analiza o la torreta gira, nadie lee la cola: se llena, el decodificador se bloquea y llegan imágenes <b style={{ color: 'var(--rojo)' }}>viejas o corruptas</b>.
      </motion.p>
    </div>
  );
}
export function Punteria({ paso }) {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Puntería" titulo="Por qué veía al rival y no disparaba" />
      <div className="cuerpo dos-asim-inv" style={{ alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 12 }}>
          {['a) Rival detectado y centrado, confianza 1,00', 'b) La foto de un robot en su caja también es un robot', 'c) Imagen corrupta por la cola de vídeo llena'].map((t, i) => (
            <motion.div key={t} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.3, duration: 0.6, ease: CURVA }}
              style={{ display: 'grid', gridTemplateColumns: '230px 1fr', gap: 16, alignItems: 'center' }}>
              <Laboratorio i={i} />
              <span style={{ fontSize: 18, color: i === 2 ? 'var(--rojo)' : 'var(--suave)' }}>{t}</span>
            </motion.div>
          ))}
        </div>
        <div style={{ display: 'grid', gap: 18 }}>
          <div className="panel">
            <div className="etiqueta" style={{ marginBottom: 14, color: paso ? 'var(--acento)' : 'var(--rojo)' }}>{paso ? 'Arreglo' : 'Causa: el vídeo, no el modelo'}</div>
            <Cola arreglado={paso >= 1} />
          </div>
          <Paso paso={paso} desde={1} className="panel" style={{ padding: '18px 22px' }}>
            <b style={{ fontSize: 21 }}>Puntería por pasos</b>
            <p style={{ marginTop: 6, fontSize: 18 }}>Con cada imagen, la torreta gira lo que falta para centrar al rival (hasta cuatro correcciones) y dispara si el error es menor de 3° o del 30 % del ancho de la caja.</p>
          </Paso>
        </div>
      </div>
    </div>
  );
}

// --- Ataque en marcha: presupuesto de tiempo --------------------------------------------------------------
export function Marcha() {
  const total = PRESUPUESTO.reduce((a, b) => a + b.s, 0);
  const colores = ['var(--azul)', 'var(--acento)', '#c9a7ff', 'var(--rojo)'];
  let acumulado = 0;
  const VEL = 2.2;              // segundos de animación por cada segundo real ÷ VEL
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Ataque en marcha" titulo="Disparar sin detener el robot" />
      <div className="panel" style={{ padding: '26px 30px' }}>
        {/* El robot recorre el tramo al mismo ritmo que se llena la barra de tiempo */}
        <div style={{ position: 'relative', height: 78, marginBottom: 10 }}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 30, height: 2, background: 'var(--borde)' }} />
          <motion.div style={{ position: 'absolute', top: 14, width: 44, height: 34, marginLeft: -22, borderRadius: 6, background: 'var(--acento)' }}
            initial={{ left: '0%' }} animate={{ left: '100%' }} transition={{ delay: 0.8, duration: total / VEL, ease: 'linear' }} />
          <span className="mono" style={{ position: 'absolute', left: 0, top: 56, fontSize: 14, color: 'var(--tenue)' }}>retroceso de 1,25 m a 0,1 m/s: unos 12,5 s, sin parar el chasis</span>
          <span className="mono" style={{ position: 'absolute', right: 0, top: 56, fontSize: 14, color: 'var(--tenue)' }}>1,25 m después</span>
        </div>
        <div style={{ display: 'flex', height: 64, gap: 3 }}>
          {PRESUPUESTO.map((p, i) => {
            const inicio = acumulado;
            acumulado += p.s;
            return (
              <div key={p.que} style={{ flex: p.s, position: 'relative', background: 'var(--panel-2)', borderRadius: 2, overflow: 'hidden' }}>
                <motion.div style={{ position: 'absolute', inset: 0, background: colores[i], transformOrigin: 'left' }}
                  initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 0.8 + inicio / VEL, duration: p.s / VEL, ease: 'linear' }} />
                <span className="mono" style={{ position: 'absolute', left: 12, top: 20, fontSize: 18, fontWeight: 600, color: 'var(--fondo)', mixBlendMode: 'normal' }}>{fmt(p.s, 1)} s</span>
              </div>
            );
          })}
        </div>
        <div style={{ display: 'flex', gap: 3, marginTop: 8 }}>
          {PRESUPUESTO.map((p) => <div key={p.que} style={{ flex: p.s, fontSize: 17, color: 'var(--suave)' }}>{p.que}</div>)}
        </div>
      </div>
      <Revela style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, marginTop: 24 }} retraso={1.4} paso={0.18}>
        {[
          ['Imagen nítida', 'Se analiza la menos movida de las últimas.'],
          ['Velocidad prevista', 'La torreta sigue al rival y corrige con cada imagen.'],
          ['Rival en alto', 'La torreta lo busca inclinada 10°.'],
        ].map(([t, d]) => (
          <Item key={t} className="panel" style={{ padding: '18px 22px' }}><b style={{ fontSize: 23 }}>{t}</b><p style={{ fontSize: 21, marginTop: 6 }}>{d}</p></Item>
        ))}
      </Revela>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.4 }} style={{ margin: '18px 0 0', fontSize: 22 }}>
        Ráfagas de <span className="acento mono">20</span> disparos: se piden 12 impactos y 8 son de margen.
      </motion.p>
    </div>
  );
}

// --- Robot camuflado y aliados ------------------------------------------------------------------------
function ImagenDetectada({ src, alt, caja, conf, retraso, aliado }) {
  return (
    <div style={{ position: 'relative', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)', background: '#fff' }}>
      <img src={src} alt={alt} style={{ width: '100%', display: 'block' }} />
      <Caja caja={caja} rotulo="ROBOT" confianza={conf} retraso={retraso} tipo={aliado ? 'robot' : 'rival'} />
      {aliado && (
        <motion.span className="chip on" style={{ position: 'absolute', right: 10, bottom: 10 }}
          initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: retraso + 1.4, type: 'spring' }}>
          5,7 % verde → aliado
        </motion.span>
      )}
      {!aliado && (
        <motion.span className="chip" style={{ position: 'absolute', right: 10, bottom: 10, background: 'var(--rojo)', color: 'var(--fondo)', borderColor: 'var(--rojo)' }}
          initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: retraso + 1.4, type: 'spring' }}>
          0 % verde → dispara
        </motion.span>
      )}
    </div>
  );
}
export function Camuflaje() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Robot camuflado" titulo="Un disfraz no basta: el aliado se marca en verde" />
      <div className="cuerpo" style={{ gridTemplateColumns: '0.8fr 1.2fr', alignItems: 'start' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <ImagenDetectada src={detectiveJpg} alt="RoboMaster disfrazado de detective" caja={{ x: 0.07, y: 0.1, w: 0.86, h: 0.87 }} conf={0.99} retraso={0.6} />
          <ImagenDetectada src={aliadoJpg} alt="Robot aliado con bandera verde" caja={{ x: 0.06, y: 0.1, w: 0.88, h: 0.87 }} conf={0.99} retraso={0.9} aliado />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.6 }} style={{ gridColumn: '1 / -1', margin: '6px 0 0', fontSize: 18, color: 'var(--suave)' }}>
            El robot disfrazado de detective y los cuatro aliados generados con IA salen como robot con más del 92 %. Solo baja al 52 % tapando ruedas, cañón y chasis a la vez.
          </motion.p>
        </div>
        <div style={{ display: 'grid', gap: 18 }}>
          <div className="panel" style={{ padding: '20px 24px 42px' }}>
            <div className="etiqueta" style={{ marginBottom: 12 }}>Verde intenso dentro de la caja</div>
            <div style={{ position: 'relative' }}>
              <BarrasH anchoEtiqueta={150} max={14} dec={1} retraso={1} paso={0.12} alto={30}
                datos={CAMUFLAJE.map((c) => ({ etiqueta: c.imagen, valor: Math.max(c.verde, 0.0001), texto: `${fmt(c.verde, 1)} %`,
                  destacado: true, color: c.verde > 2 ? 'var(--acento)' : 'var(--rojo)' }))} />
              <motion.div initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: 1.9, duration: 0.4 }}
                style={{ position: 'absolute', top: -6, bottom: -6, left: `calc(168px + (100% - 168px) * ${2 / 14})`, borderLeft: '2px dashed var(--texto)', transformOrigin: 'top' }}>
                <span className="mono" style={{ position: 'absolute', bottom: -26, left: -44, fontSize: 14, whiteSpace: 'nowrap' }}>2 % = aliado</span>
              </motion.div>
            </div>
          </div>
          <motion.div className="panel" style={{ padding: '18px 22px' }} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2.2 }}>
            <div className="etiqueta" style={{ marginBottom: 10 }}>Impreso o en pantalla, delante de una webcam</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr 1fr auto', rowGap: 6, columnGap: 14, fontSize: 18 }}>
              {SOPORTES.map((s, i) => [
                <span key={`a${i}`} className="suave">{s.soporte}</span>, <span key={`b${i}`} className="suave">{s.tam}</span>,
                <span key={`c${i}`} className="mono">{s.conf}</span>,
                <span key={`d${i}`} className="mono" style={{ color: s.dispara ? 'var(--acento)' : s.dispara === false ? 'var(--rojo)' : 'var(--naranja)' }}>
                  {s.dispara ? 'dispara' : s.dispara === false ? 'no' : 'solo pegado'}
                </span>,
              ])}
            </div>
            <p style={{ marginTop: 10, fontSize: 17 }}>En la tableta el brillo y los reflejos lo estropean: para la demo, papel mate en A3.</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

// --- Mando ------------------------------------------------------------------------------------------
export function Mando() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Control manual" titulo="Mover el robot a mano desde el navegador" />
      <div className="cuerpo dos-asim" style={{ alignItems: 'start' }}>
        <div style={{ position: 'relative', borderRadius: 6, overflow: 'hidden', border: '1px solid var(--borde)' }}>
          <motion.img src={mandoJpg} alt="Interfaz del mando con un robot detectado al 99,9 %" style={{ width: '100%', display: 'block' }}
            initial={{ scale: 1.25, x: '6%', y: '4%', filter: 'blur(6px)' }} animate={{ scale: 1, x: '0%', y: '0%', filter: 'blur(0px)' }}
            transition={{ delay: 0.2, duration: 1.6, ease: CURVA }} />
          <motion.div style={{ position: 'absolute', left: '44.5%', top: '42%', width: '15%', height: '22%', border: '2px solid var(--acento)', boxShadow: '0 0 0 9999px rgba(0,0,0,0.35)' }}
            initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ delay: 1.9, duration: 2.4, times: [0, 0.15, 0.8, 1] }} />
        </div>
        <div style={{ display: 'grid', gap: 18 }}>
          <div className="panel" style={{ padding: '20px 24px' }}>
            <div className="etiqueta" style={{ marginBottom: 12 }}>Imágenes por segundo: aquí el detector sí usa la GPU</div>
            <BarrasH anchoEtiqueta={190} max={32} dec={1} retraso={0.8} paso={0.18} alto={30}
              datos={[
                { etiqueta: 'CPU del laboratorio', valor: 1 / 2.3, texto: '0,4' },
                { etiqueta: 'CPU de 32 hilos', valor: 1 / 1.1, texto: '0,9' },
                { etiqueta: 'GPU · FRCNN v2', valor: 1 / 0.094, texto: '10,6 · 94 ms', destacado: true },
                { etiqueta: 'GPU · MobileNet', valor: 1 / 0.032, texto: '≈ 31 · 32 ms', destacado: true, color: 'var(--azul)' },
              ]} />
          </div>
          <Revela as="ul" className="lista" retraso={1.8} paso={0.14} style={{ fontSize: 22 }}>
            <Item as="li"><span><b>Uso:</b> colocar el robot, probar el detector y hacer una demo libre</span></Item>
            <Item as="li"><span><b>Teclado, ratón o mando de PS4</b></span></Item>
            <Item as="li"><span><b>Seguro:</b> sin órdenes, se para</span></Item>
            <Item as="li"><span><b>Disparo automático</b> opcional</span></Item>
            <Item as="li"><span><b><Contador valor={31} retraso={2.4} /> pruebas automáticas</b></span></Item>
          </Revela>
        </div>
      </div>
    </div>
  );
}

// --- Estado ----------------------------------------------------------------------------------------
function Marca({ hecho, retraso }) {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden style={{ flex: 'none' }}>
      <motion.circle cx="13" cy="13" r="11" fill="none" stroke={hecho ? 'var(--acento)' : 'var(--tenue)'} strokeWidth="2"
        strokeDasharray={hecho ? undefined : '3 4'} initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: retraso, duration: 0.4 }} />
      {hecho && <motion.path d="M7.5 13.5l3.6 3.6 7.4-7.6" fill="none" stroke="var(--acento)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: retraso + 0.3, duration: 0.3 }} />}
    </svg>
  );
}
const HECHO = [
  'Conexión, recta de 2,85 m en 6 s y detección del rival en P1 (0,96–1,00)',
  'Cámara corregida: solo la última imagen, tomada tras el último giro',
  'Demo completa con el robot simulado e imágenes de test',
  'Ataques en marcha, rival en alto y baile final, en simulación',
  'Robot camuflado probado en papel y en tableta',
  'Mando con detector en GPU y 31 pruebas automáticas',
  'Cada ejecución guarda imágenes, cajas, ángulos y tiempos',
];
const PENDIENTE = [
  'Disparar en el laboratorio con la cámara corregida',
  'Montar R1 y R2 y medir sus tiempos reales',
  'Ataque en marcha con el rival 2 moviéndose',
  'Contar los impactos que registra cada rival',
  'Robot camuflado desde P1 con la cámara del robot',
];
export function Estado() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Estado" titulo="Qué ya funciona y qué falta probar en el laboratorio" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        {[[HECHO, true, 'Hecho'], [PENDIENTE, false, 'Pendiente']].map(([lista, hecho, t], col) => (
          <div key={t} className="panel">
            <div className="etiqueta" style={{ marginBottom: 16, color: hecho ? 'var(--acento)' : 'var(--suave)' }}>{t}</div>
            <div style={{ display: 'grid', gap: 16 }}>
              {lista.map((l, i) => (
                <motion.div key={l} style={{ display: 'flex', gap: 14, alignItems: 'start', fontSize: 20, color: hecho ? 'var(--texto)' : 'var(--suave)' }}
                  initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + col * 0.9 + i * 0.15 }}>
                  <Marca hecho={hecho} retraso={0.5 + col * 0.9 + i * 0.15} />{l}
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
