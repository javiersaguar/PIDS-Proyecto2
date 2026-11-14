import { motion } from 'framer-motion';
import { Contador, CURVA } from './base.jsx';

const COLORES = { robot: 'var(--acento)', difficult: 'var(--naranja)', rival: 'var(--rojo)' };

// «Fijar»: las cuatro esquinas de la caja de detección se enganchan alrededor de lo importante.
// <Esquinas> se coloca dentro de un elemento con position: relative; <Fijar> envuelve a su contenido.
export function Esquinas({ retraso = 0, color = 'var(--acento)', tam = 14, grosor = 2.5, desde = 1.25, style }) {
  return (
    <motion.div aria-hidden className="fijar" style={{ inset: -6, color, '--t': `${tam}px`, '--g': `${grosor}px`, ...style }}
      initial={{ opacity: 0, scale: desde }} animate={{ opacity: [0, 1, 0.5, 1], scale: 1 }}
      transition={{ delay: retraso, duration: 0.45, ease: CURVA, opacity: { delay: retraso, duration: 0.4, times: [0, 0.4, 0.6, 1] } }}>
      <i className="a" /><i className="b" /><i className="c" /><i className="d" />
    </motion.div>
  );
}
export function Fijar({ children, retraso, color, margen = 6, className, style }) {
  return (
    <div className={className} style={{ position: 'relative', ...style }}>
      {children}
      <Esquinas retraso={retraso} color={color} style={{ inset: -margen }} />
    </div>
  );
}

// Línea de escaneo que pasa una vez sobre una foto (el contenedor necesita position: relative y overflow: hidden)
export function Barrido({ retraso = 0.4, duracion = 0.8, alto = 64 }) {
  return (
    <motion.div aria-hidden className="escaneo" style={{ height: alto }} initial={{ top: '-45%' }} animate={{ top: '115%' }}
      transition={{ delay: retraso, duration: duracion, ease: 'linear' }} />
  );
}

// Caja de detección con esquinas: se «engancha» al robot (escala desde 1,35) y después aparece su rótulo.
// Con «trazo», se dibuja de una esquina a la opuesta, como en la herramienta de anotación, y se engancha al soltarla.
export function Caja({ caja, retraso = 0, tipo = 'robot', rotulo, confianza, mostrarRotulo = true, trazo = false, duracionTrazo = 0.26 }) {
  const color = COLORES[tipo] || tipo;
  const discontinua = tipo === 'difficult';
  if (trazo) {
    const fin = retraso + duracionTrazo;
    return (
      <div className={`caja${discontinua ? ' discontinua' : ''}`}
        style={{ left: `${caja.x * 100}%`, top: `${caja.y * 100}%`, width: `${caja.w * 100}%`, height: `${caja.h * 100}%`, color, '--c': color }}>
        <motion.div style={{ position: 'absolute', inset: 0 }} initial={{ clipPath: 'inset(0% 100% 100% 0%)' }} animate={{ clipPath: 'inset(0% 0% 0% 0%)' }}
          transition={{ delay: retraso, duration: duracionTrazo, ease: 'easeInOut' }}>
          <motion.div className="relleno" initial={{ opacity: 0.3 }} animate={{ opacity: 0.08 }} transition={{ delay: fin, duration: 0.5 }} />
          <div className="marco-caja" />
        </motion.div>
        <motion.div style={{ position: 'absolute', inset: 0 }} initial={{ opacity: 0, scale: 1.22 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: fin, duration: 0.24, ease: CURVA }}>
          <i className="esq a" /><i className="esq b" /><i className="esq c" /><i className="esq d" />
        </motion.div>
        {mostrarRotulo && rotulo && (
          <motion.div className={`rotulo${caja.x + caja.w > 0.85 ? ' derecha' : ''}`} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: fin + 0.1, duration: 0.3 }}>
            <span>{rotulo}</span>
          </motion.div>
        )}
      </div>
    );
  }
  return (
    <motion.div
      className={`caja${discontinua ? ' discontinua' : ''}`}
      style={{ left: `${caja.x * 100}%`, top: `${caja.y * 100}%`, width: `${caja.w * 100}%`, height: `${caja.h * 100}%`, color, '--c': color }}
      initial={{ opacity: 0, scale: 1.35 }}
      animate={{ opacity: [0, 1, 0.6, 1], scale: 1 }}
      transition={{ delay: retraso, duration: 0.55, ease: CURVA, opacity: { delay: retraso, duration: 0.5, times: [0, 0.4, 0.6, 1] } }}
    >
      <motion.div className="relleno" initial={{ opacity: 0.45 }} animate={{ opacity: 0.08 }} transition={{ delay: retraso + 0.2, duration: 0.6 }} />
      <div className="marco-caja" />
      <i className="esq a" /><i className="esq b" /><i className="esq c" /><i className="esq d" />
      {mostrarRotulo && (rotulo || confianza != null) && (
        // Si la caja toca el borde derecho, el rótulo se alinea a la derecha para no salirse de la imagen
        <motion.div className={`rotulo${caja.x + caja.w > 0.85 ? ' derecha' : ''}`} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
          transition={{ delay: retraso + 0.35, duration: 0.35 }}>
          <span>{rotulo}{confianza != null && <> <Contador valor={confianza} dec={2} duracion={0.9} retraso={retraso + 0.35} /></>}</span>
        </motion.div>
      )}
    </motion.div>
  );
}

// Fotograma con sus cajas. modo: 'deteccion' (verde y confianza), 'anotacion' (normal/difficult) o 'nada'
export function Fotograma({ foto, modo = 'deteccion', retraso = 0.4, paso = 0.28, escaneo = false, className = '', style,
  confianzas, rotulos = true, children, imgStyle }) {
  return (
    <div className={`fotograma ${className}`} style={style}>
      <img src={foto.src} alt={`Fotograma ${foto.frame} de ${foto.video}`} style={imgStyle} />
      {escaneo && (
        <motion.div className="escaneo" initial={{ top: '-20%' }} animate={{ top: '110%' }}
          transition={{ delay: retraso - 0.2, duration: 1.6, ease: 'linear' }} />
      )}
      {modo !== 'nada' && foto.cajas.map((c, i) => {
        const tipo = modo === 'anotacion' && c.difficult ? 'difficult' : 'robot';
        const conf = modo === 'deteccion' ? (confianzas ? confianzas[i] : 0.99 - i * 0.02) : undefined;
        const rotulo = modo === 'anotacion' ? (c.difficult ? 'difficult' : 'robot') : 'ROBOT';
        // Con escaneo, cada caja aparece cuando la línea pasa por ella
        const r = escaneo ? retraso - 0.2 + 1.6 * ((c.y + c.h / 2) + 0.2) / 1.3 : retraso + i * paso;
        return <Caja key={i} caja={c} tipo={tipo} rotulo={rotulo} confianza={conf} retraso={r} mostrarRotulo={rotulos} />;
      })}
      {children}
    </div>
  );
}
