import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Cabecera, CURVA, fmt, Item, Revela, useFila, useFx } from '../componentes/base.jsx';
import { Barrido, Esquinas } from '../componentes/fotograma.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { CIRCUITO } from '../datos/cifras.js';
import laboratorioJpg from '@repo/docs/informes/figuras/bloque3/laboratorio.jpg';
import mandoJpg from '@repo/docs/informes/figuras/bloque3/mando.jpg';
import circuitoPng from '@repo/docs/informes/figuras/circuito_demo.png';
import rival1Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/2_rival1.jpg';
import camufladoJpg from '@repo/docs/informes/figuras/bloque3/demo_clase/3_camuflado.jpg';
import rival2Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/4_rival2_movimiento.jpg';
import rival3Jpg from '@repo/docs/informes/figuras/bloque3/demo_clase/5_rival3_escondido.jpg';
// Imágenes 058 y 059 del registro de la demo (evidencias/20261112_155726): causa del fallo con el rival 3
import rival3CausaJpg from '@repo/docs/informes/figuras/bloque3/demo_clase/7_rival3_causa.jpg';
import humoJpg from '@repo/docs/informes/figuras/bloque3/profesor/1_foto_humo.jpg';
import tapadoJpg from '@repo/docs/informes/figuras/bloque3/profesor/2_robot_tapado.jpg';
import profeRival2Jpg from '@repo/docs/informes/figuras/bloque3/profesor/3_rival2.jpg';
import distintoJpg from '@repo/docs/informes/figuras/bloque3/profesor/4_robot_distinto.jpg';
import disparoJpg from '@repo/docs/informes/figuras/interfaz/v1_deteccion_lejana_disparo.jpg';
import dosRobotsJpg from '@repo/docs/informes/figuras/interfaz/v2_dos_robots.jpg';
import autoSillaJpg from '@repo/docs/informes/figuras/bloque3/mando_auto/1_rival_y_silla.jpg';
import mandoTapadoJpg from '@repo/docs/informes/figuras/bloque3/mando_auto/2_robot_tapado.jpg';
import iaDetective from '@repo/docs/informes/figuras/senuelo/detector/detective.jpg';
import iaS1 from '@repo/docs/informes/figuras/senuelo/detector/aliado_s1.jpg';
import iaOrugas from '@repo/docs/informes/figuras/senuelo/detector/aliado_orugas.jpg';
import iaDibujo from '@repo/docs/informes/figuras/senuelo/detector/aliado_dibujo.jpg';
import iaBlanco from '@repo/docs/informes/figuras/senuelo/detector/aliado_blanco.jpg';
import webcamCerca from '@repo/docs/informes/figuras/senuelo/detector/webcam_cerca.jpg';
import webcamLejos from '@repo/docs/informes/figuras/senuelo/detector/webcam_lejos.jpg';
// Datos y fotos de la demo en clase, los mismos de la página del Bloque 3 (web/Bloque3/preparar_datos.py)
import '@repo/web/Bloque3/datos.js';

const BLOQUE3 = window.DATOS_BLOQUE3;
const URLS_RECORRIDO = import.meta.glob('@repo/web/Bloque3/imagenes/oficial/recorrido/*.webp', { eager: true, query: '?url', import: 'default' });

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
  const camino = [puntos[0]];   // vértices del recorrido ya hechos
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
    e.camino = p.tipo === 'mover' ? [...camino, pos] : camino;
    if (actual) return e;
    if (p.tipo === 'mover') camino.push(puntos[p.i + 1]);
  }
  return { pos, ang, modo: 'fin', vel: 0, objetivo: null, eliminados, camino, paso: GUION.pasos[GUION.pasos.length - 1] };
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

function Mapa({ e, t, compacto = false, posRival = rivalEn }) {
  const { puntos, ataques, rivales } = CIRCUITO;
  const d = puntos.map((p, i) => `${i ? 'L' : 'M'}${px(p).join(',')}`).join('');
  const [rx, ry] = px(e.pos);
  const led = colorLed(e, t);
  const modo = MODOS[e.modo];
  const blanco = e.objetivo != null ? px(posRival(e.objetivo, t)) : null;
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
      {/* El trozo de recorrido ya hecho queda más brillante */}
      {e.camino && e.camino.length > 1 && (
        <path d={e.camino.map((p, i) => `${i ? 'L' : 'M'}${px(p).join(',')}`).join('')} fill="none" stroke="var(--texto)" strokeWidth="1.6"
          strokeLinejoin="round" strokeLinecap="round" opacity="0.7" />
      )}
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
        const [cx, cy] = px(posRival(k, t));
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
      {!compacto && <g transform="translate(80,18)">
        <rect width="380" height="76" rx="6" fill="var(--panel-2)" stroke={modo.color} strokeWidth="1.5" />
        <text x="16" y="30" style={{ font: '700 17px var(--mono)', fill: modo.color }}>{modo.texto}</text>
        <text x="16" y="58" style={{ font: '600 15px var(--mono)', fill: 'var(--suave)' }}>
          {e.paso.tipo === 'mover' ? `${fmt(e.vel, 1)} m/s` : '0 m/s'}
        </text>
        <rect x="100" y="48" width="260" height="10" rx="5" fill="var(--borde)" />
        <rect x="100" y="48" width={260 * (e.paso.tipo === 'mover' ? e.vel / 0.5 : 0)} height="10" rx="5" fill={modo.color} />
      </g>}
      {/* Leyenda */}
      {!compacto && <g style={{ font: '600 15px var(--mono)' }}>
        <line x1="620" x2="656" y1="380" y2="380" stroke="var(--azul)" strokeWidth="4" />
        <text x="666" y="385" style={{ fill: 'var(--suave)' }}>avanza deprisa</text>
        <line x1="620" x2="656" y1="408" y2="408" stroke="var(--naranja)" strokeWidth="9" strokeLinecap="round" />
        <text x="666" y="413" style={{ fill: 'var(--suave)' }}>despacio, disparando</text>
      </g>}
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

// --- Foto real al disparar (en la simulación) -------------------------------------------------------
// Al empezar cada ráfaga aparece unos 2 s la imagen que vio el robot en la demo oficial del 12/11.
const ATAQUE_REAL = [
  { foto: rival1Jpg, texto: 'Rival 1 · 1,00' },
  { foto: camufladoJpg, texto: 'Robot camuflado · 0,99' },
  { foto: rival2Jpg, texto: 'Rival 2 en movimiento · 1,00' },
  { foto: rival3Jpg, texto: 'Rival 3 en la caja · 1,00' },
];
const FOTO_SEGUNDOS = 2;
// Esquina del plano donde sale cada foto, para no tapar al rival que se ataca
const POS_FOTO = [{ right: 18, top: 16 }, { right: 18, top: 16 }, { right: 18, bottom: 18 }, { left: 18, bottom: 18 }];
function fotoReal(t) {
  for (const p of GUION.pasos) {
    let inicio = null;
    let k = null;
    if (p.tipo === 'disparar') { inicio = p.desde; k = p.obj; }
    else if (p.tipo === 'mover' && p.ataque != null) { inicio = p.desde + MARCHA.disparo * p.dur; k = p.ataque; }
    if (inicio != null && t >= inicio && t < inicio + FOTO_SEGUNDOS) return k;
  }
  return null;
}
function FotoAtaque({ k }) {
  return (
    <AnimatePresence>
      {k != null && (
        <motion.div key={k} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.96 }}
          transition={{ duration: 0.25, ease: CURVA }}
          style={{ position: 'absolute', width: '42%', zIndex: 2, borderRadius: 4, overflow: 'hidden', border: '2px solid var(--rojo)',
            boxShadow: '0 12px 40px rgba(0,0,0,0.6)', ...POS_FOTO[k] }}>
          <img src={ATAQUE_REAL[k].foto} alt={`Cámara del robot en la demo: ${ATAQUE_REAL[k].texto}`}
            style={{ width: '100%', display: 'block', aspectRatio: '16 / 9', objectFit: 'cover' }} />
          <div className="mono" style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: '18px 12px 7px', fontSize: 15, fontWeight: 600, color: '#fff',
            background: 'linear-gradient(transparent, rgba(0,0,0,0.88))' }}>CÁMARA REAL · {ATAQUE_REAL[k].texto}</div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// --- Repetición real: las fotos de la demo oficial cada 0,5 s -----------------------------------------------
// La posición en el plano se reparte entre las fotos de cada fase (el robot no la registra).
const ORDEN_FASES = ['inicio', 'P1-ruta', 'P1-parada', 'R1-ruta', 'R1-marcha', 'R1-vuelta', 'R2-ruta', 'R2-marcha', 'baile'];
const FASE_REAL = {
  'inicio': { nombre: 'Salida', color: 'var(--tenue)', texto: 'Espera en la salida.' },
  'P1-ruta': { nombre: 'Túnel', color: 'var(--azul)', texto: 'Recta de 2,85 m entre las sillas a 0,5 m/s.' },
  'P1-parada': { nombre: 'P1 · parado', color: 'var(--rojo)', etapa: 0 },
  'R1-ruta': { nombre: 'Hacia R1', color: 'var(--azul)', texto: '2,19 m a 0,4 m/s y 1 m a la izquierda.' },
  'R1-marcha': { nombre: 'R1 · retrocede disparando', color: 'var(--naranja)', etapa: 1 },
  'R1-vuelta': { nombre: 'Vuelta', color: 'var(--azul)', texto: '1 m a la derecha.' },
  'R2-ruta': { nombre: 'Hacia R2', color: 'var(--azul)', texto: '2,88 m a 0,5 m/s y 0,7 m a la izquierda.' },
  'R2-marcha': { nombre: 'R2 · avanza disparando', color: 'var(--naranja)', etapa: 2 },
  'baile': { nombre: 'Baile', color: 'var(--acento)', etapa: 3 },
};
const VEL_FASE = { 'P1-ruta': 0.5, 'R1-ruta': 0.4, 'R1-vuelta': 0.5, 'R2-ruta': 0.5, 'R1-marcha': 0.1, 'R2-marcha': 0.1 };
const DEMO_REAL = (() => {
  const urls = {};
  for (const [ruta, url] of Object.entries(URLS_RECORRIDO)) urls[ruta.split('/').pop()] = url;
  const fotos = BLOQUE3.intentos[0].recorrido.map((f) => ({ ...f, url: urls[f.img.split('/').pop()] }));
  // Fracción de cada foto dentro de su fase
  let i = 0;
  while (i < fotos.length) {
    let j = i;
    while (j + 1 < fotos.length && fotos[j + 1].fase === fotos[i].fase) j += 1;
    for (let k = i; k <= j; k += 1) fotos[k].f = (k - i + 0.5) / (j - i + 1);
    i = j + 1;
  }
  return fotos;
})();
const TRAMOS_REALES = DEMO_REAL.reduce((tr, f, i) => {
  if (tr.length && tr[tr.length - 1].fase === f.fase) tr[tr.length - 1].n += 1;
  else tr.push({ fase: f.fase, n: 1, i });
  return tr;
}, []);
const PAUSA_FINAL = 12;     // cuadros quietos al acabar, antes de volver a empezar
function posRivalReal(c) {
  const n = ORDEN_FASES.indexOf(c.fase);
  const avance = n < 4 ? 0 : n === 4 ? c.f : 1;   // el rival 2 avanza durante el retroceso de R1
  return (k) => {
    const r = CIRCUITO.rivales[k];
    return r.hastaX == null ? [r.x, r.y] : [lerp(r.x, r.hastaX, avance), r.y];
  };
}
function estadoReal(k) {
  const c = DEMO_REAL[k];
  const n = ORDEN_FASES.indexOf(c.fase);
  const rival = posRivalReal(c);
  const eliminados = new Set();
  if (n > 2 || (n === 2 && c.f >= 0.5)) eliminados.add(0);
  if (n > 2) eliminados.add(1);
  if (n > 4) eliminados.add(2);
  if (n > 7) eliminados.add(3);
  let objetivo = null;
  if (c.fase === 'P1-parada') objetivo = c.f < 0.5 ? 0 : 1;
  if (c.fase === 'R1-marcha') objetivo = 2;
  if (c.fase === 'R2-marcha') objetivo = 3;
  const pos = [c.x, c.y];
  let ang = 0;
  if (objetivo != null) ang = angA(pos, rival(objetivo));
  else {
    const s = DEMO_REAL[k + 1];
    if (s && (s.x !== c.x || s.y !== c.y)) ang = angA(pos, [s.x, s.y]);
  }
  const modo = c.fase === 'P1-parada' ? 'parada' : c.fase.endsWith('marcha') ? 'marcha' : c.fase === 'baile' ? 'baile' : 'avanza';
  return { pos, ang, modo, vel: VEL_FASE[c.fase] || 0, objetivo, viendo: false, disparo: null, paso: { tipo: 'mover' }, eliminados };
}
function useCuadroReal(activo) {
  const reducido = useReducedMotion();
  const [i, setI] = useState(0);
  useEffect(() => {
    if (!activo) { setI(0); return undefined; }
    if (reducido) return undefined;
    const id = setInterval(() => setI((k) => (k + 1) % (DEMO_REAL.length + PAUSA_FINAL)), 125);   // ×4
    return () => clearInterval(id);
  }, [activo, reducido]);
  return Math.min(i, DEMO_REAL.length - 1);
}
const relojMin = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

function RepeticionReal({ k }) {
  const c = DEMO_REAL[k];
  const fase = FASE_REAL[c.fase];
  const total = DEMO_REAL[DEMO_REAL.length - 1].t;
  // En R2 fija el objetivo equivocado: el visor da un parpadeo rojo y su borde pasa a rojo
  const fallo = c.fase === 'R2-marcha';
  useEffect(() => {
    for (let j = 1; j <= 8; j += 1) if (DEMO_REAL[k + j]) new Image().src = DEMO_REAL[k + j].url;
  }, [k]);
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ position: 'relative', aspectRatio: '16 / 9', background: '#000', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)' }}>
        <img src={c.url} alt={`Cámara del robot en la demo oficial: ${fase.nombre}`} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
        {fallo && (
          <>
            <motion.div aria-hidden style={{ position: 'absolute', inset: 0, background: 'var(--rojo)', mixBlendMode: 'screen', pointerEvents: 'none' }}
              initial={{ opacity: 0.6 }} animate={{ opacity: [0.6, 0, 0.35, 0] }} transition={{ duration: 0.6 }} />
            <div aria-hidden style={{ position: 'absolute', inset: 0, border: '3px solid var(--rojo)', pointerEvents: 'none' }} />
          </>
        )}
        <div className="mono" style={{ position: 'absolute', left: 0, top: 0, padding: '7px 14px', background: fase.color, color: 'var(--fondo)', fontSize: 18, fontWeight: 700 }}>
          {fase.nombre.toUpperCase()}
        </div>
        <div className="mono" style={{ position: 'absolute', right: 14, top: 10, fontSize: 18, fontWeight: 600, color: '#fff', textShadow: '0 1px 4px #000' }}>
          {relojMin(c.t)} / {relojMin(total)} · ×4
        </div>
      </div>
      {/* Fases del recorrido, con su duración en fotos */}
      <div style={{ display: 'flex', height: 10, gap: 2 }}>
        {TRAMOS_REALES.map((tr) => (
          <div key={tr.i} style={{ flex: tr.n, background: FASE_REAL[tr.fase].color, opacity: k >= tr.i ? 1 : 0.3, borderRadius: 1 }} />
        ))}
      </div>
    </div>
  );
}

export function Circuito() {
  const t = useReloj(true);
  const e = estado(t);
  const activa = etapaActiva(e);
  // Un resalte del color del tramo se desliza de una tarjeta a otra
  const tarjetas = useRef(null);
  const marca = useFila(tarjetas, activa);
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Circuito" titulo="Dónde se para, dónde va despacio y a quién dispara" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.6fr 1fr', alignItems: 'start' }}>
        <div className="panel" style={{ padding: '14px 18px', position: 'relative' }}>
          <Mapa e={e} t={t} />
          <FotoAtaque k={fotoReal(t)} />
        </div>
        <div ref={tarjetas} style={{ position: 'relative' }}>
        {marca && (
          <motion.div aria-hidden style={{ position: 'absolute', left: -11, top: 0, width: 4, borderRadius: 2,
            background: activa >= 0 ? MODOS[ETAPAS[activa].modo].color : 'var(--borde)' }}
            initial={false} animate={{ y: marca.y, height: marca.h, opacity: activa >= 0 ? 1 : 0 }}
            transition={{ duration: 0.45, ease: CURVA, opacity: { duration: 0.25 } }} />
        )}
        <Revela style={{ display: 'grid', gap: 12 }} retraso={0.5} paso={0.14}>
          {ETAPAS.map((s, i) => (
            <Item key={s.etiqueta} data-fila={i} className="panel" style={{ padding: '16px 20px', transition: 'border-color 0.3s, background 0.3s',
              borderColor: i === activa ? MODOS[s.modo].color : undefined, background: i === activa ? 'var(--panel-2)' : undefined }}>
              <div className="etiqueta" style={{ color: i === activa ? MODOS[s.modo].color : undefined }}>{s.etiqueta}</div>
              <p style={{ color: 'var(--texto)', marginTop: 6, fontSize: 20 }}>{s.texto}</p>
            </Item>
          ))}
        </Revela>
        </div>
      </div>
    </div>
  );
}

// --- La demo oficial del 12/11, foto a foto -------------------------------------------------------------
// Cada fase tiene su explicación; las dos de ataque en marcha, más detallada.
const EXPLICA_REAL = {
  'R1-marcha': {
    titulo: 'Retrocede y dispara a la vez', color: 'var(--naranja)',
    puntos: [
      ['Tres tareas a la vez', 'el chasis mantiene 0,1 m/s, la torreta sigue al rival y otra tarea lanza el aviso y la ráfaga.'],
      ['Imagen nítida', 'de lo que llega en los últimos 0,2 s analiza la imagen menos movida.'],
      ['Rival en marcha', 'prevé cuánto gira el rival 2 (unos 2,4 °/s) y descuenta lo que viene de nuestro avance.'],
    ],
  },
  'R2-marcha': {
    titulo: 'Rival 3: fija otro robot y descarta al bueno', color: 'var(--rojo)', foto: rival3CausaJpg,
    pie: 'a) fija un robot del fondo, bajo una silla (0,99). b) 2 s después, el rival 3 (1,00), a la derecha de la línea de tiro.',
    puntos: [
      ['Fija otro robot', 'con la torreta a 180°, el primero que ve es uno del fondo (0,99). El rival 3 aún no está en la imagen.'],
      ['Descarta al rival 3', 'tras girar 40°, aparece a 1,00, pero de 30° a 36° a la derecha. Más de 25° de salto: lo toma por otro robot.'],
      ['Dispara sin verlo', 'la ráfaga ya ha empezado y la torreta sigue el giro previsto, unos 5 °/s: los 20 disparos le pasan por la izquierda.'],
      ['Qué lo habría evitado', 'el filtro de distancia de P1 también en marcha, que descarta los robots del fondo.'],
    ],
  },
};
export function DemoCircuito() {
  const k = useCuadroReal(true);
  const c = DEMO_REAL[k];
  const e = estadoReal(k);
  const fase = FASE_REAL[c.fase];
  const etapa = fase.etapa != null ? ETAPAS[fase.etapa] : null;
  const explica = EXPLICA_REAL[c.fase];
  const color = explica ? explica.color : etapa ? MODOS[etapa.modo].color : fase.color;
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Demo en clase" titulo="La demo oficial del 12/11, foto a foto" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.12fr 1fr', alignItems: 'start', gap: 28 }}>
        <div style={{ display: 'grid', gap: 14 }}>
          <RepeticionReal k={k} />
          <AnimatePresence>
            {explica?.foto && (
              <motion.figure key={c.fase} style={{ margin: 0, display: 'flex', gap: 16, alignItems: 'center' }}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <img src={explica.foto} alt="Imágenes analizadas en R2: el robot del fondo que fija y el rival 3, a la derecha de la línea de tiro"
                  style={{ width: 500, flex: 'none', borderRadius: 4, border: `1px solid ${color}`, display: 'block' }} />
                <figcaption className="mono" style={{ fontSize: 14, color: 'var(--suave)' }}>{explica.pie}</figcaption>
              </motion.figure>
            )}
          </AnimatePresence>
        </div>
        <div style={{ display: 'grid', gap: 14 }}>
          <AnimatePresence mode="wait">
            <motion.div key={explica ? c.fase : 'normal'} className="panel" style={{ padding: '18px 22px', borderColor: color }}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
              <div className="etiqueta" style={{ color }}>{explica ? explica.titulo : etapa ? etapa.etiqueta : fase.nombre}</div>
              {explica ? (
                <div style={{ display: 'grid', gap: explica.puntos.length > 3 ? 8 : 12, marginTop: 10 }}>
                  {explica.puntos.map(([t, d]) => (
                    <p key={t} style={{ margin: 0, fontSize: explica.puntos.length > 3 ? 17 : 19, color: 'var(--suave)' }}><b style={{ color: 'var(--texto)' }}>{t}:</b> {d}</p>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--texto)', marginTop: 8, fontSize: 21 }}>{etapa ? etapa.texto : fase.texto}</p>
              )}
            </motion.div>
          </AnimatePresence>
          {!explica && (
            <div className="panel" style={{ padding: '16px 22px' }}>
              <div className="etiqueta">Lo más difícil, más adelante</div>
              <p style={{ margin: '8px 0 0', fontSize: 19, color: 'var(--suave)' }}>
                <b style={{ color: 'var(--naranja)' }}>R1:</b> retroceder y disparar a un rival que también se mueve.
              </p>
              <p style={{ margin: '6px 0 0', fontSize: 19, color: 'var(--suave)' }}>
                <b style={{ color: 'var(--rojo)' }}>R2:</b> el rival 3, escondido detrás, con la torreta girada 180°.
              </p>
            </div>
          )}
          <div className="panel" style={{ padding: '8px 12px' }}>
            <div style={{ maxWidth: 640, margin: '0 auto' }}><Mapa e={e} t={k * 0.5} compacto posRival={posRivalReal(c)} /></div>
          </div>
          <p className="mono" style={{ margin: 0, fontSize: 14, color: 'var(--tenue)' }}>Fotos de la cámara cada 0,5 s, a ×4. La posición en el plano es aproximada.</p>
        </div>
      </div>
    </div>
  );
}

// --- Decisiones del circuito ------------------------------------------------------------------------------
// Valores de ENTREGA 2/WEEK3/circuito.py y pruebas del 11/11 (apartados 15 y 18 de la memoria).
const DECISIONES = [
  { t: 'Umbral 0,95', gana: 'el 94,5 % de lo que dispara en test es un robot', cede: 'un robot tapado (0,85–0,91) se queda sin disparos' },
  { t: 'Umbral 0,7 en una zona', gana: 'elimina al robot camuflado en papel (0,72–0,97)', cede: 'solo hacia su lado en P1 y con caja de menos de media imagen' },
  { t: 'Margen de puntería', gana: 'dispara con un error de menos de 3° o del 30 % del ancho de la caja', cede: 'hasta 4 correcciones antes de disparar' },
  { t: 'Ráfaga de 20', gana: '8 disparos de margen sobre los 12 impactos que se piden', cede: '6,2 s por rival' },
  { t: '0,1 m/s al atacar en marcha', gana: 'tiempo para girar la torreta, fijar al rival, avisar y disparar', cede: '52 de los 138 s de la demo' },
  { t: 'Imagen reciente', gana: 'un hilo lee siempre el vídeo; en marcha se usa la imagen menos movida', cede: 'en las paradas espera a la torreta quieta para confirmar' },
];
// Hijo de un <Item>: aparece un momento después que su tarjeta
const DESPUES = { oculto: { opacity: 0, x: -8 }, visible: { opacity: 1, x: 0, transition: { delay: 0.42, duration: 0.4, ease: CURVA } } };
export function Decisiones() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Decisiones" titulo="Qué decidimos en el circuito y qué cedimos" />
      <div style={{ display: 'grid', gap: 18 }}>
        <motion.div className="panel" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 34, alignItems: 'center', padding: '16px 26px' }}
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.6, ease: CURVA }}>
          <div>
            <div className="etiqueta" style={{ marginBottom: 4 }}>Ni muy grande ni muy lejos</div>
            <EscalaAlto />
          </div>
          <div style={{ display: 'grid', gap: 10, fontSize: 19 }}>
            <p style={{ margin: 0 }}><b style={{ color: 'var(--rojo)' }}>Más de media imagen:</b> sería un robot a menos de 0,5 m. Con las sillas azules muy cerca y poca luz salían cajas enormes con 0,95–0,99.</p>
            <p style={{ margin: 0 }}><b style={{ color: 'var(--naranja)' }}>En P1, a más de 2 m:</b> por el alto de la caja, fuera del circuito. El robot de otro grupo al fondo dio 0,98 a unos 3 m.</p>
          </div>
        </motion.div>
        <Revela style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }} retraso={0.8} paso={0.12}>
          {DECISIONES.map((d) => (
            <Item key={d.t} className="panel" style={{ padding: '16px 22px' }}>
              <b style={{ fontSize: 21 }}>{d.t}</b>
              <p style={{ margin: '8px 0 0', fontSize: 17, color: 'var(--suave)' }}><span className="mono" style={{ color: 'var(--acento)' }}>+ </span>{d.gana}</p>
              {/* Lo que se cede entra justo después de lo que se gana */}
              <motion.p variants={DESPUES} style={{ margin: '4px 0 0', fontSize: 17, color: 'var(--suave)' }}><span className="mono" style={{ color: 'var(--naranja)' }}>− </span>{d.cede}</motion.p>
            </Item>
          ))}
        </Revela>
      </div>
    </div>
  );
}

// --- Mosaico de fotos con rótulo ----------------------------------------------------------------------
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
// «Señal alterada» (con fx): el mosaico sufre medio segundo de interferencia, con franjas y desfase rojo y cian,
// y después cada foto recibe su veredicto: marco naranja si no dispara, destello rojo si dispara.
const ALTERA = { delay: 0.95, duration: 0.5 };
const DESFASES = [['#ff2a2a', [0, -14, 8, -6, 0]], ['#22e0ff', [0, 12, -7, 5, 0]]];
function MosaicoAlterado({ fotos, columnas }) {
  const capa = { position: 'absolute', inset: 0, pointerEvents: 'none' };
  const imagen = { width: '100%', height: '100%', objectFit: 'cover', display: 'block' };
  return (
    <Revela style={{ display: 'grid', gridTemplateColumns: `repeat(${columnas}, 1fr)`, gap: 18 }} retraso={0.3} paso={0.16}>
      {fotos.map((f, k) => {
        const veredicto = 1.6 + k * 0.22;
        return (
          <Item key={f.titulo} style={{ position: 'relative', aspectRatio: '16 / 9', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)' }}>
            <motion.img src={f.foto} alt={`${f.titulo}: ${f.texto}`} style={imagen}
              animate={{ x: [0, -12, 9, -5, 0], scale: [1, 1.04, 1.04, 1.04, 1] }} transition={ALTERA} />
            {/* Cada capa es la foto en un solo color (multiplicar), sumada a la original (trama) y desplazada */}
            {DESFASES.map(([color, xs]) => (
              <motion.div key={color} aria-hidden style={{ ...capa, background: color, mixBlendMode: 'screen' }}
                initial={{ opacity: 0 }} animate={{ opacity: [0, 0.85, 0.2, 0.7, 0], x: xs }} transition={ALTERA}>
                <img src={f.foto} alt="" style={{ ...imagen, mixBlendMode: 'multiply' }} />
              </motion.div>
            ))}
            <motion.div aria-hidden className="interferencia" initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0.3, 0.8, 0], y: [0, 6, -4, 3, 0] }} transition={ALTERA} />
            <div className="mono" style={{ position: 'absolute', left: 0, top: 0, padding: '6px 12px', background: f.color, color: 'var(--fondo)', fontSize: 16, fontWeight: 700 }}>
              {f.n} · {f.titulo.toUpperCase()}
            </div>
            <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: '22px 14px 9px', fontSize: 17,
              background: 'linear-gradient(transparent, rgba(0,0,0,0.85))', color: '#fff' }}>{f.texto}</div>
            {f.dispara ? (
              <motion.div aria-hidden style={{ ...capa, background: 'var(--rojo)', mixBlendMode: 'screen' }}
                initial={{ opacity: 0 }} animate={{ opacity: [0, 0.6, 0, 0.35, 0] }} transition={{ delay: veredicto, duration: 0.55 }} />
            ) : (
              <motion.div aria-hidden style={{ ...capa, border: '4px solid var(--naranja)' }}
                initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ delay: veredicto, duration: 1.3, times: [0, 0.12, 0.75, 1] }} />
            )}
          </Item>
        );
      })}
    </Revela>
  );
}
// --- El intento sorpresa del profesor ----------------------------------------------------------------------
// evidencias/20261112_160426: imágenes del profesor, robots tapados y un robot distinto en la recta final.
const SORPRESA = [
  { n: 'P1', titulo: 'Foto entre humo', texto: '0,59: lo ve, pero no le dispara', foto: humoJpg, color: 'var(--naranja)' },
  { n: 'P1', titulo: 'Robot tapado', texto: 'Con una tela: 0,85 a 0,91, no le dispara', foto: tapadoJpg, color: 'var(--naranja)' },
  { n: 'R1', titulo: 'Rival 2', texto: '1,00: lo sigue y le dispara', foto: profeRival2Jpg, color: 'var(--acento)', dispara: true },
  { n: 'R2', titulo: 'Robot distinto', texto: 'Otro modelo, con partes rojas: 0,99', foto: distintoJpg, color: 'var(--acento)', dispara: true },
];
// Robots generados con IA, con la caja del modelo de la demo (docs/informes/figuras/senuelo/detector/)
const ROBOTS_IA = [
  { foto: iaDetective, t: 'Camuflado', c: '0,99' },
  { foto: iaS1, t: 'Aliado S1', c: '1,00' },
  { foto: iaOrugas, t: 'Cabeza redonda', c: '1,00' },
  { foto: iaDibujo, t: 'Dibujo', c: '0,98' },
  { foto: iaBlanco, t: 'Blanco', c: '0,95' },
];
export function Sorpresa() {
  const fx = useFx();
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Prueba sorpresa" titulo="El profesor cambió los robots" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start', gap: 28 }}>
        <div style={{ display: 'grid', gap: 14 }}>
          {fx ? <MosaicoAlterado fotos={SORPRESA} columnas={2} /> : <Mosaico fotos={SORPRESA} columnas={2} />}
          <motion.div className="panel" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 18, alignItems: 'center', padding: 12 }}
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.4, duration: 0.5 }}>
            <img src={mandoTapadoJpg} alt="Robot tapado con una tela detectado a 0,97 con la interfaz del mando" style={{ width: '100%', borderRadius: 4, display: 'block' }} />
            <p style={{ margin: 0, fontSize: 19 }}>
              <b>Con la interfaz</b>, desde un ángulo mejor, el robot tapado sí llegó a <span className="mono acento">0,97</span> y le disparó.
            </p>
          </motion.div>
        </div>
        <Revela style={{ display: 'grid', gap: 14 }} retraso={0.8} paso={0.25}>
          <Item className="panel" style={{ padding: '16px 22px' }}>
            <div className="etiqueta">Por qué generaliza</div>
            <p style={{ margin: '6px 0 0', fontSize: 18 }}>
              Faster R-CNN v2 parte de pesos preentrenados en <b>COCO</b> (118.000 imágenes de 80 tipos de objeto): ya sabe ver formas, ruedas y vehículos. Nuestras 808 imágenes solo le enseñan qué es un robot.
            </p>
          </Item>
          <Item className="panel" style={{ padding: '16px 22px' }}>
            <div className="etiqueta">Ya lo habíamos visto antes de la demo</div>
            <p style={{ margin: '6px 0 10px', fontSize: 17, color: 'var(--suave)' }}>Robots camuflados y aliados hechos con IA: los reconoce a todos.</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
              {ROBOTS_IA.map((r) => (
                <div key={r.t} style={{ textAlign: 'center' }}>
                  <img src={r.foto} alt={`${r.t}: robot ${r.c}`} style={{ width: '100%', borderRadius: 4, display: 'block' }} />
                  <div className="mono" style={{ fontSize: 13, color: 'var(--suave)', marginTop: 4 }}>{r.t}</div>
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 }}>
              {[[webcamCerca, 'Papel cerca: 0,99, dispararía'], [webcamLejos, 'Papel lejos: 0,53, no']].map(([f, t]) => (
                <div key={t}>
                  <img src={f} alt={`Robot camuflado delante de la webcam. ${t}`} style={{ width: '100%', height: 125, objectFit: 'cover', borderRadius: 4, display: 'block' }} />
                  <div className="mono" style={{ fontSize: 13, color: 'var(--suave)', marginTop: 4 }}>{t}</div>
                </div>
              ))}
            </div>
          </Item>
          <Item className="panel" style={{ padding: '16px 22px', borderColor: 'var(--naranja)' }}>
            <div className="etiqueta" style={{ color: 'var(--naranja)' }}>Umbral 0,95</div>
            <p style={{ margin: '6px 0 0', fontSize: 18 }}>
              Detectó el robot tapado y la foto entre humo, pero no les disparó: preferimos no atacar a un posible falso positivo.
            </p>
          </Item>
        </Revela>
      </div>
    </div>
  );
}

// --- Por qué 0,95 ------------------------------------------------------------------------------------------
// Confianza de cada detección en el intento del profesor (evidencias/20261112_160426, vía web/Bloque3/datos.js).
const PROFESOR = BLOQUE3.intentos[1].detecciones;
const GRUPOS_UMBRAL = [
  { parada: 'P1', titulo: 'P1 · parado', ancho: 210, color: 'var(--rojo)' },
  { parada: 'R1-marcha', titulo: 'R1 · rival 2', ancho: 250, color: 'var(--naranja)' },
  { parada: 'R2-marcha', titulo: 'R2 · robot distinto', ancho: 330, color: 'var(--naranja)' },
];
// «La barrera del umbral» (con fx): la línea de 0,95 se dibuja como un láser y los puntos suben desde abajo.
// Los de P1 se quedan por debajo; los que la cruzan se encienden en verde, y cuando la cruza el primer punto
// del robot distinto la línea parpadea, sale un anillo y aparece «0,96: lo fija y le dispara».
function GraficaUmbral({ fx }) {
  const W = 900;
  const H = 470;
  const m = { l: 70, r: 20, t: 46, b: 40 };
  const sy = (v) => m.t + ((1 - v) / (1 - 0.3)) * (H - m.t - m.b);
  const huecos = 24;
  let x0 = m.l;
  const grupos = GRUPOS_UMBRAL.map((g) => {
    const det = PROFESOR.filter((d) => d.parada === g.parada);
    const r = { ...g, det, x0 };
    x0 += g.ancho + huecos;
    return r;
  });
  const sx = (g, i) => g.x0 + 10 + (i / Math.max(1, g.det.length - 1)) * (g.ancho - 20);
  const yu = sy(0.95);
  let orden = 0;
  // Dónde cruza el umbral el robot distinto: primera imagen de R2 que pasa 0,95
  const r2 = grupos[2];
  const cruce = r2.det.findIndex((d) => d.aceptadas > 0);
  const primera = r2.det.findIndex((d) => d.conf.length);
  const conPunto = (lista) => lista.filter((d) => d.conf.length).length;
  const retrasoPunto = (n) => 0.8 + n * 0.012;
  // Momento en que el primer punto aceptado de R2 cruza la línea (unos 2,1 s)
  const tCruce = retrasoPunto(conPunto(grupos[0].det) + conPunto(grupos[1].det) + conPunto(r2.det.slice(0, cruce + 1))) + 0.2;
  const yCruce = cruce > 0 ? sy(r2.det[cruce].conf[0]) : 0;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', display: 'block' }} role="img"
      aria-label="Confianza de cada detección en el intento del profesor frente al umbral 0,95">
      {[0.3, 0.5, 0.7, 0.9, 1].map((v) => (
        <g key={v}>
          <line x1={m.l} x2={W - m.r} y1={sy(v)} y2={sy(v)} stroke="var(--borde)" strokeDasharray="2 6" />
          <text x={m.l - 12} y={sy(v) + 5} textAnchor="end" style={{ font: '14px var(--mono)', fill: 'var(--tenue)' }}>{fmt(v, 2)}</text>
        </g>
      ))}
      <text x={18} y={(m.t + H - m.b) / 2} textAnchor="middle" transform={`rotate(-90 18 ${(m.t + H - m.b) / 2})`}
        style={{ font: '14px var(--mono)', fill: 'var(--tenue)' }}>confianza</text>
      {grupos.map((g) => (
        <g key={g.parada}>
          <rect x={g.x0} y={m.t - 8} width={g.ancho} height={H - m.t - m.b + 8} fill={g.color} opacity="0.06" />
          <text x={g.x0 + g.ancho / 2} y={m.t - 18} textAnchor="middle" style={{ font: '600 15px var(--mono)', fill: g.color }}>{g.titulo}</text>
          <text x={g.x0 + g.ancho / 2} y={H - 14} textAnchor="middle" style={{ font: '13px var(--mono)', fill: 'var(--tenue)' }}>
            {g.det.length} imágenes{g.parada === 'P1' ? ', una por ángulo' : ''}
          </text>
        </g>
      ))}
      <motion.g animate={fx && cruce > 0 ? { opacity: [1, 0.15, 1, 0.35, 1] } : undefined} transition={{ delay: tCruce, duration: 0.45 }}>
        {fx && (
          <motion.line x1={m.l} x2={W - m.r} y1={yu} y2={yu} stroke="var(--rojo)" strokeWidth="9" strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0.5 }} animate={{ pathLength: 1, opacity: [0.5, 0.5, 0] }}
            transition={{ delay: 0.3, duration: 0.8, opacity: { delay: 0.3, duration: 1.5, times: [0, 0.55, 1] } }} />
        )}
        <motion.line x1={m.l} x2={W - m.r} y1={yu} y2={yu} stroke="var(--rojo)" strokeWidth="2.5" strokeDasharray="8 6"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.3, duration: 0.8 }} />
        <text x={m.l + 8} y={yu - 10} style={{ font: '700 16px var(--mono)', fill: 'var(--rojo)' }}>umbral 0,95</text>
      </motion.g>
      {/* Un punto por imagen: su detección más segura */}
      {grupos.map((g) => g.det.map((d, i) => d.conf.slice(0, 1).map((c, j) => {
        orden += 1;
        const ok = d.aceptadas > 0;
        if (fx) {
          const t = retrasoPunto(orden);
          const radio = g.parada === 'P1' ? 8 : 5;
          return (
            <motion.g key={`${g.parada}-${i}-${j}`} initial={{ y: sy(0.3) - sy(c) + 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
              transition={{ delay: t, duration: 0.5, ease: CURVA, opacity: { delay: t, duration: 0.12 } }}>
              <motion.circle cx={sx(g, i)} cy={sy(c)} r={radio} fill="var(--fondo)" stroke="var(--naranja)" strokeWidth="2.5"
                animate={{ opacity: ok ? 0 : 1 }} transition={{ delay: t + 0.2, duration: 0.12 }} />
              {ok && (
                <motion.circle cx={sx(g, i)} cy={sy(c)} r={radio} fill="var(--acento)" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: t + 0.2, duration: 0.12 }} />
              )}
            </motion.g>
          );
        }
        return (
          <motion.circle key={`${g.parada}-${i}-${j}`} cx={sx(g, i)} cy={sy(c)} r={g.parada === 'P1' ? 8 : 5}
            fill={ok ? 'var(--acento)' : 'var(--fondo)'} stroke={ok ? 'none' : 'var(--naranja)'} strokeWidth="2.5"
            initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8 + orden * 0.012, duration: 0.25 }}
            style={{ transformBox: 'fill-box', transformOrigin: 'center' }} />
        );
      })))}
      {/* Anotaciones */}
      <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.6 }} style={{ font: '600 15px var(--mono)' }}>
        <text x={grupos[0].x0 + grupos[0].ancho / 2} y={sy(0.79)} textAnchor="middle" style={{ fill: 'var(--texto)' }}>robot tapado</text>
        <text x={grupos[0].x0 + grupos[0].ancho / 2} y={sy(0.79) + 18} textAnchor="middle" style={{ fill: 'var(--suave)', fontWeight: 400 }}>0,85–0,91</text>
        <text x={grupos[0].x0 + grupos[0].ancho / 2} y={sy(0.62) - 14} textAnchor="middle" style={{ fill: 'var(--texto)' }}>foto entre humo · 0,59</text>
        <text x={grupos[1].x0 + grupos[1].ancho / 2} y={sy(0.5)} textAnchor="middle" style={{ fill: 'var(--texto)' }}>lo sigue a 0,99</text>
        <text x={grupos[1].x0 + grupos[1].ancho / 2} y={sy(0.5) + 18} textAnchor="middle" style={{ fill: 'var(--suave)', fontWeight: 400 }}>hasta que sale de la imagen</text>
        {cruce > 0 && (
          <g>
            <line x1={sx(r2, primera)} x2={sx(r2, cruce)} y1={sy(0.36)} y2={sy(0.36)} stroke="var(--texto)" strokeWidth="1.5" />
            <text x={(sx(r2, primera) + sx(r2, cruce)) / 2} y={sy(0.36) + 22} textAnchor="middle" style={{ fill: 'var(--texto)' }}>sube en 3 s</text>
          </g>
        )}
      </motion.g>
      {/* El cruce: con fx aparece en cuanto el punto pasa la línea; sin fx, con el resto de anotaciones */}
      {cruce > 0 && (
        <g style={{ font: '600 15px var(--mono)' }}>
          {fx && (
            <motion.circle cx={sx(r2, cruce)} cy={yCruce} fill="none" stroke="var(--acento)" strokeWidth="2.5"
              initial={{ r: 13, opacity: 0 }} animate={{ r: [13, 16, 48], opacity: [0, 0.95, 0] }}
              transition={{ delay: tCruce, duration: 0.8, times: [0, 0.08, 1], ease: 'easeOut' }} />
          )}
          <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: fx ? tCruce + 0.1 : 2.6 }}>
            <circle cx={sx(r2, cruce)} cy={yCruce} r="13" fill="none" stroke="var(--acento)" strokeWidth="2.5" />
            <line x1={sx(r2, cruce)} x2={sx(r2, cruce + 12)} y1={sy(0.93)} y2={sy(0.7)} stroke="var(--acento)" strokeWidth="1.5" />
            <text x={sx(r2, cruce + 12)} y={sy(0.7) + 20} textAnchor="middle" style={{ fill: 'var(--acento)' }}>0,96: lo fija</text>
            <text x={sx(r2, cruce + 12)} y={sy(0.7) + 38} textAnchor="middle" style={{ fill: 'var(--acento)' }}>y le dispara</text>
          </motion.g>
        </g>
      )}
    </svg>
  );
}

// Alto de la caja en la imagen (720 px): robot del fondo 61 px, rivales 100-232 px, sillas cercanas 650-720 px.
const ALTOS = [
  { desde: 0, hasta: 12, color: 'var(--naranja)', texto: 'más de 2 m' },
  { desde: 12, hasta: 50, color: 'var(--acento)', texto: 'rival' },
  { desde: 50, hasta: 100, color: 'var(--rojo)', texto: 'a menos de 0,5 m' },
];
const MARCAS_ALTO = [
  { v: 8.5, texto: 'robot del fondo · 0,98', abajo: false },
  { v: 23, texto: 'rivales del circuito', abajo: true, rango: [14, 32] },
  { v: 95, texto: 'sillas cercanas · 0,95–0,99', abajo: false, rango: [90, 100] },
];
function EscalaAlto() {
  const W = 560;
  const sx = (v) => 10 + (v / 100) * (W - 20);
  return (
    <svg viewBox={`0 0 ${W} 120`} style={{ width: '100%', display: 'block' }} aria-label="Alto de la caja en porcentaje de la imagen">
      {/* Las tres zonas crecen una tras otra y después se enganchan las marcas */}
      {ALTOS.map((z, i) => (
        <g key={z.texto}>
          <motion.rect x={sx(z.desde)} y={44} width={sx(z.hasta) - sx(z.desde) - 2} height={20} fill={z.color} opacity="0.85"
            initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 0.6 + i * 0.25, duration: 0.45, ease: CURVA }}
            style={{ transformBox: 'fill-box', transformOrigin: 'left center' }} />
          <motion.text x={(sx(z.desde) + sx(z.hasta)) / 2} y={84} textAnchor="middle" style={{ font: '600 13px var(--mono)', fill: z.color }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.85 + i * 0.25 }}>{z.texto}</motion.text>
        </g>
      ))}
      {MARCAS_ALTO.map((mk, i) => (
        <motion.g key={mk.texto} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.45 + i * 0.12 }}>
          {mk.rango
            ? <motion.rect x={sx(mk.rango[0])} y={38} width={sx(mk.rango[1]) - sx(mk.rango[0])} height={32} fill="none" stroke="var(--texto)" strokeWidth="2"
              initial={{ scale: 1.45 }} animate={{ scale: 1 }} transition={{ delay: 1.45 + i * 0.12, duration: 0.45, ease: CURVA }}
              style={{ transformBox: 'fill-box', transformOrigin: 'center' }} />
            : <line x1={sx(mk.v)} x2={sx(mk.v)} y1={36} y2={72} stroke="var(--texto)" strokeWidth="2.5" />}
          <text x={sx(mk.v)} y={mk.abajo ? 106 : 26} textAnchor={mk.v > 80 ? 'end' : mk.v < 10 ? 'start' : 'middle'}
            style={{ font: '13px var(--mono)', fill: 'var(--texto)' }}>{mk.texto}</text>
        </motion.g>
      ))}
      <text x={sx(100)} y={118} textAnchor="end" style={{ font: '12px var(--mono)', fill: 'var(--tenue)' }}>alto de la caja, % de la imagen</text>
    </svg>
  );
}

const RAZONES_UMBRAL = [
  { t: 'Elegido en validación', d: 'En test, el 94,5 % de lo que detecta por encima de 0,95 es un robot.', color: 'var(--acento)' },
  { t: 'Lo que deja pasar', d: 'Robot tapado (0,85–0,91) y foto entre humo (0,59).', color: 'var(--naranja)' },
  { t: 'Lo que sí ataca', d: 'El robot distinto sube a 0,96 en unos 3 s y le dispara.', color: 'var(--acento)' },
];
export function Umbral() {
  const fx = useFx();
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Cuándo disparar" titulo="Por qué 0,95" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.75fr 1fr', alignItems: 'start', gap: 28 }}>
        <div className="panel" style={{ padding: '14px 18px' }}>
          <div className="etiqueta" style={{ marginBottom: 4 }}>Intento del profesor: cada punto es una imagen</div>
          <GraficaUmbral fx={fx} />
          <div className="mono" style={{ display: 'flex', gap: 24, fontSize: 15, color: 'var(--suave)', marginTop: 4 }}>
            <span><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 6, background: 'var(--acento)', marginRight: 8 }} />pasa el umbral: le dispara</span>
            <span><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 6, border: '2.5px solid var(--naranja)', marginRight: 8 }} />no llega: no le dispara</span>
          </div>
        </div>
        <Revela style={{ display: 'grid', gap: 18 }} retraso={0.6} paso={0.3}>
          {RAZONES_UMBRAL.map((r) => (
            <Item key={r.t} className="panel" style={{ padding: '22px 26px', borderLeft: `4px solid ${r.color}` }}>
              <div className="etiqueta" style={{ color: r.color }}>{r.t}</div>
              <p style={{ color: 'var(--texto)', margin: '8px 0 0', fontSize: 22 }}>{r.d}</p>
            </Item>
          ))}
        </Revela>
      </div>
    </div>
  );
}

// --- Mando ------------------------------------------------------------------------------------------
// Controles de ENTREGA 2/WEEK3/mando/README.md
const CONTROLES = [
  { que: 'Chasis', tecla: 'WASD · joystick izq.', d: 'Ruedas mecanum: se mueve hacia cualquier lado sin girar, hasta 0,5 m/s. Z/X o L1/R1 lo giran a 30 °/s.' },
  { que: 'Torreta', tecla: 'Flechas · joystick der.', d: 'Gira a 30 °/s. W avanza hacia donde mira la cámara.' },
  { que: 'Disparo', tecla: 'Clic · R2', d: 'Infrarrojos mientras se mantiene pulsado.' },
  { que: 'Radar', tecla: 'en pantalla', d: 'Hacia dónde mira la torreta respecto al chasis.' },
  { que: 'Bailes', tecla: 'Q E F C · □ △ ○ ✕', d: 'Moonwalk, Waka Waka, Super Estrella y Risa, con música en el robot.' },
  { que: 'Parada', tecla: 'Esc · SHARE', d: 'Y se para solo si no recibe órdenes en 0,3 s.' },
];
const AJUSTES = ['Disparo automático', 'Asistente de puntería (aimbot)', 'Umbral de detección', 'Moverse hacia la cámara', 'Reasignar controles'];
export function Mando() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Control manual" titulo="La interfaz que hicimos para manejar el robot" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1fr 1fr', alignItems: 'start', gap: 28 }}>
        <div style={{ display: 'grid', gap: 16 }}>
          <div style={{ position: 'relative', borderRadius: 6, overflow: 'hidden', border: '1px solid var(--borde)' }}>
            <motion.img src={mandoJpg} alt="Interfaz del mando con un robot detectado al 99,9 %" style={{ width: '100%', display: 'block' }}
              initial={{ scale: 1.25, x: '6%', y: '4%' }} animate={{ scale: 1, x: '0%', y: '0%' }}
              transition={{ delay: 0.2, duration: 1.6, ease: CURVA }} />
            <motion.div style={{ position: 'absolute', left: '44.5%', top: '42%', width: '15%', height: '22%', border: '2px solid var(--acento)', boxShadow: '0 0 0 9999px rgba(0,0,0,0.35)' }}
              initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ delay: 1.9, duration: 2.4, times: [0, 0.15, 0.8, 1] }}>
              {/* El recuadro de la detección se engancha con las esquinas */}
              <Esquinas retraso={1.9} tam={12} desde={1.5} style={{ inset: -6 }} />
            </motion.div>
          </div>
          <motion.div className="panel" style={{ padding: '16px 22px' }} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.6 }}>
            <div className="etiqueta" style={{ marginBottom: 10 }}>Se puede cambiar desde Ajustes</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {AJUSTES.map((a, k) => (
                <motion.span key={a} className="chip" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.75 + k * 0.08, duration: 0.35, ease: CURVA }}>{a}</motion.span>
              ))}
            </div>
            <p style={{ margin: '10px 0 0', fontSize: 17, color: 'var(--suave)' }}>
              El asistente centra la torreta en el rival y, con el disparo automático, dispara al tenerlo centrado.
            </p>
          </motion.div>
        </div>
        <Revela className="panel" retraso={0.5} paso={0.12} style={{ padding: '14px 24px' }}>
          {CONTROLES.map((c) => (
            <Item key={c.que} style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 16, padding: '12px 0', borderTop: '1px solid var(--borde)' }}>
              <div>
                <b style={{ fontSize: 20 }}>{c.que}</b>
                <div className="mono" style={{ fontSize: 13, color: 'var(--tenue)', marginTop: 4 }}>{c.tecla}</div>
              </div>
              <p style={{ margin: 0, fontSize: 18, color: 'var(--suave)' }}>{c.d}</p>
            </Item>
          ))}
        </Revela>
      </div>
    </div>
  );
}

// --- El mando con el robot real ---------------------------------------------------------------------------
const CAPTURAS_MANDO = [
  { foto: disparoJpg, texto: '11/11 · rival lejano bajo una mesa, con el aviso de disparo' },
  { foto: dosRobotsJpg, texto: '11/11 · dos robots detectados a la vez' },
  { foto: autoSillaJpg, texto: '12/11 · disparo automático: rival a 1,00 (y una silla a 0,79, con umbral 0,5)' },
  { foto: mandoTapadoJpg, texto: '12/11 · disparo automático al robot tapado: 0,97' },
];
const HARDWARE = [
  { que: 'Ordenador', ahora: 'RTX 5070 de portátil: 108 ms por imagen en la demo, pero 130–570 ms con la interfaz y el vídeo a la vez.', falta: 'Una GPU de sobremesa, o un modelo más ligero como MobileNet (unos 32 ms).' },
  { que: 'RoboMaster', ahora: 'Solo envía el vídeo por wifi, a 8–16 imágenes por segundo, y recibe órdenes: no puede ejecutar el detector.', falta: 'Un ordenador a bordo con GPU (tipo Jetson) para no depender de la wifi, y un router propio.' },
];
export function MandoReal() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 03 · Control manual" titulo="La interfaz con el robot real" />
      <div className="cuerpo" style={{ gridTemplateColumns: '1.35fr 1fr', alignItems: 'start', gap: 28 }}>
        <Revela style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }} retraso={0.3} paso={0.16}>
          {CAPTURAS_MANDO.map((c, k) => (
            <Item key={c.texto} style={{ position: 'relative', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--borde)', aspectRatio: '16 / 9' }}>
              <img src={c.foto} alt={c.texto} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
              <Barrido retraso={0.7 + k * 0.16} duracion={0.6} alto={56} />
              <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: '20px 12px 8px', fontSize: 15,
                background: 'linear-gradient(transparent, rgba(0,0,0,0.88))', color: '#fff' }}>{c.texto}</div>
            </Item>
          ))}
        </Revela>
        <Revela style={{ display: 'grid', gap: 14 }} retraso={1} paso={0.25}>
          <Item className="etiqueta">El límite es el hardware</Item>
          {HARDWARE.map((h) => (
            <Item key={h.que} className="panel" style={{ padding: '16px 22px' }}>
              <b style={{ fontSize: 21 }}>{h.que}</b>
              <p style={{ margin: '6px 0 0', fontSize: 17, color: 'var(--suave)' }}>{h.ahora}</p>
              {/* La solución entra un momento después que el problema */}
              <motion.p variants={DESPUES} style={{ margin: '8px 0 0', fontSize: 17 }}><span className="mono acento">Haría falta: </span>{h.falta}</motion.p>
            </Item>
          ))}
        </Revela>
      </div>
    </div>
  );
}

// Imágenes que se precargan mientras se muestra la diapositiva anterior
Seccion3.imagenes = [laboratorioJpg, mandoJpg, circuitoPng];
Circuito.imagenes = ATAQUE_REAL.map((a) => a.foto);
DemoCircuito.imagenes = [...DEMO_REAL.slice(0, 12).map((f) => f.url), rival3CausaJpg];
Sorpresa.imagenes = [...SORPRESA.map((f) => f.foto), mandoTapadoJpg, ...ROBOTS_IA.map((r) => r.foto), webcamCerca, webcamLejos];
Mando.imagenes = [mandoJpg];
MandoReal.imagenes = CAPTURAS_MANDO.map((c) => c.foto);
