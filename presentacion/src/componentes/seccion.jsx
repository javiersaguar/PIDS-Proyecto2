import { motion } from 'framer-motion';
import { CURVA } from './base.jsx';

// Texto que entra letra a letra desde abajo, recortado por su línea
export function Letras({ texto, retraso = 0, paso = 0.035, className, style }) {
  return (
    <span className={className} style={{ display: 'inline-block', overflow: 'hidden', paddingBottom: '0.08em', verticalAlign: 'bottom', ...style }}
      aria-label={texto}>
      {[...texto].map((c, i) => (
        <motion.span key={i} aria-hidden style={{ display: 'inline-block', whiteSpace: 'pre' }}
          initial={{ y: '110%' }} animate={{ y: '0%' }} transition={{ delay: retraso + i * paso, duration: 0.7, ease: CURVA }}>
          {c}
        </motion.span>
      ))}
    </span>
  );
}

// Texto que se escribe como en un terminal
export function Tipeo({ texto, retraso = 0, duracion = 1, className, style }) {
  const n = texto.length;
  return (
    <motion.span className={className} style={{ display: 'inline-block', whiteSpace: 'nowrap', ...style }}
      initial={{ clipPath: 'inset(0 100% 0 0)' }} animate={{ clipPath: 'inset(0 0% 0 0)' }}
      transition={{ delay: retraso, duration: duracion, ease: (t) => Math.floor(t * n) / n }}>
      {texto}
    </motion.span>
  );
}

// Separador de fase: cortina verde, número gigante, título letra a letra y fotogramas en movimiento
export function Seccion({ numero, titulo, lema, puntos = [], fotos = [], color = 'var(--acento)' }) {
  const cinta = [...fotos, ...fotos];
  return (
    <div className="diapo" style={{ justifyContent: 'center' }}>
      {fotos.length > 0 && (
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 70, height: 210, overflow: 'hidden', opacity: 0.5,
          maskImage: 'linear-gradient(90deg, transparent, #000 15%, #000 85%, transparent)' }}>
          <motion.div style={{ display: 'flex', gap: 16, width: 'max-content' }} animate={{ x: ['0%', '-50%'] }}
            transition={{ duration: 46, ease: 'linear', repeat: Infinity }}>
            {cinta.map((f, i) => (
              <img key={i} src={f.src || f} alt="" style={{ height: 210, aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: 3,
                filter: 'saturate(0.6) brightness(0.8)', border: '1px solid var(--borde)' }} />
            ))}
          </motion.div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', alignItems: 'end', gap: 64, marginTop: -150, position: 'relative' }}>
        <motion.div style={{ font: '400 330px/0.8 var(--pixel)', color, WebkitTextStroke: `2px ${color}`, overflow: 'hidden', paddingTop: 20 }}
          initial={{ color: 'rgba(0,0,0,0)' }} animate={{ color: [null, 'rgba(0,0,0,0)', color] }}
          transition={{ delay: 0.5, duration: 1.4, times: [0, 0.5, 1] }}>
          <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} transition={{ delay: 0.45, duration: 0.9, ease: CURVA }}>{numero}</motion.div>
        </motion.div>
        <div style={{ paddingBottom: 18 }}>
          <motion.div className="fase" initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.8, duration: 0.5 }}>
            Fase {numero}
          </motion.div>
          <h2 style={{ margin: '10px 0 0', fontSize: 132, lineHeight: 0.95, fontWeight: 700, letterSpacing: '-0.045em' }}>
            <Letras texto={titulo} retraso={0.7} paso={0.04} />
          </h2>
          {lema && (
            <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2, duration: 0.6 }}
              style={{ margin: '18px 0 0', fontSize: 28, color: 'var(--suave)', maxWidth: 820 }}>
              {lema}
            </motion.p>
          )}
          {puntos.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 26 }}>
              {puntos.map((p, i) => (
                <motion.span key={p} className="chip" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.4 + i * 0.08, duration: 0.45 }}>{p}</motion.span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cortina: cruza la pantalla y descubre la fase */}
      <motion.div aria-hidden style={{ position: 'absolute', inset: 0, background: color, zIndex: 10 }}
        initial={{ clipPath: 'inset(0 100% 0 0)' }}
        animate={{ clipPath: ['inset(0 100% 0 0)', 'inset(0 0% 0 0)', 'inset(0 0% 0 100%)'] }}
        transition={{ duration: 1.05, times: [0, 0.42, 1], ease: [0.76, 0, 0.24, 1] }} />
      <motion.div aria-hidden style={{ position: 'absolute', left: 0, right: 0, height: 2, background: color, zIndex: 9, boxShadow: `0 0 18px ${color}` }}
        initial={{ top: '0%', opacity: 0 }} animate={{ top: ['0%', '100%'], opacity: [0, 1, 0] }} transition={{ delay: 0.9, duration: 1.2, ease: 'easeInOut' }} />
    </div>
  );
}
