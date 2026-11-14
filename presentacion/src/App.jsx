import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { AnimatePresence, MotionConfig, motion, useReducedMotion } from 'framer-motion';
import { DIAPOSITIVAS, FASES } from './diapositivas/index.js';

const ANCHO = 1600;
const ALTO = 900;
const CURVA = [0.22, 1, 0.36, 1];

function leerHash() {
  const n = parseInt(window.location.hash.replace('#', ''), 10);
  return Number.isFinite(n) ? Math.min(Math.max(n - 1, 0), DIAPOSITIVAS.length - 1) : 0;
}

// Escala el escenario de 1600 × 900 para que quepa en la ventana sin deformarse
function useEscala() {
  const [escala, setEscala] = useState(1);
  useLayoutEffect(() => {
    const ajustar = () => setEscala(Math.min(window.innerWidth / ANCHO, window.innerHeight / ALTO));
    ajustar();
    window.addEventListener('resize', ajustar);
    return () => window.removeEventListener('resize', ajustar);
  }, []);
  return escala;
}

// Cambio de diapositiva como un corte de cámara: sin desenfoques, 0,55 s entre salir y entrar.
const transiciones = {
  normal: {
    initial: { opacity: 0, y: 14 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.37, ease: CURVA } },
    exit: { opacity: 0, transition: { duration: 0.18, ease: 'easeIn' } },
  },
  // Las portadas hacen su propia entrada llamativa
  portada: {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: 0, scale: 1.03, transition: { duration: 0.3, ease: 'easeIn' } },
  },
  // Las portadas de fase salen tapadas por la cortina de su color (ver «efecto»)
  seccion: {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: [1, 1, 0], transition: { duration: 0.32, times: [0, 0.94, 1] } },
  },
};

export default function App() {
  const [indice, setIndice] = useState(leerHash);
  const [paso, setPaso] = useState(0);
  const [verIndice, setVerIndice] = useState(false);
  const [verNotas, setVerNotas] = useState(false);
  const [efecto, setEfecto] = useState(null);     // línea de corte o cortina entre dos diapositivas
  const [repeticion, setRepeticion] = useState(0);
  const escala = useEscala();
  const reducido = useReducedMotion();
  const diapo = DIAPOSITIVAS[indice];
  const pasos = diapo.pasos || 0;
  const ultimoToque = useRef(0);
  const actual = useRef(indice);

  const ir = useCallback((i, alFinal = false) => {
    const n = Math.min(Math.max(i, 0), DIAPOSITIVAS.length - 1);
    const de = DIAPOSITIVAS[actual.current];
    if (n !== actual.current) {
      setEfecto((e) => {
        const k = (e?.n || 0) + 1;
        if (de.tipo === 'seccion') return { n: k, tipo: 'cortina', color: de.color || 'var(--acento)' };
        return DIAPOSITIVAS[n].tipo ? { n: k, tipo: null } : { n: k, tipo: 'corte' };
      });
    }
    actual.current = n;
    setIndice(n);
    setPaso(alFinal ? DIAPOSITIVAS[n].pasos || 0 : 0);
    window.history.replaceState(null, '', `#${n + 1}`);
  }, []);
  const siguiente = useCallback(() => {
    if (paso < pasos) setPaso(paso + 1);
    else ir(indice + 1);
  }, [paso, pasos, indice, ir]);
  const anterior = useCallback(() => {
    if (paso > 0) setPaso(paso - 1);
    else ir(indice - 1, true);
  }, [paso, indice, ir]);

  useEffect(() => {
    const tecla = (e) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      const k = e.key;
      if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); siguiente(); }
      else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); anterior(); }
      else if (k === 'ArrowDown') { e.preventDefault(); ir(indice + 1); }
      else if (k === 'ArrowUp') { e.preventDefault(); ir(indice - 1); }
      else if (k === 'Home') ir(0);
      else if (k === 'End') ir(DIAPOSITIVAS.length - 1);
      else if (k === 'g' || k === 'G' || k === 'Escape') setVerIndice((v) => (k === 'Escape' ? false : !v));
      else if (k === 'n' || k === 'N') setVerNotas((v) => !v);
      else if (k === 'r' || k === 'R') setRepeticion((v) => v + 1);
      else if (k === 'f' || k === 'F') {
        if (document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen?.();
      }
    };
    const hash = () => ir(leerHash());
    // La página de comparación (comparar.html) pide repetir la entrada de la diapositiva
    const mensaje = (e) => { if (e.data === 'pids:repetir') setRepeticion((v) => v + 1); };
    window.addEventListener('keydown', tecla);
    window.addEventListener('hashchange', hash);
    window.addEventListener('message', mensaje);
    return () => {
      window.removeEventListener('keydown', tecla);
      window.removeEventListener('hashchange', hash);
      window.removeEventListener('message', mensaje);
    };
  }, [siguiente, anterior, ir, indice]);

  // Descarga y decodifica por adelantado las imágenes de la diapositiva siguiente
  useEffect(() => {
    const urls = DIAPOSITIVAS[indice + 1]?.Componente.imagenes;
    if (!urls) return undefined;
    const id = setTimeout(() => urls.forEach((u) => {
      const img = new Image();
      img.src = u;
      img.decode?.().catch(() => {});
    }), 500);
    return () => clearTimeout(id);
  }, [indice]);

  // Clic: mitad derecha avanza, izquierda retrocede (sin dobles avances por toques rápidos)
  const clic = (e) => {
    if (verIndice || e.target.closest('button, a')) return;
    const ahora = performance.now();
    if (ahora - ultimoToque.current < 250) return;
    ultimoToque.current = ahora;
    const caja = e.currentTarget.getBoundingClientRect();
    if (e.clientX - caja.left > caja.width * 0.3) siguiente();
    else anterior();
  };

  const Componente = diapo.Componente;
  const fase = FASES[diapo.fase];

  return (
    <MotionConfig reducedMotion="user">
      <div className="marco" onClick={clic}>
        <div className="escenario" style={{ transform: `translate(-50%, -50%) scale(${escala})` }}>
          <AnimatePresence key={`rep-${repeticion}`} mode="wait">
            <motion.div key={diapo.id} style={{ position: 'absolute', inset: 0 }} {...transiciones[diapo.tipo || 'normal']}>
              <Componente paso={paso} />
            </motion.div>
          </AnimatePresence>

          {/* Línea verde que barre la pantalla en cada corte */}
          {!reducido && efecto?.tipo === 'corte' && (
            <motion.div key={`corte-${efecto.n}`} aria-hidden className="corte" initial={{ y: -12, opacity: 1 }} animate={{ y: ALTO + 12, opacity: [1, 1, 0] }}
              transition={{ duration: 0.55, ease: [0.5, 0, 0.3, 1], opacity: { duration: 0.55, times: [0, 0.85, 1] } }} />
          )}
          {/* Al salir de una portada de fase, la cortina vuelve a cruzar y descubre la diapositiva siguiente */}
          {!reducido && efecto?.tipo === 'cortina' && (
            <motion.div key={`cortina-${efecto.n}`} aria-hidden style={{ position: 'absolute', inset: 0, zIndex: 15, background: efecto.color, pointerEvents: 'none' }}
              initial={{ clipPath: 'inset(0 100% 0 0)' }}
              animate={{ clipPath: ['inset(0 100% 0 0)', 'inset(0 0% 0 0)', 'inset(0 0% 0 100%)'] }}
              transition={{ duration: 0.74, times: [0, 0.42, 1], ease: [0.76, 0, 0.24, 1] }} />
          )}

          {diapo.tipo !== 'portada' && (
            <div className="barra">
              <span className="nombre-fase">
                <AnimatePresence mode="wait" initial={false}>
                  <motion.span key={fase.nombre} initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -10, opacity: 0 }}
                    transition={{ duration: 0.16, ease: 'easeOut' }}>{fase.nombre}</motion.span>
                </AnimatePresence>
              </span>
              <div className="progreso">
                {FASES.map((f, i) => {
                  const del = DIAPOSITIVAS.map((d, j) => [d, j]).filter(([d]) => d.fase === i);
                  const hechas = del.filter(([, j]) => j <= indice).length;
                  const fraccion = del.length ? hechas / del.length : 0;
                  return (
                    <div key={f.nombre} className="tramo" style={{ '--n': del.length }}>
                      <div className="pista">
                        <motion.i initial={false} animate={{ scaleX: fraccion }} transition={{ duration: 0.5, ease: CURVA }} />
                      </div>
                      {diapo.fase === i && (
                        <motion.b className="punto" initial={false} animate={{ left: `${fraccion * 100}%` }} transition={{ duration: 0.5, ease: CURVA }} />
                      )}
                    </div>
                  );
                })}
              </div>
              <span className="contador">
                <AnimatePresence mode="wait" initial={false}>
                  <motion.span key={indice} initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -8, opacity: 0 }}
                    transition={{ duration: 0.13, ease: 'easeOut' }}>{String(indice + 1).padStart(2, '0')}</motion.span>
                </AnimatePresence>
                {' '}/ {DIAPOSITIVAS.length}
              </span>
            </div>
          )}

          <AnimatePresence>
            {verNotas && (
              <motion.div className="notas" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}>
                <span className="etiqueta">Notas · {diapo.titulo}</span>
                {diapo.notas || 'Sin notas.'}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {verIndice && (
              <motion.div className="indice" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <h2>Índice</h2>
                {DIAPOSITIVAS.map((d, i) => (
                  <button key={d.id} type="button" className={i === indice ? 'actual' : ''}
                    onClick={() => { ir(i); setVerIndice(false); }}>
                    <small>{String(i + 1).padStart(2, '0')} · {FASES[d.fase].nombre}</small>{d.titulo}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </MotionConfig>
  );
}
