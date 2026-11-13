import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Cabecera, Contador, CURVA, fmt, Item, Revela } from '../componentes/base.jsx';
import { Caja, Fotograma } from '../componentes/fotograma.jsx';
import { BarrasH } from '../componentes/graficas.jsx';
import { Seccion } from '../componentes/seccion.jsx';
import { FOTOGRAMAS } from '../datos/fotogramas.js';
import { ANOTACION, CRITERIOS, DATASET, INTERVALOS, RECOGIDA } from '../datos/cifras.js';
import generados from '../datos/generados.json';

const F = FOTOGRAMAS;
export const VIDEOS = [F.v01, F.v02, F.v03, F.v04, F.v05, F.v06, F.v07, F.v08, F.v09, F.v10];

// --- Separador ---------------------------------------------------------------------------------
export function Seccion1() {
  return (
    <Seccion numero="01" titulo="Datos" fotos={VIDEOS}
      lema="Antes de entrenar, grabamos nuestros vídeos, decidimos qué es un robot y analizamos los datos."
      puntos={['10 vídeos', '808 imágenes', '1420 robots', 'análisis exploratorio', 'aumento ×4']} />
  );
}

// --- Recogida -----------------------------------------------------------------------------------
const EMBUDO = [
  { v: RECOGIDA.videos, t: 'vídeos grabados con el RoboMaster', d: '1280 × 720 · 30 fps · interior y exterior' },
  { v: RECOGIDA.segundos, dec: 1, t: 'segundos de grabación', d: 'vestíbulo, aulas, pasillo y exterior' },
  { v: RECOGIDA.fotogramas, t: 'fotogramas', d: 'de uno al siguiente (1/30 s) casi no cambia nada' },
  { v: RECOGIDA.imagenes, t: 'imágenes para anotar', d: 'una de cada 24 fotogramas (0,79 s)', acento: true },
];
export function Recogida() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Recolección" titulo="Las imágenes con las que entrenamos" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 10 }}>
          {EMBUDO.map((e, i) => (
            <motion.div key={e.t} initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.35 + i * 0.4, duration: 0.6, ease: CURVA }}
              style={{ display: 'grid', gridTemplateColumns: '250px 1fr', alignItems: 'center', gap: 22, padding: '14px 0',
                borderBottom: i < EMBUDO.length - 1 ? '1px dashed var(--borde)' : 'none',
                marginLeft: i * 26 }}>
              <span className={`cifra media${e.acento ? ' acento' : ''}`} style={{ textAlign: 'right' }}>
                <Contador valor={e.v} dec={e.dec || 0} retraso={0.35 + i * 0.4} duracion={1.2} />
              </span>
              <div>
                <div style={{ fontSize: 23, fontWeight: 600 }}>{e.t}</div>
                <div style={{ fontSize: 18, color: 'var(--suave)' }}>{e.d}</div>
              </div>
            </motion.div>
          ))}
        </div>
        <div className="panel">
          <div className="etiqueta" style={{ marginBottom: 6 }}>¿Cada cuántos fotogramas guardamos una imagen?</div>
          <p style={{ fontSize: 18, marginBottom: 22 }}>Porcentaje de imágenes casi iguales a la anterior según el intervalo elegido.</p>
          <BarrasH anchoEtiqueta={210} max={12} dec={1} retraso={0.9} paso={0.14} alto={44}
            datos={INTERVALOS.map((d) => ({ etiqueta: `cada ${d.intervalo} · ${fmt(d.imagenes)} img`, valor: d.duplicadas,
              texto: `${fmt(d.duplicadas, 1)} %`, destacado: d.intervalo === 24 }))} />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.2 }}
            style={{ marginTop: 22, fontSize: 19, color: 'var(--texto)' }}>
            Con una de cada <span className="acento mono">24</span> casi no hay repetidas (1,4 %) y quedan unos 1420 robots: una cantidad razonable para anotar entre cinco.
          </motion.p>
        </div>
      </div>
    </div>
  );
}

// --- Anotación ----------------------------------------------------------------------------------
// Uso del campo difficult: train.ipynb lo lee pero entrena con todos; test.ipynb mide aparte (como PASCAL VOC).
const DIFFICULT_USO = [
  ['Entrenan igual', 'Ni los quitamos ni les bajamos el peso: si no, la red aprendería que esos robots son fondo.'],
  ['Métricas aparte', 'AP de todos, solo normales y solo difficult. Modelo final: 0,966 frente a 0,692.'],
  ['Guían las decisiones', 'El aumento sube su AP de 0,55 a 0,63, y a igual AP elegimos el mejor en difficult.'],
];
export function Anotacion() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Anotación" titulo="Qué consideramos un robot" />
      <div className="cuerpo dos-asim">
        <div>
          <Fotograma foto={F.anotacion} modo="anotacion" retraso={0.6} paso={0.35} />
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }}
            className="mono" style={{ display: 'flex', gap: 28, marginTop: 14, fontSize: 16, color: 'var(--suave)' }}>
            <span><span style={{ display: 'inline-block', width: 26, height: 0, borderTop: '3px solid var(--acento)', verticalAlign: 'middle', marginRight: 8 }} />robot</span>
            <span><span style={{ display: 'inline-block', width: 26, height: 0, borderTop: '3px dashed var(--naranja)', verticalAlign: 'middle', marginRight: 8 }} />difficult: cortado por el borde</span>
            <span style={{ marginLeft: 'auto' }}>V04 · exterior · fotograma 1416</span>
          </motion.div>
          <Revela className="panel" retraso={2.1} paso={0.18} style={{ marginTop: 18, padding: '16px 22px' }}>
            <Item className="etiqueta" style={{ marginBottom: 10, color: 'var(--naranja)' }}>Para qué marcamos los difficult</Item>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 22 }}>
              {DIFFICULT_USO.map(([t, d]) => (
                <Item key={t}>
                  <b style={{ fontSize: 18 }}>{t}</b>
                  <p style={{ margin: '4px 0 0', fontSize: 16, lineHeight: 1.35, color: 'var(--suave)' }}>{d}</p>
                </Item>
              ))}
            </div>
          </Revela>
        </div>
        <div style={{ display: 'grid', gap: 20, alignContent: 'start' }}>
          <Revela className="panel" retraso={0.5} paso={0.1} style={{ padding: '22px 26px' }}>
            <Item className="etiqueta" style={{ marginBottom: 6 }}>Reglas que fijamos por escrito antes de anotar</Item>
            {CRITERIOS.map(([t, d]) => (
              <Item key={t} style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: 14, padding: '7px 0', fontSize: 19 }}>
                <span className="mono acento" style={{ fontSize: 16, paddingTop: 2 }}>{t}</span>
                <span className="suave">{d}</span>
              </Item>
            ))}
          </Revela>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.3 }}>
              <div className="cifra peque"><Contador valor={ANOTACION.robots} retraso={1.3} /></div>
              <div className="cifra-pie">robots anotados, <Contador valor={ANOTACION.difficult} retraso={1.4} /> de ellos difficult (26,4 %), y 41 imágenes sin robots</div>
            </motion.div>
            <motion.div className="panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.5 }}>
              <div className="cifra peque acento"><Contador valor={ANOTACION.iouAnotadores} dec={2} retraso={1.5} /></div>
              <div className="cifra-pie">coincidencia media (IoU) de nuestras cajas en las mismas 20 imágenes difíciles</div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- EDA ------------------------------------------------------------------------------------------
function BarrasVideos() {
  const datos = generados.videos;
  const max = 200;
  const alto = 330;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${datos.length}, 1fr)`, gap: 12, alignItems: 'end', height: alto + 60 }}>
      {datos.map((v, i) => {
        const normales = v.robots - v.difficult;
        return (
          <div key={v.video} style={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', height: '100%', justifyContent: 'flex-end' }}>
            <motion.div className="mono" style={{ textAlign: 'center', fontSize: 16, fontWeight: 600, marginBottom: 6 }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 + i * 0.07 }}>{v.robots}</motion.div>
            <motion.div style={{ display: 'flex', flexDirection: 'column', gap: 2, transformOrigin: 'bottom' }}
              initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: 0.4 + i * 0.07, duration: 0.9, ease: CURVA }}>
              <div style={{ height: (v.difficult / max) * alto, background: 'var(--naranja)', borderRadius: '4px 4px 0 0' }} />
              <div style={{ height: (normales / max) * alto, background: '#4f5a49' }} />
            </motion.div>
            <div className="mono" style={{ textAlign: 'center', fontSize: 15, color: 'var(--suave)', marginTop: 8 }}>{v.video}</div>
          </div>
        );
      })}
    </div>
  );
}
const DOMINIO = [
  ['Robots por imagen', '1,76', '2,32', '2,40'],
  ['Robots difficult', '26,4 %', '16,3 %', '15,7 %'],
  ['Robots de menos de 50 px', '3,9 %', '11,3 %', '9,1 %'],
  ['Imágenes exteriores', '26,4 %', '19,9 %', '1,1 %'],
];
export function Eda() {
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Análisis exploratorio" titulo="Nuestros vídeos vs. los de la asignatura" />
      <div className="cuerpo dos" style={{ alignItems: 'start' }}>
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span className="etiqueta">Robots anotados por vídeo</span>
            <span className="mono" style={{ fontSize: 14, color: 'var(--suave)', display: 'flex', gap: 16 }}>
              <span><i style={{ display: 'inline-block', width: 12, height: 12, background: '#4f5a49', marginRight: 6 }} />normales</span>
              <span><i style={{ display: 'inline-block', width: 12, height: 12, background: 'var(--naranja)', marginRight: 6 }} />difficult</span>
            </span>
          </div>
          <BarrasVideos />
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }} style={{ marginTop: 14, fontSize: 18 }}>
            Cada vídeo tiene una cantidad distinta de robots difíciles (de 17 en V04 a 65 en V08), así que medimos aparte cómo los detecta el modelo.
          </motion.p>
        </div>
        <div className="panel">
          <div className="etiqueta" style={{ marginBottom: 18 }}>Nuestros vídeos frente a los de la asignatura</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr repeat(3, 1fr)', rowGap: 4, fontSize: 19 }}>
            {['', 'Nuestros vídeos', 'Validación', 'Test'].map((c) => <div key={c} className="mono" style={{ fontSize: 14, color: 'var(--tenue)', paddingBottom: 10, textAlign: c ? 'right' : 'left' }}>{c}</div>)}
            {DOMINIO.map((fila, i) => fila.map((c, j) => (
              <motion.div key={`${i}-${j}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 + i * 0.25 + j * 0.06 }}
                className={j ? 'mono' : ''} style={{ padding: '12px 0', borderTop: '1px solid var(--borde)', textAlign: j ? 'right' : 'left',
                  color: j === 1 ? 'var(--acento)' : j ? 'var(--texto)' : 'var(--suave)' }}>{c}</motion.div>
            )))}
          </div>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2 }} style={{ marginTop: 22, fontSize: 19, color: 'var(--texto)' }}>
            En validación y test hay más robots por imagen y más pequeños. Por eso el aumento aleja los robots (hasta ×0,6) y probamos a darle al modelo la imagen más grande.
          </motion.p>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.4 }} style={{ marginTop: 14, fontSize: 19, color: 'var(--texto)' }}>
            Cada imagen se parece sobre todo a otras de su mismo vídeo (<span className="mono acento">74 %</span> de los casos): por eso validamos con vídeos de otros grupos, no con los nuestros.
          </motion.p>
        </div>
      </div>
    </div>
  );
}

// --- Aumento y depuración ----------------------------------------------------------------------------
const TRANSFORMACIONES = [
  { n: 'Original', g: {}, f: 'none' },
  { n: 'Volteo horizontal', g: { scaleX: -1 }, f: 'none' },
  { n: 'Alejar ×0,6', g: { scale: 0.6 }, f: 'none' },
  { n: 'Giro de 6° y desplazamiento', g: { rotate: 6, x: '5%', y: '-3%', scale: 0.9 }, f: 'none' },
  { n: 'Brillo y contraste', g: {}, f: 'brightness(0.6) contrast(1.25)' },
  { n: 'Balance de blancos', g: {}, f: 'sepia(0.35) hue-rotate(-15deg) saturate(1.4)' },
  { n: 'Desenfoque de movimiento', g: { scale: 1 }, f: 'blur(3px)' },
  { n: 'Ruido y compresión', g: {}, f: 'contrast(1.4) saturate(0.6) brightness(1.05)' },
];
function AumentoEnVivo() {
  const [i, setI] = useState(0);
  const reducido = useReducedMotion();
  useEffect(() => {
    if (reducido) return undefined;
    const id = setInterval(() => setI((n) => (n + 1) % TRANSFORMACIONES.length), 1700);
    return () => clearInterval(id);
  }, [reducido]);
  const t = TRANSFORMACIONES[i];
  const base = { scaleX: 1, scale: 1, rotate: 0, x: '0%', y: '0%' };
  const foto = F.v05;
  return (
    <div>
      <div className="fotograma" style={{ background: '#3a3d38' }}>
        <motion.div style={{ position: 'absolute', inset: 0 }} animate={{ ...base, ...t.g }} transition={{ duration: 0.7, ease: CURVA }}>
          <motion.img src={foto.src} alt="Fotograma de V05" animate={{ filter: t.f }} transition={{ duration: 0.6 }}
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
          {foto.cajas.map((c, k) => <Caja key={k} caja={c} retraso={0.3 + k * 0.15} mostrarRotulo={false} />)}
          {i === 7 && <div style={{ position: 'absolute', inset: 0, opacity: 0.35, mixBlendMode: 'overlay',
            backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27160%27 height=%27160%27%3E%3Cfilter id=%27r%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%270.9%27 numOctaves=%272%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23r)%27/%3E%3C/svg%3E")' }} />}
        </motion.div>
        <AnimatePresence mode="wait">
          <motion.span key={t.n} className="chip on" style={{ position: 'absolute', left: 16, top: 16, zIndex: 3 }}
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.25 }}>
            {t.n}
          </motion.span>
        </AnimatePresence>
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 12 }}>
        {TRANSFORMACIONES.map((x, k) => (
          <div key={x.n} style={{ flex: 1, height: 3, background: k === i ? 'var(--acento)' : 'var(--borde)', transition: 'background .3s' }} />
        ))}
      </div>
      <p style={{ marginTop: 12, fontSize: 18, color: 'var(--suave)' }}>
        Las cajas se mueven con la imagen y el robot nunca se deforma: se escala igual a lo ancho que a lo alto.
      </p>
    </div>
  );
}
// Transformaciones del aumentador (ENTREGA 1/WEEK1/data_aug.ipynb) y extras del perfil robusto_v1
// (herramientas/aumento_robusto.py), con lo que intenta imitar cada una.
const LISTA_AUMENTO = [
  { g: 'Geometría', t: 'Volteo horizontal', p: '50 %', d: 'el rival puede estar a cualquier lado' },
  { g: 'Geometría', t: 'Escala ×0,6 a ×1,25', p: '70 %', d: 'robots lejanos, como en validación y test' },
  { g: 'Geometría', t: 'Desplazamiento y giro ±6°', p: '70 %', d: 'cámara inclinada; el robot no se deforma' },
  { g: 'Color', t: 'Brillo, contraste o gamma', p: '50 %', d: 'otras luces y otras horas' },
  { g: 'Color', t: 'Tono, saturación o canales', p: '30 %', d: 'balance de blancos de otras cámaras' },
  { g: 'Calidad', t: 'Desenfoque de movimiento', p: '15 %', d: 'robot o cámara en marcha' },
  { g: 'Calidad', t: 'JPEG, ruido o menos resolución', p: '30 %', d: 'vídeo comprimido de otros grupos' },
  { g: 'Extra', t: 'Sombras y lluvia en exteriores', p: '25 · 15 %', d: 'V04 y V09, grabados al aire libre' },
  { g: 'Extra', t: 'Tapar hasta un 25 % del robot', p: '15 %', d: 'robots detrás de obstáculos' },
  { g: 'Extra', t: 'Oscurecer o mover los difficult', p: '50 %', d: 'más ejemplos de los que más falla' },
];
const COLOR_GRUPO = { Geometría: 'var(--azul)', Color: 'var(--naranja)', Calidad: '#c9a7ff', Extra: 'var(--acento)' };
export function Aumento() {
  const flujo = [
    { v: DATASET.originales, t: 'originales' },
    { v: DATASET.depuradas, t: 'tras depurar', d: 'quitamos 11 casi repetidas y 1 mal anotada' },
    { v: DATASET.total, t: 'para entrenar', d: `cada imagen y 3 versiones aumentadas · ${fmt(DATASET.cajasTotal)} robots`, acento: true },
  ];
  return (
    <div className="diapo">
      <Cabecera fase="Fase 01 · Aumento y depuración" titulo="Más imágenes sin grabar escenas nuevas" />
      <div className="cuerpo" style={{ gridTemplateColumns: '0.95fr 1.05fr', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 16 }}>
          <AumentoEnVivo />
          <div className="panel" style={{ display: 'grid', gridTemplateColumns: '0.8fr auto 1fr auto 1.2fr', alignItems: 'start', gap: 12, padding: '18px 22px' }}>
            {flujo.map((f, i) => [
              <motion.div key={f.t} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 + i * 0.45 }}>
                <div className={`cifra peque${f.acento ? ' acento' : ''}`}><Contador valor={f.v} retraso={1.2 + i * 0.45} duracion={1} /></div>
                <div style={{ fontSize: 18, color: 'var(--texto)', marginTop: 4 }}>{f.t}</div>
                {f.d && <div style={{ fontSize: 15, color: 'var(--suave)', lineHeight: 1.3 }}>{f.d}</div>}
              </motion.div>,
              i < flujo.length - 1 && (
                <motion.span key={`f${i}`} className="mono acento" style={{ fontSize: 26, paddingTop: 4 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: 1.4 + i * 0.45 }}>{i === 1 ? '×4' : '→'}</motion.span>
              ),
            ])}
          </div>
        </div>
        <div className="panel" style={{ padding: '16px 24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 82px 1fr', gap: 16, paddingBottom: 6 }}>
            {['Transformación', 'Prob.', 'Para qué'].map((c) => <span key={c} className="etiqueta">{c}</span>)}
          </div>
          <Revela retraso={0.4} paso={0.09}>
            {LISTA_AUMENTO.map((x) => (
              <Item key={x.t} style={{ display: 'grid', gridTemplateColumns: '1fr 82px 1fr', gap: 16, alignItems: 'baseline', padding: '8px 0', borderTop: '1px solid var(--borde)' }}>
                <span style={{ fontSize: 18, color: 'var(--texto)' }}>
                  <i style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 5, background: COLOR_GRUPO[x.g], marginRight: 10, verticalAlign: 'middle' }} />{x.t}
                </span>
                <span className="mono" style={{ fontSize: 15, color: 'var(--suave)' }}>{x.p}</span>
                <span style={{ fontSize: 17, color: 'var(--suave)' }}>{x.d}</span>
              </Item>
            ))}
          </Revela>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }} style={{ margin: '10px 0 0', fontSize: 16, color: 'var(--tenue)' }}>
            Descartadas: volteo vertical, giros de 90° y perspectiva, porque el robot nunca aparece así.
          </motion.p>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.4 }} style={{ margin: '8px 0 0', fontSize: 18, color: 'var(--texto)' }}>
            Con aumento, Faster R-CNN v1 pasa de <span className="mono">0,923</span> a <span className="mono acento">0,942</span> de AP@0,5 en validación.
          </motion.p>
        </div>
      </div>
    </div>
  );
}
