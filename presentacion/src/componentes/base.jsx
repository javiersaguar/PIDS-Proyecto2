import { useEffect, useRef } from 'react';
import { animate, motion, useInView, useReducedMotion } from 'framer-motion';

export const CURVA = [0.22, 1, 0.36, 1];

// Número con coma decimal y, desde 10 000, espacio fino entre miles (como en la memoria)
export function fmt(v, dec = 0) {
  const [entera, decimales] = Math.abs(v).toFixed(dec).split('.');
  const miles = Math.abs(v) >= 10000 ? entera.replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : entera;
  return (v < 0 ? '−' : '') + miles + (decimales ? `,${decimales}` : '');
}

// Cuenta hasta «valor» al aparecer
export function Contador({ valor, dec = 0, duracion = 1.6, retraso = 0, desde = 0, prefijo = '', sufijo = '', className }) {
  const ref = useRef(null);
  const visto = useInView(ref, { once: true });
  const reducido = useReducedMotion();
  useEffect(() => {
    if (!visto || !ref.current) return undefined;
    if (reducido) {
      ref.current.textContent = prefijo + fmt(valor, dec) + sufijo;
      return undefined;
    }
    const control = animate(desde, valor, {
      duration: duracion, delay: retraso, ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => { if (ref.current) ref.current.textContent = prefijo + fmt(v, dec) + sufijo; },
    });
    return () => control.stop();
  }, [visto, valor, dec, duracion, retraso, desde, prefijo, sufijo, reducido]);
  return <span ref={ref} className={className}>{prefijo + fmt(desde, dec) + sufijo}</span>;
}

// Entrada suave en cascada: <Revela> envuelve y cada <Item> aparece después del anterior
const contenedor = (retraso, paso) => ({
  oculto: {},
  visible: { transition: { delayChildren: retraso, staggerChildren: paso } },
});
export const itemSuave = {
  oculto: { opacity: 0, y: 22, filter: 'blur(6px)' },
  visible: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.7, ease: CURVA } },
};
export function Revela({ children, retraso = 0.15, paso = 0.09, className, style, as = 'div' }) {
  const M = motion[as];
  return (
    <M className={className} style={style} variants={contenedor(retraso, paso)} initial="oculto" animate="visible">
      {children}
    </M>
  );
}
export function Item({ children, className, style, as = 'div', variants = itemSuave }) {
  const M = motion[as];
  return <M className={className} style={style} variants={variants}>{children}</M>;
}

// Aparece cuando el presentador llega al paso «desde» (fragmentos)
export function Paso({ paso, desde, children, className, style, y = 18 }) {
  return (
    <motion.div className={className} style={style} initial={false}
      animate={paso >= desde ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y, filter: 'blur(4px)' }}
      transition={{ duration: 0.6, ease: CURVA }}>
      {children}
    </motion.div>
  );
}

export function Cabecera({ fase, titulo, subtitulo }) {
  return (
    <Revela className="cabecera" retraso={0.05} paso={0.08}>
      {fase && <Item className="fase">{fase}</Item>}
      <Item as="h2" className="titulo">{titulo}</Item>
      {subtitulo && <Item as="p" className="subtitulo">{subtitulo}</Item>}
    </Revela>
  );
}
