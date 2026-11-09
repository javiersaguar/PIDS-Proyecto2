import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { AnimatePresence, MotionConfig, motion } from 'framer-motion';
import { DIAPOSITIVAS, FASES } from './diapositivas/index.js';

const ANCHO = 1600;
const ALTO = 900;

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

const transiciones = {
  normal: {
    initial: { opacity: 0, y: 26, filter: 'blur(10px)' },
    animate: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
    exit: { opacity: 0, y: -18, filter: 'blur(8px)', transition: { duration: 0.32, ease: 'easeIn' } },
  },
  // Las portadas y separadores hacen su propia entrada llamativa
  propia: {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: 0, scale: 1.04, filter: 'blur(10px)', transition: { duration: 0.35, ease: 'easeIn' } },
  },
};

export default function App() {
  const [indice, setIndice] = useState(leerHash);
  const [paso, setPaso] = useState(0);
  const [verIndice, setVerIndice] = useState(false);
  const [verNotas, setVerNotas] = useState(false);
  const escala = useEscala();
  const diapo = DIAPOSITIVAS[indice];
  const pasos = diapo.pasos || 0;
  const ultimoToque = useRef(0);

  const ir = useCallback((i, alFinal = false) => {
    const n = Math.min(Math.max(i, 0), DIAPOSITIVAS.length - 1);
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
      else if (k === 'f' || k === 'F') {
        if (document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen?.();
      }
    };
    const hash = () => ir(leerHash());
    window.addEventListener('keydown', tecla);
    window.addEventListener('hashchange', hash);
    return () => { window.removeEventListener('keydown', tecla); window.removeEventListener('hashchange', hash); };
  }, [siguiente, anterior, ir, indice]);

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
  const tipo = diapo.tipo === 'seccion' || diapo.tipo === 'portada' ? 'propia' : 'normal';
  const fase = FASES[diapo.fase];

  return (
    <MotionConfig reducedMotion="user">
      <div className="marco" onClick={clic}>
        <div className="escenario" style={{ transform: `translate(-50%, -50%) scale(${escala})` }}>
          <AnimatePresence mode="wait">
            <motion.div key={diapo.id} style={{ position: 'absolute', inset: 0 }} {...transiciones[tipo]}>
              <Componente paso={paso} />
            </motion.div>
          </AnimatePresence>

          {diapo.tipo !== 'portada' && (
            <div className="barra">
              <span>{fase.nombre}</span>
              <div className="progreso">
                {FASES.map((f, i) => {
                  const del = DIAPOSITIVAS.map((d, j) => [d, j]).filter(([d]) => d.fase === i);
                  const hechas = del.filter(([, j]) => j <= indice).length;
                  return (
                    <div key={f.nombre} className="tramo" style={{ '--n': del.length }}>
                      <motion.i initial={false} animate={{ scaleX: del.length ? hechas / del.length : 0 }}
                        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} />
                    </div>
                  );
                })}
              </div>
              <span className="contador">{String(indice + 1).padStart(2, '0')} / {DIAPOSITIVAS.length}</span>
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
