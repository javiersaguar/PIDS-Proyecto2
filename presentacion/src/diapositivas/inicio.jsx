import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cabecera, Contador, CURVA, Item, Revela } from '../componentes/base.jsx';
import { Fotograma } from '../componentes/fotograma.jsx';
import { Letras, Tipeo } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { EQUIPO } from '../datos/cifras.js';
import robotPartes from '@repo/docs/informes/figuras/robot_partes.png';

// Retícula de puntería
export function Reticula({ tam = 120, color = 'var(--acento)', fijada = false }) {
  return (
    <svg width={tam} height={tam} viewBox="-60 -60 120 120" style={{ overflow: 'visible' }} aria-hidden>
      <motion.g animate={{ rotate: fijada ? 0 : 360 }} transition={{ duration: 12, ease: 'linear', repeat: fijada ? 0 : Infinity }}>
        <circle r="38" fill="none" stroke={color} strokeWidth="1.5" strokeDasharray="6 8" />
      </motion.g>
      <circle r="22" fill="none" stroke={color} strokeWidth="2" />
      {[0, 90, 180, 270].map((a) => (
        <line key={a} x1="0" y1="-52" x2="0" y2="-28" stroke={color} strokeWidth="2.5" transform={`rotate(${a})`} />
      ))}
      <circle r="2.5" fill={color} />
    </svg>
  );
}

function Reloj() {
  const [t, setT] = useState(0);
  useEffect(() => {
    const inicio = performance.now();
    const id = setInterval(() => setT((performance.now() - inicio) / 1000), 100);
    return () => clearInterval(id);
  }, []);
  const s = Math.floor(t);
  return <span>00:{String(Math.floor(s / 60)).padStart(2, '0')}:{String(s % 60).padStart(2, '0')}.{Math.floor((t % 1) * 10)}</span>;
}

// --- 1. Portada --------------------------------------------------------------------------------
export function Portada() {
  const f = FOTOGRAMAS.portada;
  const centros = f.cajas.map((c) => [(c.x + c.w / 2) * 100, (c.y + c.h / 2) * 100]);
  const ruta = [...centros, centros[0]];
  return (
    <div className="diapo sangre" style={{ background: '#000' }}>
      {/* Encendido de pantalla: una línea que se abre */}
      <motion.div style={{ position: 'absolute', inset: 0, transformOrigin: 'center' }}
        initial={{ scaleY: 0.003, scaleX: 0.6, filter: 'brightness(4) saturate(0)' }}
        animate={{ scaleY: [0.003, 0.003, 1], scaleX: [0.6, 1, 1], filter: ['brightness(4) saturate(0)', 'brightness(4) saturate(0)', 'brightness(1) saturate(1)'] }}
        transition={{ duration: 0.9, times: [0, 0.35, 1], ease: [0.7, 0, 0.2, 1] }}>
        <Fotograma foto={f} modo="deteccion" escaneo retraso={1.2} confianzas={[0.99, 0.98, 0.97]}
          style={{ position: 'absolute', inset: 0, aspectRatio: 'auto', border: 0, borderRadius: 0 }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(12,13,11,0.55) 0%, rgba(12,13,11,0) 22%, rgba(12,13,11,0.25) 48%, rgba(12,13,11,0.92) 76%, #0c0d0b 100%)' }} />
        <div className="lineas-crt" />
      </motion.div>

      {/* Retícula que salta de un robot a otro */}
      <motion.div style={{ position: 'absolute', marginLeft: -60, marginTop: -60, zIndex: 3 }}
        initial={{ left: `${ruta[0][0]}%`, top: `${ruta[0][1]}%`, opacity: 0, scale: 2 }}
        animate={{ left: ruta.map((c) => `${c[0]}%`), top: ruta.map((c) => `${c[1]}%`), opacity: 1, scale: 1 }}
        transition={{ left: { delay: 2.6, duration: 9, repeat: Infinity, ease: 'easeInOut' },
          top: { delay: 2.6, duration: 9, repeat: Infinity, ease: 'easeInOut' },
          opacity: { delay: 2.4, duration: 0.3 }, scale: { delay: 2.4, duration: 0.5, ease: CURVA } }}>
        <Reticula />
      </motion.div>

      {/* Indicadores de la cámara */}
      <div className="mono" style={{ position: 'absolute', left: 56, right: 56, top: 40, display: 'flex', justifyContent: 'space-between',
        fontSize: 16, letterSpacing: '0.14em', color: 'var(--texto)', zIndex: 4, textTransform: 'uppercase' }}>
        <Tipeo texto="PIDS 2026 · Proyecto 2 · Grupo 2" retraso={1} duracion={0.9} />
        <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }} style={{ display: 'flex', gap: 18 }}>
          <motion.span style={{ color: 'var(--rojo)' }} animate={{ opacity: [1, 0.15, 1] }} transition={{ duration: 1.2, repeat: Infinity }}>● REC</motion.span>
          <Reloj />
        </motion.span>
      </div>

      <div style={{ position: 'absolute', left: 88, right: 88, bottom: 60, zIndex: 4 }}>
        <motion.div className="fase" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }}>
          Proyectos en Ingeniería de Datos y Sistemas · ETSIT UPM
        </motion.div>
        <h1 style={{ margin: '14px 0 0', fontSize: 108, lineHeight: 0.98, fontWeight: 700, letterSpacing: '-0.045em', position: 'relative' }}>
          <Letras texto="Detección de" retraso={1.9} paso={0.03} /><br />
          <Letras texto="RoboMasters" retraso={2.2} paso={0.045} style={{ color: 'var(--acento)' }} />
          {/* Desfase de color de una décima: «glitch» al terminar de escribirse */}
          <motion.span aria-hidden style={{ position: 'absolute', left: 0, bottom: 0, color: 'var(--rojo)', mixBlendMode: 'screen', pointerEvents: 'none' }}
            initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0, 0.7, 0], x: [0, -8, 5, -3, 0] }} transition={{ delay: 2.85, duration: 0.45 }}>
            RoboMasters
          </motion.span>
          <motion.span aria-hidden style={{ position: 'absolute', left: 0, bottom: 0, color: '#6fd3ff', mixBlendMode: 'screen', pointerEvents: 'none' }}
            initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0, 0.7, 0], x: [0, 7, -4, 3, 0] }} transition={{ delay: 2.85, duration: 0.45 }}>
            RoboMasters
          </motion.span>
        </h1>
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 3.1, duration: 0.7, ease: CURVA }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginTop: 22, gap: 40 }}>
          <p style={{ margin: 0, fontSize: 27, color: 'var(--suave)' }}>
            Del vídeo al disparo: datos propios, un detector y un robot.
          </p>
          <p className="mono" style={{ margin: 0, fontSize: 16, color: 'var(--suave)', textAlign: 'right', lineHeight: 1.7 }}>
            Javier Saguar · Alejandro Cuevas · Mónica Fernández<br />Pedro José Orrego · Daniel Naval
          </p>
        </motion.div>
      </div>
    </div>
  );
}

// --- 2. El reto y las tres fases ----------------------------------------------------------------
const FASES_RETO = [
  { n: '01', nombre: 'Datos', que: 'Grabar diez vídeos, extraer, anotar y analizar los robots', cifra: 808, pie: 'imágenes y 1420 robots anotados' },
  { n: '02', nombre: 'Modelo', que: 'Entrenar y comparar siete detectores; elegir uno con validación', cifra: 0.952, dec: 3, pie: 'AP@0,5 en test con Faster R-CNN v2' },
  { n: '03', nombre: 'Robot', que: 'Llevar el detector al RoboMaster: circuito, puntería y disparo', cifra: 1.0, dec: 2, pie: 'confianza máxima al ver al rival en el laboratorio' },
];
export function Reto() {
  return (
    <div className="diapo">
      <Cabecera fase="El reto" titulo="Un robot que encuentra a sus rivales y les dispara"
        subtitulo="El RoboMaster EP recorre un circuito, detecta con su cámara a los robots rivales y los marca con su emisor de infrarrojos." />
      <div className="cuerpo dos-asim-inv" style={{ alignItems: 'center' }}>
        <motion.figure initial={{ opacity: 0, scale: 0.96, filter: 'blur(8px)' }} animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          transition={{ delay: 0.4, duration: 0.9, ease: CURVA }} style={{ margin: 0 }}>
          <img src={robotPartes} alt="Partes de un RoboMaster EP" style={{ width: '100%', borderRadius: 4, border: '1px solid var(--borde)', display: 'block' }} />
          <figcaption className="etiqueta" style={{ marginTop: 12 }}>RoboMaster EP en uno de nuestros vídeos (V03)</figcaption>
        </motion.figure>
        <div style={{ position: 'relative', paddingLeft: 44 }}>
          <svg style={{ position: 'absolute', left: 10, top: 18, height: 'calc(100% - 36px)', width: 4, overflow: 'visible' }} aria-hidden>
            <motion.line x1="2" x2="2" y1="0" y2="100%" stroke="var(--acento)" strokeWidth="2"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.5, duration: 1.6, ease: 'easeInOut' }} />
          </svg>
          <div style={{ display: 'grid', gap: 26 }}>
            {FASES_RETO.map((f, i) => (
              <motion.div key={f.n} className="panel" style={{ position: 'relative' }}
                initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.45, duration: 0.7, ease: CURVA }}>
                <motion.span style={{ position: 'absolute', left: -43, top: 30, width: 16, height: 16, background: 'var(--fondo)',
                  border: '2px solid var(--acento)', borderRadius: '50%' }}
                  initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.6 + i * 0.45, type: 'spring', stiffness: 400, damping: 14 }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 20 }}>
                  <h3><span className="mono acento" style={{ marginRight: 14 }}>{f.n}</span>{f.nombre}</h3>
                  <span className="cifra peque acento"><Contador valor={f.cifra} dec={f.dec || 0} retraso={0.8 + i * 0.45} /></span>
                </div>
                <p>{f.que}</p>
                <p className="mono" style={{ fontSize: 15, marginTop: 8, color: 'var(--tenue)' }}>{f.pie}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// --- 3. Cómo nos organizamos ----------------------------------------------------------------------
const FLUJO = ['Rama personal', 'Pull request', 'Revisión de otro integrante', 'main'];
export function Equipo() {
  return (
    <div className="diapo">
      <Cabecera fase="El equipo" titulo="Cinco personas, criterios comunes y todo revisado por otro"
        subtitulo="Cada integrante anotó dos vídeos y revisó los de otro. El código, la memoria y la web viven en un repositorio con pull requests." />
      <Revela className="cuerpo" style={{ gridTemplateColumns: 'repeat(5, 1fr)', gap: 18, flex: 'none' }} retraso={0.35} paso={0.1}>
        {EQUIPO.map((p) => (
          <Item key={p.nombre} className="panel" style={{ textAlign: 'center', padding: '28px 18px' }}>
            <div style={{ width: 84, height: 84, margin: '0 auto 16px', borderRadius: '50%', border: '2px solid var(--acento)',
              display: 'grid', placeItems: 'center', font: '400 34px/1 var(--pixel)', color: 'var(--acento)' }}>{p.lote}</div>
            <div style={{ fontSize: 22, fontWeight: 600 }}>{p.nombre}</div>
            <div className="mono" style={{ fontSize: 15, color: 'var(--tenue)', marginTop: 6 }}>Lote {p.lote} · vídeos {p.videos}</div>
          </Item>
        ))}
      </Revela>
      <div style={{ marginTop: 44, display: 'flex', alignItems: 'center', gap: 0 }}>
        {FLUJO.map((paso, i) => (
          <div key={paso} style={{ display: 'flex', alignItems: 'center', flex: i < FLUJO.length - 1 ? 1 : 'none' }}>
            <motion.span className={`chip${i === FLUJO.length - 1 ? ' on' : ''}`} style={{ fontSize: 18, padding: '12px 18px' }}
              initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.1 + i * 0.35, duration: 0.4 }}>
              {paso}
            </motion.span>
            {i < FLUJO.length - 1 && (
              <svg height="14" style={{ flex: 1, margin: '0 10px' }} aria-hidden>
                <motion.line x1="0" x2="100%" y1="7" y2="7" stroke="var(--acento)" strokeWidth="2" strokeDasharray="5 6"
                  initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.25 + i * 0.35, duration: 0.4 }} />
              </svg>
            )}
          </div>
        ))}
      </div>
      <Revela style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, marginTop: 34 }} retraso={2.4} paso={0.12}>
        {[
          ['Criterios comunes', 'Calibración: los cinco anotamos las mismas 20 imágenes difíciles; IoU medio de 0,81.'],
          ['Todo se revisa', 'Cada lote y cada cambio de código pasa por la revisión de otro integrante antes de main.'],
          ['Resultados abiertos', 'Memoria, notebooks y una web con las gráficas interactivas de los bloques 1 y 2.'],
        ].map(([t, d]) => (
          <Item key={t} className="panel" style={{ padding: '20px 24px' }}><h3 style={{ fontSize: 22 }}>{t}</h3><p style={{ fontSize: 19 }}>{d}</p></Item>
        ))}
      </Revela>
    </div>
  );
}
