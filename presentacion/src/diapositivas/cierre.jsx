import { motion } from 'framer-motion';
import { CURVA } from '../componentes/base.jsx';
import { Barrido, Fotograma } from '../componentes/fotograma.jsx';
import { Letras } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { Reticula } from './inicio.jsx';
import qrPages from '../datos/qr_pages.svg';
import qrRepo from '../datos/qr_repo.svg';

// Enlaces: la web con las figuras interactivas (GitHub Pages) y el repositorio del grupo
const ENLACES = [
  { qr: qrPages, titulo: 'Figuras interactivas', texto: 'Los datos, el modelo y la demo foto a foto', url: 'javiersaguar.github.io/PIDS-Proyecto2' },
  { qr: qrRepo, titulo: 'Repositorio del grupo', texto: 'El código, los notebooks y la memoria', url: 'github.com/javiersaguar/PIDS-Proyecto2' },
];

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
          {/* Durante las preguntas, la retícula «respira» muy despacio */}
          <motion.div animate={{ scale: [1, 1.07, 1] }} transition={{ delay: 3.2, duration: 5, ease: 'easeInOut', repeat: Infinity }}>
            <Reticula tam={160} color="var(--rojo)" fijada />
          </motion.div>
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
      <motion.div initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 3.8, duration: 0.6, ease: CURVA }}
        style={{ position: 'absolute', right: 88, top: 80, width: 520, zIndex: 5, display: 'grid', gap: 14 }}>
        {ENLACES.map((e, i) => (
          <div key={e.titulo} className="panel" style={{ display: 'flex', gap: 18, alignItems: 'center', padding: 14, background: 'rgba(12,13,11,0.85)' }}>
            <div style={{ position: 'relative', overflow: 'hidden', flex: 'none', borderRadius: 3 }}>
              <img src={e.qr} alt={`Código QR: ${e.titulo}`} width="150" height="150" style={{ display: 'block' }} />
              <Barrido retraso={4.3 + i * 0.25} duracion={0.7} alto={44} />
            </div>
            <div>
              <div className="etiqueta">{e.titulo}</div>
              <div style={{ fontSize: 20, marginTop: 6, lineHeight: 1.3 }}>{e.texto}</div>
              <div className="mono" style={{ fontSize: 14, color: 'var(--suave)', marginTop: 8 }}>{e.url}</div>
            </div>
          </div>
        ))}
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
Gracias.imagenes = [FOTOGRAMAS.objetivo.src, qrPages, qrRepo];
