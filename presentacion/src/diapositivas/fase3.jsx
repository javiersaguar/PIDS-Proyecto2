import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Revela } from '../componentes/base.jsx';
import { BarrasH } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { CIRCUITO, PRESUPUESTO } from '../datos/cifras.js';
import laboratorioJpg from '@repo/docs/informes/figuras/bloque3/laboratorio.jpg';
import mandoJpg from '@repo/docs/informes/figuras/bloque3/mando.jpg';
import circuitoPng from '@repo/docs/informes/figuras/circuito_demo.png';
import tunelJpg from '@repo/docs/informes/figuras/bloque3/demo_clase/1_tunel.jpg';
import rival1Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/2_rival1.jpg';
import camufladoJpg from '@repo/docs/informes/figuras/bloque3/demo_clase/3_camuflado.jpg';
import rival2Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/4_rival2_movimiento.jpg';
import rival3Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/5_rival3_escondido.jpg';
import baileJpg from '@repo/docs/informes/figuras/bloque3/demo_clase/6_baile.jpg';
import humoJpg from '@repo/docs/informes/figuras/bloque3/profesor/1_foto_humo.jpg';
import tapadoJpg from '@repo/docs/informes/figuras/bloque3/profesor/2_robot_tapado.jpg';
import profeRival2Jpg from '@repo/docs/informes/figuras/bloque3/profesor/3_rival2.jpg';
import distintoJpg from '@repo/docs/informes/figuras/bloque3/profesor/4_robot_distinto.jpg';
import disparoJpg from '@repo/docs/informes/figuras/interfaz/v1_deteccion_lejana_disparo.jpg';
import dosRobotsJpg from '@repo/docs/informes/figuras/interfaz/v2_dos_robots.jpg';
import trasCajaJpg from '@repo/docs/informes/figuras/interfaz/v1_deteccion_tras_caja.jpg';
import wakaJpg from '@repo/docs/informes/figuras/interfaz/v2_emote_waka_dos_robots.jpg';

// --- Separador ---------------------------------------------------------------------------------
export function Seccion3() {
  return (
    <Seccion numero="03" titulo="Robot" color="var(--rojo)" fotos={[laboratorioJpg, mandoJpg, circuitoPng]}
      lema="Llevamos el detector al RoboMaster: recorrer el circuito, encontrar a los rivales y dispararles."
      puntos={['circuito por tramos', 'ataque en marcha', 'control manual']} />
  );
}

// --- El circuito ------------------------------------------------------------------------------------
// Animación de la demo sobre el plano de la Figura B3.1. El tiempo va comprimido (la demo real dura
// casi dos minutos), pero respeta el orden: dónde avanza, dónde se para, dónde va despacio y a quién dispara.
const ESC = 102;   // el recorrido llega a 8,78 m: 70 + 8,78 × 102 cabe en los 1000 del dibujo
const px = ([x, y]) => [70 + x * ESC, 40 + (y + 2.4) * ESC];
function longitudes(puntos) {
  const tramos = puntos.slice(1).map((p, i) => Math.hypot(p[0] - puntos[i][0], p[1] - puntos[i][1]));
  return { tramos, total: tramos.reduce((a, b) => a + b, 0) };
}
const lerp = (a, b, f) => a + (b - a) * f;
const suave = (f) => f * f * (3 - 2 * f);
const tramoDe = (f, a, b) => Math.min(1, Math.max(0, (f - a) / (b - a)));
// Interpola ángulos por el camino más corto
function lerpAng(a, b, f) {
  const d = ((b - a + 540) % 360) - 180;
  return a + d * f;
}

// Guion de la demo: cada paso dura `dur` segundos de animación
const DISPAROS = 20;
const GUION = (() => {
  const g = [];
  const mover = (i, dur, vel, ataque) => g.push({ tipo: 'mover', i, dur, vel, ataque });
  const parada = (obj) => g.push({ tipo: 'apuntar', obj, dur: 1 }, { tipo: 'ver', obj, dur: 1.1 }, { tipo: 'disparar', obj, dur: 2.4 });
  mover(0, 3, 0.5);
  parada(0);
  parada(1);
  mover(1, 2.4, 0.4);
  mover(2, 1.2, 0.5);
  mover(3, 8.5, 0.1, 2);
  mover(4, 1.2, 0.5);
  mover(5, 2.4, 0.5);
  mover(6, 1, 0.5);
  mover(7, 8.5, 0.1, 3);
  g.push({ tipo: 'baile', dur: 3.6 }, { tipo: 'fin', dur: 1.6 });
  let t = 0;
  for (const p of g) { p.desde = t; t += p.dur; }
  return { pasos: g, total: t };
})();
// Dentro de un ataque en marcha: girar, ver, ráfaga
const MARCHA = { ver: 0.18, disparo: 0.34, fin: 0.9 };

function posicion(p, f) {
  const { puntos } = CIRCUITO;
  if (p.tipo !== 'mover') return null;
  const a = puntos[p.i];
  const b = puntos[p.i + 1];
  // Arranca y frena en los extremos de cada tramo
  const g = p.ataque != null ? f : suave(f);
  return [lerp(a[0], b[0], g), lerp(a[1], b[1], g)];
}
function rivalEn(k, t) {
  const r = CIRCUITO.rivales[k];
  if (r.hastaX == null) return [r.x, r.y];
  const p = GUION.pasos.find((q) => q.ataque === k);
  const f = tramoDe(t, p.desde, p.desde + p.dur);
  return [lerp(r.x, r.hastaX, f), r.y];
}
const angA = (de, a) => (Math.atan2(a[1] - de[1], a[0] - de[0]) * 180) / Math.PI;

// Estado de la demo en el instante t
function estado(t) {
  const { puntos } = CIRCUITO;
  let pos = puntos[0];
  let ang = 0;
  const eliminados = new Set();
  for (const p of GUION.pasos) {
    const f = Math.min(1, Math.max(0, (t - p.desde) / p.dur));
    const actual = t < p.desde + p.dur;
    const e = { pos, ang, modo: 'avanza', vel: 0, objetivo: null, viendo: false, disparo: null, paso: p, eliminados };
    if (p.tipo === 'mover') {
      pos = posicion(p, f);
      e.pos = pos;
      e.vel = p.vel;
      if (p.ataque != null) {
        const blanco = rivalEn(p.ataque, t);
        const fin = angA(pos, blanco);
        e.modo = 'marcha';
        e.objetivo = p.ataque;
        if (f < MARCHA.ver) ang = lerpAng(e.ang, fin, suave(f / MARCHA.ver));
        else ang = fin;
        e.viendo = f >= MARCHA.ver && f < MARCHA.disparo;
        if (f >= MARCHA.disparo && f < MARCHA.fin) e.disparo = (f - MARCHA.disparo) / (MARCHA.fin - MARCHA.disparo);
        if (f >= MARCHA.fin) { eliminados.add(p.ataque); e.objetivo = null; }
      } else {
        // Sin objetivo, la torreta vuelve al frente durante el primer tercio del tramo
        ang = lerpAng(e.ang, 0, suave(tramoDe(f, 0, 0.35)));
      }
    } else if (p.tipo === 'apuntar' || p.tipo === 'ver' || p.tipo === 'disparar') {
      const fin = angA(pos, rivalEn(p.obj, t));
      ang = p.tipo === 'apuntar' ? lerpAng(e.ang, fin, suave(f)) : fin;
      e.modo = 'parada';
      e.objetivo = p.obj;
      e.viendo = p.tipo === 'ver';
      if (p.tipo === 'disparar') {
        e.disparo = f;
        if (f >= 1) eliminados.add(p.obj);
      }
    } else if (p.tipo === 'baile') {
      e.modo = 'baile';
      ang = lerpAng(e.ang, 0, 1) + Math.sin(f * Math.PI * 6) * 60;
      e.pos = [pos[0] + Math.sin(f * Math.PI * 4) * 0.12, pos[1] + Math.sin(f * Math.PI * 8) * 0.08];
    } else {
      e.modo = 'fin';
    }
    e.ang = ang;
    if (actual) return e;
  }
  return { pos, ang, modo: 'fin', vel: 0, objetivo: null, eliminados, paso: GUION.pasos[GUION.pasos.length - 1] };
}

function useReloj(activo) {
  const reducido = useReducedMotion();
  const [t, setT] = useState(reducido ? GUION.total - 0.01 : 0);
  useEffect(() => {
    if (reducido || !activo) return undefined;
    let id;
    const inicio = performance.now() + 1200;
    const bucle = (ahora) => {
      setT(Math.max(0, ((ahora - inicio) / 1000)) % GUION.total);
      id = requestAnimationFrame(bucle);
    };
    id = requestAnimationFrame(bucle);
    return () => cancelAnimationFrame(id);
  }, [reducido, activo]);
  return t;
}

const MODOS = {
  avanza: { texto: 'AVANZA', color: 'var(--azul)' },
  parada: { texto: 'PARADO · BUSCA Y DISPARA', color: 'var(--rojo)' },
  marcha: { texto: 'DESPACIO · DISPARA SIN PARAR', color: 'var(--naranja)' },
  baile: { texto: 'BAILE FINAL', color: 'var(--acento)' },
  fin: { texto: 'FIN DE LA DEMO', color: 'var(--suave)' },
};
// Color de los LED del robot, como en la demo: ámbar buscando, rojo al disparar y verde tras eliminar
function colorLed(e, t) {
  if (e.modo === 'baile') return `hsl(${(t * 600) % 360} 85% 65%)`;
  if (e.disparo != null) return Math.floor(t * 8) % 2 ? 'var(--rojo)' : '#ffd0d0';
  if (e.objetivo != null) return '#ffc24a';
  return 'var(--acento)';
}

// Dónde va el nombre de cada rival y los datos de la detección, para no pisar el recorrido
const ROTULOS = [
  { nombre: [[26, 5, 'start', 'Rival 1']], datos: [-32, -6, 'end'] },
  { nombre: [[0, -24, 'middle', 'Camuflado']], datos: [-32, -4, 'end'] },
  { nombre: [[0, -24, 'middle', 'Rival 2']], datos: [32, -4, 'start'] },
  { nombre: [[0, 42, 'middle', 'Rival 3'], [0, 60, 'middle', 'escondido']], datos: [0, -48, 'middle'] },
];

function Mapa({ e, t }) {
  const { puntos, ataques, rivales } = CIRCUITO;
  const d = puntos.map((p, i) => `${i ? 'L' : 'M'}${px(p).join(',')}`).join('');
  const [rx, ry] = px(e.pos);
  const led = colorLed(e, t);
  const modo = MODOS[e.modo];
  const blanco = e.objetivo != null ? px(rivalEn(e.objetivo, t)) : null;
  const rad = (e.ang * Math.PI) / 180;
  const boca = [rx + Math.cos(rad) * 24, ry + Math.sin(rad) * 24];
  // Ráfaga: proyectiles en vuelo entre el cañón y el blanco
  const balas = [];
  if (e.disparo != null && blanco) {
    const fase = e.disparo * DISPAROS;
    for (let j = 0; j < 4; j += 1) {
      const f = (fase + j / 4) % 1;
      balas.push([lerp(boca[0], blanco[0], f), lerp(boca[1], blanco[1], f), f]);
    }
  }
  const impactos = e.disparo != null ? Math.min(DISPAROS, Math.floor(e.disparo * DISPAROS) + 1) : 0;
  const destello = e.disparo != null && (e.disparo * DISPAROS) % 1 < 0.35;
  return (
    <svg viewBox="0 0 1000 470" style={{ width: '100%', display: 'block' }} role="img"
      aria-label="Animación del recorrido: el robot avanza, se para en P1 para disparar a dos objetivos, retrocede despacio disparando al rival 2 y acaba disparando hacia atrás al rival 3">
      {Array.from({ length: 9 }, (_, i) => (
        <g key={i}>
          <line x1={70 + i * ESC} x2={70 + i * ESC} y1="20" y2="450" stroke="var(--borde)" strokeDasharray="2 6" />
          <text x={70 + i * ESC} y="466" textAnchor="middle" style={{ font: '13px var(--mono)', fill: 'var(--tenue)' }}>{i} m</text>
        </g>
      ))}
      <path d={d} fill="none" stroke="var(--azul)" strokeWidth="4" strokeLinejoin="round" opacity="0.85" />
      {ataques.map((k) => (
        <path key={k} d={`M${px(puntos[k]).join(',')}L${px(puntos[k + 1]).join(',')}`} stroke="var(--naranja)" strokeWidth="9" strokeLinecap="round" opacity="0.9" />
      ))}
      {/* Parada en P1 */}
      <g transform={`translate(${px([2.85, 0]).join(',')})`}>
        <polygon points="-9,-22 9,-22 22,-9 22,9 9,22 -9,22 -22,9 -22,-9" fill="none" stroke="var(--rojo)" strokeWidth="2.5" opacity="0.8" />
        <text y="44" textAnchor="middle" style={{ font: '600 15px var(--mono)', fill: 'var(--texto)' }}>P1 · parada</text>
      </g>
      {[[[0, 0], 'salida', 0, 30, 'middle'], [[8.78, -0.7], 'baile final', 4, 32, 'end']].map(([p, txt, dx, dy, ancla]) => (
        <g key={txt}>
          <circle cx={px(p)[0]} cy={px(p)[1]} r="6" fill="var(--texto)" />
          <text x={px(p)[0] + dx} y={px(p)[1] + dy} textAnchor={ancla} style={{ font: '600 15px var(--mono)', fill: 'var(--texto)' }}>{txt}</text>
        </g>
      ))}
      {/* Caja del rival 3 */}
      {(() => { const [cx, cy] = px([rivales[3].x, rivales[3].y]); return <rect x={cx - 26} y={cy - 22} width="52" height="44" rx="4" fill="var(--panel-2)" stroke="var(--borde)" />; })()}
      {/* Campo de visión de la cámara de la torreta */}
      <path d={`M${rx},${ry} L${rx + Math.cos(rad - 0.55) * 150},${ry + Math.sin(rad - 0.55) * 150} A150,150 0 0 1 ${rx + Math.cos(rad + 0.55) * 150},${ry + Math.sin(rad + 0.55) * 150} Z`}
        fill="var(--acento)" opacity={e.modo === 'baile' || e.modo === 'fin' ? 0 : e.viendo ? 0.22 : 0.07} />
      {rivales.map((r, k) => {
        const [cx, cy] = px(rivalEn(k, t));
        const fuera = e.eliminados.has(k);
        const atacado = e.objetivo === k;
        const rot = ROTULOS[k];
        return (
          <g key={r.nombre} opacity={fuera ? 0.45 : 1}>
            {atacado && destello && <circle cx={cx} cy={cy} r="26" fill="var(--rojo)" opacity="0.35" />}
            <rect x={cx - 17} y={cy - 13} width="34" height="26" rx="5" fill={r.camuflado ? 'none' : 'var(--rojo)'} stroke="var(--rojo)" strokeWidth="2.5"
              strokeDasharray={r.camuflado ? '5 4' : undefined} />
            {fuera && <path d={`M${cx - 12},${cy - 9}L${cx + 12},${cy + 9}M${cx + 12},${cy - 9}L${cx - 12},${cy + 9}`} stroke="var(--texto)" strokeWidth="3" />}
            {rot.nombre.map(([dx, dy, ancla, txt]) => (
              <text key={txt} x={cx + dx} y={cy + dy} textAnchor={ancla} style={{ font: '600 15px var(--mono)', fill: 'var(--rojo)' }}>{txt}</text>
            ))}
            {/* Caja de detección al verlo y contador de la ráfaga */}
            {atacado && (e.viendo || e.disparo != null) && (
              <g style={{ font: '600 13px var(--mono)' }} textAnchor={rot.datos[2]}>
                <rect x={cx - 25} y={cy - 21} width="50" height="42" fill="none" stroke="var(--acento)" strokeWidth="2" />
                <text x={cx + rot.datos[0]} y={cy + rot.datos[1]} style={{ fill: 'var(--acento)' }}>robot 0,99</text>
                {e.disparo != null && (
                  <text x={cx + rot.datos[0]} y={cy + rot.datos[1] + 16} style={{ fill: 'var(--texto)' }}>impactos {impactos}/{DISPAROS}</text>
                )}
              </g>
            )}
          </g>
        );
      })}
      {balas.map(([bx, by, f], j) => <circle key={j} cx={bx} cy={by} r="4" fill="var(--rojo)" opacity={1 - f * 0.4} />)}
      {/* Robot: chasis con el color de los LED y torreta girada hacia el blanco */}
      <g transform={`translate(${rx},${ry})`}>
        {e.viendo && <text y="-30" textAnchor="middle" style={{ font: '700 14px var(--mono)', fill: '#ffc24a' }}>«Enemy spotted»</text>}
        <rect x="-16" y="-13" width="32" height="26" rx="5" fill={led} />
        <g transform={`rotate(${e.ang})`}>
          <circle r="8" fill="var(--fondo)" />
          <rect x="4" y="-3" width="20" height="6" rx="2" fill="var(--fondo)" />
        </g>
        {e.disparo != null && destello && <circle cx={boca[0] - rx} cy={boca[1] - ry} r="7" fill="#fff3c4" />}
      </g>
      {e.modo === 'baile' && [0, 1, 2].map((j) => (
        <text key={j} x={rx - 30 + j * 30} y={ry - 30 - ((t * 60 + j * 20) % 40)} style={{ font: '700 20px var(--mono)', fill: led }}>♪</text>
      ))}
      {/* Estado actual */}
      <g transform="translate(80,18)">
        <rect width="380" height="76" rx="6" fill="var(--panel-2)" stroke={modo.color} strokeWidth="1.5" />
        <text x="16" y="30" style={{ font: '700 17px var(--mono)', fill: modo.color }}>{modo.texto}</text>
        <text x="16" y="58" style={{ font: '600 15px var(--mono)', fill: 'var(--suave)' }}>
          {e.paso.tipo === 'mover' ? `${fmt(e.vel, 1)} m/s` : '0 m/s'}
        </text>
        <rect x="100" y="48" width="260" height="10" rx="5" fill="var(--borde)" />
        <rect x="100" y="48" width={260 * (e.paso.tipo === 'mover' ? e.vel / 0.5 : 0)} height="10" rx="5" fill={modo.color} />
      </g>
      {/* Leyenda */}
      <g style={{ font: '600 15px var(--mono)' }}>
        <line x1="620" x2="656" y1="380" y2="380" stroke="var(--azul)" strokeWidth="4" />
        <text x="666" y="385" style={{ fill: 'var(--suave)' }}>avanza deprisa</text>
        <line x1="620" x2="656" y1="408" y2="408" stroke="var(--naranja)" strokeWidth="9" strokeLinecap="round" />
        <text x="666" y="413" style={{ fill: 'var(--suave)' }}>despacio, disparando</text>
      </g>
    </svg>
  );
}

const ETAPAS = [
  { modo: 'parada', etiqueta: 'P1 · se para', texto: 'Tras 2,85 m a 0,5 m/s se detiene, gira la torreta a la derecha contra el rival 1 y a la izquierda contra el robot camuflado: 20 disparos a cada uno.' },
  { modo: 'marcha', ataque: 2, etiqueta: 'R1 · retrocede a 0,1 m/s', texto: 'Recorre 1,44 m marcha atrás sin pararse mientras sigue y dispara al rival 2, que también avanza.' },
  { modo: 'marcha', ataque: 3, etiqueta: 'R2 · avanza a 0,1 m/s', texto: 'En los 2,3 m finales gira la torreta hacia atrás para alcanzar al rival 3, escondido detrás.' },
  { modo: 'baile', etiqueta: 'Final', texto: 'Baile con música y los LED cambiando de color.' },
];
function etapaActiva(e) {
  if (e.modo === 'parada') return 0;
  if (e.modo === 'marcha') return e.objetivo === 3 || e.paso.ataque === 3 ? 2 : 1;
  if (e.modo === 'baile') return 3;
  return -1;
}

export function Circuito() {
  const t = useReloj(true);
  const e = estado(t);
  const activa = etapaActiva(e);
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Circuito" titulo="Dónde se para, dónde va despacio y a quién dispara" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.6fr 1fr', alignItems: 'start' }}>
        <div className="panel" style={{ padding: '14px 18px' }}><Mapa e={e} t={t} /></div>
        <Revela style={{ display: 'grid', gap: 12 }} retraso={0.5} paso={0.14}>
          {ETAPAS.map((s, i) => (
            <Item key={s.etiqueta} className="panel" style={{ padding: '16px 20px', transition: 'border-color 0.3s, background 0.3s',
              borderColor: i === activa ? MODOS[s.modo].color : undefined, background: i === activa ? 'var(--panel-2)' : undefined }}>
              <div className="etiqueta" style={{ color: i === activa ? MODOS[s.modo].color : undefined }}>{s.etiqueta}</div>
              <p style={{ color: 'var(--texto)', marginTop: 6, fontSize: 20 }}>{s.texto}</p>
            </Item>
          ))}
        </Revela>
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
          <span className="mono" style={{ position: 'absolute', left: 0, top: 56, fontSize: 14, color: 'var(--tenue)' }}>retroceso de 1,44 m a 0,1 m/s: unos 14,5 s, sin parar el chasis</span>
          <span className="mono" style={{ position: 'absolute', right: 0, top: 56, fontSize: 14, color: 'var(--tenue)' }}>1,44 m después</span>
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
          ['Imagen nítida', 'Como el robot se mueve, de las últimas imágenes analizamos la menos borrosa.'],
          ['Seguir al rival', 'La torreta gira a la velocidad prevista del rival y se corrige con cada imagen.'],
          ['Rival en alto', 'La torreta apunta 10° hacia arriba para encontrarlo.'],
        ].map(([t, d]) => (
          <Item key={t} className="panel" style={{ padding: '18px 22px' }}><b style={{ fontSize: 23 }}>{t}</b><p style={{ fontSize: 21, marginTop: 6 }}>{d}</p></Item>
        ))}
      </Revela>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.4 }} style={{ margin: '18px 0 0', fontSize: 22 }}>
        Cada ráfaga son <span className="acento mono">20</span> disparos: el enunciado pide 12 impactos y dejamos 8 de margen por si alguno no se registra.
      </motion.p>
    </div>
  );
}

// --- La demo oficial en clase, fase a fase -------------------------------------------------------------------
// Cámara del robot en la demo en clase del 12/11 (evidencias/20261112_155726). El túnel y el baile salen de las
// fotos de todo el recorrido (FOTOS_RECORRIDO); el resto, de las imágenes analizadas.
const FASES_DEMO = [
  { n: '01', titulo: 'Túnel', texto: 'Recta de 2,85 m entre las sillas a 0,5 m/s', foto: tunelJpg, color: 'var(--azul)' },
  { n: '02', titulo: 'Rival 1', texto: 'P1, torreta a la derecha · 1,00 · 20 disparos', foto: rival1Jpg, color: 'var(--rojo)' },
  { n: '03', titulo: 'Señuelo camuflado', texto: 'P1, torreta a la izquierda · 0,99 · 20 disparos', foto: camufladoJpg, color: 'var(--rojo)' },
  { n: '04', titulo: 'Rival 2 en movimiento', texto: 'R1, los dos en marcha · 1,00 · 20 disparos', foto: rival2Jpg, color: 'var(--naranja)' },
  { n: '05', titulo: 'Rival 3 escondido', texto: 'R2, torreta girada 180º, en una caja · 1,00 · 20 disparos', foto: rival3Jpg, color: 'var(--naranja)' },
  { n: '06', titulo: 'Baile final', texto: 'Super Estrella, con la clase mirando', foto: baileJpg, color: 'var(--acento)' },
];
function Mosaico({ fotos, columnas }) {
  return (
    <Revela style={{ display: 'grid', gridTemplateColumns: `repeat(${columnas}, 1fr)`, gap: 18 }} retraso={0.3} paso={0.16}>
      {fotos.map((f) => (
        <Item key={f.titulo} style={{ position: 'relative', aspectRatio: '16 / 9', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)' }}>
          <img src={f.foto} alt={`${f.titulo}: ${f.texto}`} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          <div className="mono" style={{ position: 'absolute', left: 0, top: 0, padding: '6px 12px', background: f.color, color: 'var(--fondo)', fontSize: 16, fontWeight: 700 }}>
            {f.n} · {f.titulo.toUpperCase()}
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: '22px 14px 9px', fontSize: 17,
            background: 'linear-gradient(transparent, rgba(0,0,0,0.85))', color: '#fff' }}>{f.texto}</div>
        </Item>
      ))}
    </Revela>
  );
}
export function DemoReal() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Demo en clase" titulo="La demo oficial, fase a fase" />
      <Mosaico fotos={FASES_DEMO} columnas={3} />
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }} style={{ margin: '16px 0 0', fontSize: 19, color: 'var(--tenue)' }}>
        Cámara del robot el 12/11, con el detector en la GPU. Los cuatro rivales registraron los 80 disparos.
      </motion.p>
    </div>
  );
}

// --- El intento sorpresa del profesor ----------------------------------------------------------------------
// evidencias/20261112_160426: imágenes del profesor, robots tapados y un robot distinto en la recta final.
const SORPRESA = [
  { n: 'P1', titulo: 'Foto entre humo', texto: '0,59: por debajo del umbral, no dispara', foto: humoJpg, color: 'var(--naranja)' },
  { n: 'P1', titulo: 'Robot tapado', texto: 'Con una tela: 0,85 a 0,91, no dispara', foto: tapadoJpg, color: 'var(--naranja)' },
  { n: 'R1', titulo: 'Rival 2', texto: '1,00: lo sigue y le dispara', foto: profeRival2Jpg, color: 'var(--acento)' },
  { n: 'R2', titulo: 'Robot distinto', texto: 'Otro modelo, con partes rojas: 0,99, le dispara', foto: distintoJpg, color: 'var(--acento)' },
];
export function Sorpresa() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Prueba sorpresa" titulo="El profesor cambió los robots" />
      <div className="cuerpo" style={{ gridTemplateColumns: '2.3fr 1fr', alignItems: 'start', gap: 28 }}>
        <Mosaico fotos={SORPRESA} columnas={2} />
        <Revela as="ul" className="lista" retraso={1.2} paso={0.16} style={{ fontSize: 22 }}>
          <Item as="li"><span><b>Generaliza:</b> detecta y ataca a un robot que no estaba en nuestros datos</span></Item>
          <Item as="li"><span><b>No se deja engañar:</b> un robot tapado o una foto borrosa no llegan al umbral de 0,95</span></Item>
          <Item as="li"><span><b>El precio:</b> esos dos robots se quedan sin disparar; el umbral prioriza no atacar a lo que no es un robot</span></Item>
        </Revela>
      </div>
    </div>
  );
}

// --- El mando con el robot real ---------------------------------------------------------------------------
const CAPTURAS_MANDO = [
  { foto: disparoJpg, texto: 'Rival lejano bajo una mesa, con el aviso de disparo' },
  { foto: dosRobotsJpg, texto: 'Dos robots detectados a la vez' },
  { foto: trasCajaJpg, texto: 'Robot detrás de una caja; el radar marca hacia dónde mira la torreta' },
  { foto: wakaJpg, texto: 'Baile «Waka waka» lanzado desde el mando' },
];
export function MandoReal() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Control manual" titulo="La interfaz con el robot real" />
      <div className="cuerpo" style={{ gridTemplateColumns: '2.5fr 0.9fr', alignItems: 'start', gap: 28 }}>
        <Revela style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }} retraso={0.3} paso={0.16}>
          {CAPTURAS_MANDO.map((c) => (
            <Item key={c.texto} style={{ position: 'relative', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)', aspectRatio: '16 / 9' }}>
              <img src={c.foto} alt={c.texto} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
              <div style={{ position: 'absolute', left: 0, right: 0, top: 0, padding: '8px 12px 20px', fontSize: 16,
                background: 'linear-gradient(rgba(0,0,0,0.85), transparent)', color: '#fff' }}>{c.texto}</div>
            </Item>
          ))}
        </Revela>
        <Revela as="ul" className="lista" retraso={1.2} paso={0.14} style={{ fontSize: 21 }}>
          <Item as="li"><span><b>11/11</b>, en el suelo del laboratorio con el mando de PS4</span></Item>
          <Item as="li"><span><b>Vídeo</b> a 8–16 imágenes por segundo</span></Item>
          <Item as="li"><span><b>Confianza</b> de 0,97 a 1,00, también con varios robots y detrás de obstáculos</span></Item>
          <Item as="li"><span><b>Radar</b> con la orientación de la torreta y el chasis</span></Item>
          <Item as="li"><span><b>Bailes</b> desde los botones, con aviso en pantalla</span></Item>
        </Revela>
      </div>
    </div>
  );
}

// --- Mando ------------------------------------------------------------------------------------------
export function Mando() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Control manual" titulo="La interfaz que hicimos para manejar el robot" />
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
            <Item as="li"><span><b>Seguro:</b> si deja de recibir órdenes, se para solo</span></Item>
            <Item as="li"><span><b>Disparo automático</b> al ver un rival (opcional)</span></Item>
            <Item as="li"><span><b><Contador valor={42} retraso={2.4} /> pruebas automáticas</b> del código</span></Item>
          </Revela>
        </div>
      </div>
    </div>
  );
}
