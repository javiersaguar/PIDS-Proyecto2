// Figuras del Bloque 3 en SVG, sin bibliotecas. Datos en datos.js (preparar_datos.py).
(function () {
  'use strict';
  const D = window.DATOS_BLOQUE3;
  if (!D) return;
  const NS = 'http://www.w3.org/2000/svg';
  const $ = (id) => document.getElementById(id);
  const coma = (v, d = 0) => v.toLocaleString('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d });
  const reloj = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  function el(padre, tipo, attrs = {}, texto) {
    const n = document.createElementNS(NS, tipo);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (texto != null) n.textContent = texto;
    padre.appendChild(n);
    return n;
  }

  const FASES = {
    'inicio': ['Salida', 'gris'], 'P1-ruta': ['Túnel', 'ruta'], 'P1-parada': ['P1 · parado', 'parada'],
    'R1-ruta': ['Hacia R1', 'ruta'], 'R1-marcha': ['R1 · retrocede disparando', 'marcha'],
    'R1-vuelta': ['Vuelta', 'ruta'], 'R2-ruta': ['Hacia R2', 'ruta'],
    'R2-marcha': ['R2 · avanza disparando', 'marcha'], 'baile': ['Baile', 'baile'],
  };
  const color = (fase) => `var(--${(FASES[fase] || ['', 'gris'])[1]})`;
  const nombreFase = (fase) => (FASES[fase] || [fase])[0];
  const TEXTO_FASE = {
    'inicio': 'Espera en la salida a que arranque la demo.',
    'P1-parada': 'Parado en P1: gira la torreta a la derecha (rival 1) y a la izquierda (robot camuflado) y dispara una ráfaga de 20 a cada uno.',
    'baile': 'Baile final con música y los LED cambiando de color.',
  };
  for (const t of D.tramos) TEXTO_FASE[t.fase] = t.texto;

  function grupos(recorrido) {
    const g = [];
    recorrido.forEach((f, i) => {
      if (g.length && g[g.length - 1].fase === f.fase) g[g.length - 1].fin = i;
      else g.push({ fase: f.fase, inicio: i, fin: i });
    });
    // Duración con la hora de las fotos (al segundo): hasta la primera foto de la fase siguiente.
    g.forEach((x, k) => {
      x.t0 = recorrido[x.inicio].t;
      x.s = (k + 1 < g.length ? recorrido[g[k + 1].inicio].t : recorrido[recorrido.length - 1].t) - x.t0;
    });
    return g;
  }

  function llenarIntentos(select) {
    D.intentos.forEach((it, i) => {
      const o = document.createElement('option');
      o.value = i; o.textContent = `${it.nombre} (${it.hora})`;
      select.appendChild(o);
    });
  }

  // ---------- Figura 1: recorrido foto a foto ----------
  const M = { esc: 100, ox: 50, oy: 270 };
  const mx = (x) => M.ox + x * M.esc;
  const my = (y) => M.oy + y * M.esc;
  const R = { intento: 0, i: 0, temporizador: null };
  let robot, rastro, canon;

  function dibujarMapa() {
    const svg = $('mapa');
    for (let m = 0; m <= 9; m++) {
      el(svg, 'line', { x1: mx(m), x2: mx(m), y1: 20, y2: 430, stroke: '#e6ebf0', 'stroke-dasharray': '2 5' });
      el(svg, 'text', { x: mx(m), y: 458, 'text-anchor': 'middle', fill: '#7a8a99', 'font-size': 20 }, `${m} m`);
    }
    for (const t of D.tramos) {
      const pts = D.puntos.slice(t.desde, t.hasta + 1).map(([x, y]) => `${mx(x)},${my(y)}`).join(' ');
      const marcha = t.fase.endsWith('marcha');
      el(svg, 'polyline', { points: pts, fill: 'none', stroke: marcha ? 'var(--marcha)' : 'var(--ruta)', 'stroke-width': marcha ? 9 : 4,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0.85 });
    }
    // P1, salida y final
    const [p1x, p1y] = [mx(D.puntos[1][0]), my(D.puntos[1][1])];
    el(svg, 'polygon', { points: [[-9, -20], [9, -20], [20, -9], [20, 9], [9, 20], [-9, 20], [-20, 9], [-20, -9]].map(([a, b]) => `${p1x + a},${p1y + b}`).join(' '),
      fill: 'none', stroke: 'var(--parada)', 'stroke-width': 2.5 });
    el(svg, 'text', { x: p1x, y: p1y - 28, 'text-anchor': 'middle', 'font-size': 22, 'font-weight': 600, fill: 'var(--text)' }, 'P1');
    const fin = D.puntos[D.puntos.length - 1];
    el(svg, 'text', { x: mx(0), y: my(0) + 34, 'text-anchor': 'middle', 'font-size': 20, fill: 'var(--muted)' }, 'salida');
    el(svg, 'text', { x: mx(fin[0]), y: my(fin[1]) - 18, 'text-anchor': 'end', 'font-size': 20, fill: 'var(--muted)' }, 'baile');
    for (const r of D.rivales) {
      const [cx, cy] = [mx(r.x), my(r.y)];
      if (r.hasta_x != null) {
        el(svg, 'line', { x1: cx - 22, x2: mx(r.hasta_x) + 4, y1: cy, y2: cy, stroke: 'var(--parada)', 'stroke-width': 2, 'stroke-dasharray': '4 4' });
        el(svg, 'path', { d: `M${mx(r.hasta_x)},${cy} l10,-6 v12 z`, fill: 'var(--parada)' });
      }
      if (r.escondido) el(svg, 'rect', { x: cx - 26, y: cy - 22, width: 52, height: 44, rx: 4, fill: '#eef1f4', stroke: '#c5cfd8' });
      el(svg, 'rect', { x: cx - 16, y: cy - 12, width: 32, height: 24, rx: 4, fill: r.camuflado ? '#fff' : 'var(--parada)',
        stroke: 'var(--parada)', 'stroke-width': 2.5, 'stroke-dasharray': r.camuflado ? '5 4' : '' });
      const debajo = r.y > 0 || r.escondido;
      el(svg, 'text', { x: cx, y: debajo ? cy + (r.escondido ? 40 : 44) : cy - 24, 'text-anchor': 'middle', 'font-size': r.escondido ? 18 : 20, 'font-weight': 600, fill: 'var(--parada)' }, r.nombre);
      if (r.escondido) el(svg, 'text', { x: cx, y: cy + 58, 'text-anchor': 'middle', 'font-size': 16, fill: 'var(--parada)' }, 'en una caja');
    }
    rastro = el(svg, 'polyline', { fill: 'none', stroke: 'var(--text)', 'stroke-width': 2, 'stroke-dasharray': '1 5', 'stroke-linecap': 'round' });
    robot = el(svg, 'g', {});
    el(robot, 'circle', { r: 22, fill: 'var(--accent)', opacity: 0.15 });
    el(robot, 'rect', { x: -13, y: -10, width: 26, height: 20, rx: 4, fill: 'var(--text)' });
    canon = el(robot, 'circle', { r: 5, fill: '#fff' });
  }

  function dibujarFranja() {
    const franja = $('franja');
    franja.textContent = '';
    const rec = D.intentos[R.intento].recorrido;
    for (const g of grupos(rec)) {
      const b = document.createElement('button');
      b.type = 'button';
      b.style.flex = `${g.fin - g.inicio + 1} 1 0`;
      b.style.background = color(g.fase);
      b.textContent = nombreFase(g.fase);
      b.title = `${nombreFase(g.fase)}: unos ${g.s} s`;
      b.setAttribute('aria-label', b.title);
      b.dataset.inicio = g.inicio;
      b.dataset.fin = g.fin;
      b.addEventListener('click', () => { parar(); mostrar(g.inicio); });
      franja.appendChild(b);
    }
  }

  function mostrar(i) {
    const rec = D.intentos[R.intento].recorrido;
    R.i = Math.max(0, Math.min(rec.length - 1, i));
    const f = rec[R.i];
    $('barra').value = R.i;
    $('foto-recorrido').src = f.img;
    $('foto-recorrido').alt = `Cámara del robot: ${nombreFase(f.fase)}, segundo ${f.t}`;
    $('fase-recorrido').textContent = nombreFase(f.fase);
    $('fase-recorrido').style.background = color(f.fase);
    $('reloj').textContent = `${reloj(f.t)} / ${reloj(rec[rec.length - 1].t)}`;
    $('tramo-actual').textContent = TEXTO_FASE[f.fase] || '';
    robot.setAttribute('transform', `translate(${mx(f.x)},${my(f.y)})`);
    rastro.setAttribute('points', rec.slice(0, R.i + 1).map((p) => `${mx(p.x)},${my(p.y)}`).join(' '));
    for (const b of $('franja').children) b.classList.toggle('activa', R.i >= +b.dataset.inicio && R.i <= +b.dataset.fin);
    // precarga las siguientes
    for (let k = 1; k <= 4; k++) if (rec[R.i + k]) new Image().src = rec[R.i + k].img;
  }

  function parar() {
    clearInterval(R.temporizador); R.temporizador = null;
    $('reproducir').textContent = 'Reproducir';
    $('reproducir').setAttribute('aria-pressed', 'false');
  }
  function reproducir() {
    const rec = D.intentos[R.intento].recorrido;
    if (R.i >= rec.length - 1) mostrar(0);
    $('reproducir').textContent = 'Pausa';
    $('reproducir').setAttribute('aria-pressed', 'true');
    R.temporizador = setInterval(() => {
      if (R.i >= rec.length - 1) return parar();
      mostrar(R.i + 1);
    }, 500 / +$('velocidad').value);
  }

  function iniciarRecorrido() {
    llenarIntentos($('intento-recorrido'));
    dibujarMapa();
    const cambiar = () => {
      parar();
      R.intento = +$('intento-recorrido').value;
      $('barra').max = D.intentos[R.intento].recorrido.length - 1;
      dibujarFranja();
      mostrar(0);
    };
    $('intento-recorrido').addEventListener('change', cambiar);
    $('barra').addEventListener('input', (e) => { parar(); mostrar(+e.target.value); });
    $('reproducir').addEventListener('click', () => (R.temporizador ? parar() : reproducir()));
    $('velocidad').addEventListener('change', () => { if (R.temporizador) { parar(); reproducir(); } });
    cambiar();
    if (window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
      new IntersectionObserver((entradas, obs) => {
        if (entradas[0].isIntersecting) { obs.disconnect(); if (!R.temporizador && R.i === 0) reproducir(); }
      }, { threshold: 0.6 }).observe($('recorrido').querySelector('.visor'));
    }
  }

  // ---------- Figura 2: qué vio el detector ----------
  const G = { w: 720, h: 420, iz: 62, de: 16, ar: 34, ab: 46 };
  const MEDIDAS = {
    conf: { titulo: 'Confianza', dom: [0.3, 1.02], marcas: [0.3, 0.5, 0.7, 0.9, 1], fmt: (v) => coma(v, 2) },
    yaw: { titulo: 'Ángulo de la torreta (°)', dom: null, fmt: (v) => `${coma(v, 0)}°` },
    ms: { titulo: 'Tiempo por imagen (ms)', dom: [0, 420], marcas: [0, 100, 200, 300, 400], fmt: (v) => `${coma(v, 0)} ms` },
  };
  const S = { intento: 0, medida: 'conf', sel: 0 };

  function escala(d0, d1, r0, r1) { return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0); }

  function dibujarDetector() {
    const svg = $('svg-detector');
    svg.textContent = '';
    const it = D.intentos[S.intento];
    const det = it.detecciones;
    const med = MEDIDAS[S.medida];
    const t0 = Math.floor(det[0].t / 5) * 5 - 2;
    const t1 = Math.ceil(det[det.length - 1].t / 5) * 5 + 2;
    const X = escala(t0, t1, G.iz, G.w - G.de);
    let dom = med.dom, marcas = med.marcas;
    if (S.medida === 'yaw') {
      const ys = det.map((d) => d.yaw);
      const a = Math.floor(Math.min(...ys) / 45) * 45, b = Math.ceil(Math.max(...ys) / 45) * 45;
      dom = [a - 10, b + 10]; marcas = [];
      for (let v = a; v <= b; v += 45) marcas.push(v);
    }
    const Y = escala(dom[0], dom[1], G.h - G.ab, G.ar);
    // Fondo por parada
    const paradas = [];
    for (const d of det) {
      const p = paradas[paradas.length - 1];
      if (p && p.nombre === d.parada) p.fin = d.t; else paradas.push({ nombre: d.parada, inicio: d.t, fin: d.t });
    }
    for (const p of paradas) {
      const fase = p.nombre === 'P1' ? 'P1-parada' : p.nombre;
      const x0 = X(p.inicio) - 6, x1 = X(p.fin) + 6;
      el(svg, 'rect', { x: x0, y: G.ar, width: x1 - x0, height: G.h - G.ab - G.ar, fill: color(fase), opacity: 0.07 });
      el(svg, 'text', { x: (x0 + x1) / 2, y: G.ar - 10, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 600, fill: color(fase) },
        p.nombre === 'P1' ? 'P1 · parado' : p.nombre.replace('-marcha', ' · en marcha'));
    }
    // Ejes
    for (const v of marcas) {
      el(svg, 'line', { x1: G.iz, x2: G.w - G.de, y1: Y(v), y2: Y(v), stroke: '#e6ebf0' });
      el(svg, 'text', { x: G.iz - 8, y: Y(v) + 4, 'text-anchor': 'end', 'font-size': 12, fill: '#7a8a99' }, med.fmt(v));
    }
    for (let t = Math.ceil(t0 / 10) * 10; t <= t1; t += 10) {
      el(svg, 'text', { x: X(t), y: G.h - G.ab + 20, 'text-anchor': 'middle', 'font-size': 12, fill: '#7a8a99' }, reloj(t));
    }
    el(svg, 'text', { x: (G.iz + G.w - G.de) / 2, y: G.h - 6, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--muted)' }, 'tiempo desde la salida (min:s)');
    el(svg, 'text', { x: 14, y: (G.ar + G.h - G.ab) / 2, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--muted)',
      transform: `rotate(-90 14 ${(G.ar + G.h - G.ab) / 2})` }, med.titulo);
    if (S.medida === 'conf') {
      el(svg, 'line', { x1: G.iz, x2: G.w - G.de, y1: Y(D.umbral), y2: Y(D.umbral), stroke: 'var(--parada)', 'stroke-width': 1.5, 'stroke-dasharray': '6 4' });
      el(svg, 'text', { x: G.w - G.de, y: Y(D.umbral) + 16, 'text-anchor': 'end', 'font-size': 12, 'font-weight': 600, fill: 'var(--parada)' }, 'umbral 0,95');
    }
    if (S.medida === 'ms') {
      const ms = det.map((d) => d.ms).sort((a, b) => a - b);
      const med2 = ms[Math.floor(ms.length / 2)];
      el(svg, 'line', { x1: G.iz, x2: G.w - G.de, y1: Y(med2), y2: Y(med2), stroke: 'var(--accent)', 'stroke-dasharray': '6 4' });
      el(svg, 'text', { x: G.w - G.de, y: Y(med2) - 8, 'text-anchor': 'end', 'font-size': 12, 'font-weight': 600, fill: 'var(--accent)' }, `mediana ${med2} ms`);
    }
    // Puntos
    const capa = el(svg, 'g', {});
    det.forEach((d, i) => {
      const valores = S.medida === 'conf' ? d.conf.map((c, k) => [c, k < d.aceptadas]) : [[d[S.medida], d.aceptadas > 0]];
      if (S.medida === 'conf' && !d.conf.length) valores.push([0.3, false, true]);
      for (const [v, ok, vacia] of valores) {
        const c = el(capa, 'circle', { cx: X(d.t), cy: Y(Math.max(dom[0], v)), r: i === S.sel ? 7 : 4.5, class: 'punto',
          fill: vacia ? '#fff' : ok ? 'var(--text)' : '#fff', stroke: vacia ? '#b9c4ce' : ok ? 'none' : 'var(--marcha)', 'stroke-width': 2 });
        if (i === S.sel) c.setAttribute('stroke', 'var(--accent)'), c.setAttribute('stroke-width', 3);
        c.addEventListener('mouseenter', () => consejo(c, d, v, vacia));
        c.addEventListener('mouseleave', () => ($('consejo').hidden = true));
        c.addEventListener('click', () => seleccionar(i));
      }
    });
    $('leyenda-detector').innerHTML = S.medida === 'conf'
      ? '<span><i style="background:var(--text)"></i>pasa el umbral: es un rival</span><span><i style="background:#fff;border:2px solid var(--marcha)"></i>por debajo del umbral: no se ataca</span><span><i style="background:#fff;border:2px solid #b9c4ce"></i>imagen sin detecciones</span>'
      : '<span><i style="background:var(--text)"></i>imagen con un rival</span><span><i style="background:#fff;border:2px solid var(--marcha)"></i>imagen sin rival</span>';
  }

  function consejo(c, d, v, vacia) {
    const caja = $('grafica-detector').getBoundingClientRect();
    const r = c.getBoundingClientRect();
    const ct = $('consejo');
    const med = MEDIDAS[S.medida];
    ct.innerHTML = `<b>${reloj(d.t)} · ${d.parada} · ${d.fase}</b><br>` +
      (vacia ? 'sin detecciones' : `${med.titulo.replace(/ \(.*/, '')}: ${med.fmt(v)}`) +
      (S.medida !== 'yaw' ? ` · torreta ${coma(d.yaw)}°` : '');
    ct.style.left = `${r.left + r.width / 2 - caja.left}px`;
    ct.style.top = `${r.top - caja.top}px`;
    ct.hidden = false;
  }

  function seleccionar(i) {
    const det = D.intentos[S.intento].detecciones;
    S.sel = Math.max(0, Math.min(det.length - 1, i));
    const d = det[S.sel];
    $('foto-detector').src = d.img;
    $('foto-detector').alt = `Imagen ${d.n} de ${d.parada}, ${d.fase}, con las cajas del detector`;
    $('titulo-foto').textContent = `${d.parada} · ${d.fase}`;
    $('titulo-foto').style.background = color(d.parada === 'P1' ? 'P1-parada' : d.parada);
    const confs = d.conf.length ? d.conf.map((c) => coma(c, 3)).join(', ') : 'ninguna';
    $('ficha').innerHTML = `<b>Imagen ${d.n} de ${D.intentos[S.intento].detecciones.length}</b> · ${reloj(d.t)} · torreta a ${coma(d.yaw)}°<br>` +
      `Detecciones: ${confs}. ${d.aceptadas ? `<b>${d.aceptadas === 1 ? 'Una pasa' : `${d.aceptadas} pasan`} el umbral.</b>` : 'Ninguna pasa el umbral.'}` +
      `${d.disparos ? ` Ráfaga de ${d.disparos} disparos.` : ''} Inferencia: ${d.ms} ms.`;
    dibujarDetector();
  }

  function iniciarDetector() {
    llenarIntentos($('intento-detector'));
    const cambiar = () => {
      S.intento = +$('intento-detector').value;
      S.medida = $('medida').value;
      S.sel = Math.min(S.sel, D.intentos[S.intento].detecciones.length - 1);
      seleccionar(S.sel);
    };
    $('intento-detector').addEventListener('change', () => { S.sel = 0; cambiar(); });
    $('medida').addEventListener('change', cambiar);
    $('anterior').addEventListener('click', () => seleccionar(S.sel - 1));
    $('siguiente').addEventListener('click', () => seleccionar(S.sel + 1));
    $('exportar-detector').addEventListener('click', () => {
      const svg = $('svg-detector').cloneNode(true);
      svg.setAttribute('xmlns', NS);
      const estilo = getComputedStyle(document.documentElement);
      let texto = new XMLSerializer().serializeToString(svg);
      texto = texto.replace(/var\(--([a-z]+)\)/g, (_, n) => estilo.getPropertyValue(`--${n}`).trim() || '#233342');
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([texto], { type: 'image/svg+xml' }));
      a.download = `detector_${D.intentos[S.intento].clave}_${S.medida}.svg`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });
    cambiar();
  }

  // ---------- Figura 3: duración de cada fase ----------
  function dibujarDuraciones() {
    const svg = $('svg-duraciones');
    const iz = 190, de = 20, alto = 46;
    const total = (it) => it.recorrido[it.recorrido.length - 1].t - it.recorrido[0].t;
    const maximo = Math.max(...D.intentos.map(total));
    const X = escala(0, maximo, iz, 960 - de);
    D.intentos.forEach((it, k) => {
      const y = 22 + k * (alto + 40);
      el(svg, 'text', { x: iz - 12, y: y + alto / 2 - 4, 'text-anchor': 'end', 'font-size': 14, 'font-weight': 600, fill: 'var(--text)' }, it.nombre);
      el(svg, 'text', { x: iz - 12, y: y + alto / 2 + 14, 'text-anchor': 'end', 'font-size': 12, fill: 'var(--muted)' }, `${reloj(total(it))} en total`);
      for (const g of grupos(it.recorrido)) {
        const s0 = g.t0 - it.recorrido[0].t, s = g.s;
        const x0 = X(s0), w = X(s0 + s) - x0;
        const r = el(svg, 'rect', { x: x0, y, width: Math.max(0, w - 2), height: alto, fill: color(g.fase), class: 'seg' });
        el(r, 'title', {}, `${nombreFase(g.fase)}: unos ${s} s`);
        if (w > 44) el(svg, 'text', { x: x0 + w / 2 - 1, y: y + alto / 2 + 5, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 600, fill: '#fff', 'pointer-events': 'none' }, `${s} s`);
      }
    });
    for (let t = 0; t <= maximo; t += 30) {
      el(svg, 'text', { x: X(t), y: 184, 'text-anchor': 'middle', 'font-size': 12, fill: '#7a8a99' }, reloj(t));
    }
  }

  iniciarRecorrido();
  iniciarDetector();
  dibujarDuraciones();
})();
