import { useEffect, useMemo } from 'react';
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Revela } from '../componentes/base.jsx';
import { BarrasH } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { CIRCUITO, PRESUPUESTO } from '../datos/cifras.js';
import laboratorioJpg from '@repo/docs/informes/figuras/bloque3/laboratorio.jpg';
import mandoJpg from '@repo/docs/informes/figuras/bloque3/mando.jpg';
import circuitoPng from '@repo/docs/informes/figuras/circuito_demo.png';

// --- Separador ---------------------------------------------------------------------------------
export function Seccion3() {
  return (
    <Seccion numero="03" titulo="Robot" color="var(--rojo)" fotos={[laboratorioJpg, mandoJpg, circuitoPng]}
      lema="Llevamos el detector al RoboMaster: recorrer el circuito, encontrar a los rivales y dispararles."
      puntos={['circuito por tramos', 'ataque en marcha', 'control manual']} />
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
            <div className="etiqueta">Primera recta (P1) · medida el 05/11</div>
            <p style={{ color: 'var(--texto)', marginTop: 6 }}>Avanza 2,85 m a 0,5 m/s (unos 6 s), se para y gira la torreta: a la derecha está el rival 1 y a la izquierda, el robot camuflado.</p>
          </Item>
          <Item className="panel" style={{ padding: '18px 22px' }}>
            <div className="etiqueta">R1 y R2 · ataques en marcha</div>
            <p style={{ color: 'var(--texto)', marginTop: 6 }}>Ataca sin pararse dos veces: retrocede 1,25 m disparando al rival 2, que también se mueve, y en los 2 m finales ataca al rival 3, colocado en alto. Las ruedas mecanum le dejan ir hacia atrás o de lado sin girar.</p>
          </Item>
          <Item className="panel" style={{ padding: '18px 22px', borderColor: 'var(--acento-oscuro)' }}>
            <div className="etiqueta acento">Primer problema del laboratorio</div>
            <p style={{ marginTop: 6 }}>La orden del SDK de «avanzar tantos metros» no respetaba la velocidad pedida: el robot iba a 0,06 m/s. Ahora le mandamos la velocidad 20 veces por segundo y medimos lo recorrido con la odometría: frena en los últimos 17 cm y se para con 1 cm de error.</p>
          </Item>
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
            <Item as="li"><span><b><Contador valor={31} retraso={2.4} /> pruebas automáticas</b> del código</span></Item>
          </Revela>
        </div>
      </div>
    </div>
  );
}
