import { motion } from 'framer-motion';
import { Cabecera, CURVA, Item, Revela } from '../componentes/base.jsx';
import { Fotograma } from '../componentes/fotograma.jsx';
import { Letras } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { Reticula } from './inicio.jsx';

const LECCIONES = [
  { n: '01', t: 'Datos', d: 'Con criterios comunes, lo que más mejoró al detector fue el aumento, sobre todo en difficult. Marcar los difficult en validación y test mostró dónde falla.' },
  { n: '02', t: 'Modelo', d: 'La arquitectura importa más que la tasa o el perfil de aumento. Faster R-CNN v2 confirma en test lo que daba en validación; los difficult siguen muy por debajo.' },
  { n: '03', t: 'Robot', d: 'La latencia lo ha condicionado todo: parar a mirar, repartir el tiempo de cada tramo e imágenes recientes y nítidas. Para distinguir aliados hace falta una marca, no una forma.' },
];

export function Conclusiones() {
  return (
    <div className="diapo">
      <Cabecera fase="Conclusiones" titulo="Qué nos llevamos de cada fase" />
      <Revela className="cuerpo tres" retraso={0.3} paso={0.2} style={{ flex: 'none' }}>
        {LECCIONES.map((l) => (
          <Item key={l.n} className="panel" style={{ padding: '28px 30px' }}>
            <div style={{ font: '400 64px/1 var(--pixel)', color: 'var(--acento)', marginBottom: 18 }}>{l.n}</div>
            <h3 style={{ fontSize: 30 }}>{l.t}</h3>
            <p style={{ fontSize: 20 }}>{l.d}</p>
          </Item>
        ))}
      </Revela>
      <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2, duration: 0.6, ease: CURVA }}
        style={{ marginTop: 26, display: 'grid', gridTemplateColumns: '200px 1fr', alignItems: 'center', gap: 20, borderColor: 'var(--acento-oscuro)' }}>
        <span className="etiqueta acento">Trabajo futuro</span>
        <span style={{ fontSize: 21 }}>Llevar a la demo el detector en GPU del mando (unas 10 imágenes por segundo), añadir la regla de color para los aliados y grabar más robots difficult y lejanos.</span>
      </motion.div>
    </div>
  );
}

export function Gracias() {
  const f = FOTOGRAMAS.objetivo;
  const c = f.cajas.reduce((a, b) => (a.w * a.h > b.w * b.h ? a : b));
  const cx = (c.x + c.w / 2) * 100;
  const cy = (c.y + c.h / 2) * 100;
  return (
    <div className="diapo sangre" style={{ background: '#000' }}>
      <motion.div style={{ position: 'absolute', inset: 0 }} initial={{ scale: 1.15, filter: 'brightness(0.4)' }} animate={{ scale: 1, filter: 'brightness(0.75)' }}
        transition={{ duration: 2.4, ease: CURVA }}>
        <Fotograma foto={f} modo="nada" style={{ position: 'absolute', inset: 0, aspectRatio: 'auto', border: 0, borderRadius: 0 }} />
      </motion.div>
      <div className="lineas-crt" />
      {/* Degradado inferior para que el texto se lea sobre los reflejos del suelo */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: '45%', zIndex: 2, pointerEvents: 'none',
        background: 'linear-gradient(to top, rgba(12,13,11,0.92), rgba(12,13,11,0.55) 45%, transparent)' }} />
      {/* La retícula busca y se fija en el robot más cercano */}
      <motion.div style={{ position: 'absolute', marginLeft: -80, marginTop: -80, zIndex: 3 }}
        initial={{ left: '20%', top: '70%', opacity: 0 }}
        animate={{ left: ['20%', '70%', `${cx - 6}%`, `${cx}%`], top: ['70%', '30%', `${cy + 4}%`, `${cy}%`], opacity: 1 }}
        transition={{ duration: 2.2, times: [0, 0.4, 0.8, 1], ease: 'easeInOut', opacity: { duration: 0.3 } }}>
        <motion.div initial={{ scale: 1.3 }} animate={{ scale: [1.3, 1.3, 0.85] }} transition={{ duration: 2.6, times: [0, 0.85, 1] }}>
          <Reticula tam={160} color="var(--rojo)" fijada />
        </motion.div>
      </motion.div>
      <motion.div style={{ position: 'absolute', inset: 0, background: 'var(--rojo)', mixBlendMode: 'screen', zIndex: 4, pointerEvents: 'none' }}
        initial={{ opacity: 0 }} animate={{ opacity: [0, 0.55, 0, 0.3, 0] }} transition={{ delay: 2.6, duration: 0.6 }} />
      <motion.div className="caja" style={{ left: `${c.x * 100}%`, top: `${c.y * 100}%`, width: `${c.w * 100}%`, height: `${c.h * 100}%`, color: 'var(--rojo)', '--c': 'var(--rojo)', zIndex: 3 }}
        initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0.4, 1] }} transition={{ delay: 2.5, duration: 0.5 }}>
        <div className="marco-caja" />
        <i className="esq a" /><i className="esq b" /><i className="esq c" /><i className="esq d" />
        <div className="rotulo"><span>OBJETIVO FIJADO</span></div>
      </motion.div>
      <div style={{ position: 'absolute', left: 88, bottom: 84, right: 88, zIndex: 5 }}>
        <h2 style={{ margin: 0, fontSize: 150, lineHeight: 0.9, fontWeight: 700, letterSpacing: '-0.05em' }}>
          <Letras texto="Gracias" retraso={3} paso={0.05} />
        </h2>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 3.6, duration: 0.6 }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginTop: 20 }}>
          <span style={{ fontSize: 34, color: 'var(--texto)' }}>¿Preguntas?</span>
          <span className="mono" style={{ fontSize: 17, color: 'var(--texto)' }}>github.com/javiersaguar/PIDS-Proyecto2 · Grupo 2 · PIDS 2026</span>
        </motion.div>
      </div>
    </div>
  );
}
