(() => {
  'use strict';
  const graph = document.querySelector('.plotly-graph-div');
  if (!graph) return;
  const embedded = window.parent !== window;
  let pausePlayback = () => {};

  function reportSize() {
    if (!embedded) return;
    window.parent.postMessage({ type: 'pids:figure-size', height: Math.ceil(graph.parentElement.getBoundingClientRect().height + 2) }, '*');
  }
  window.addEventListener('message', (event) => {
    if (event.source !== window.parent) return;
    if (event.data?.type === 'pids:pause') pausePlayback();
    if (event.data?.type === 'pids:request-size') reportSize();
  });

  const began = performance.now();
  function ready() {
    if (!graph._fullLayout || !graph._transitionData?._frames?.length) {
      if (performance.now() - began < 10000) setTimeout(ready, 40);
      return;
    }
    enhance().catch(() => {
      pausePlayback();
      document.body.classList.remove('figure-enhanced', 'embedded');
      document.querySelectorAll('.chart-header, .chart-toolbar').forEach((element) => element.remove());
      reportSize();
    });
  }

  async function enhance() {
    const plotly = window.Plotly;
    const frames = graph._transitionData._frames;
    const heatmap = graph.data[0].type === 'heatmap';
    const original = JSON.parse(JSON.stringify(graph.layout));
    const menus = original.updatemenus || [];
    const play = menus.flatMap((menu) => menu.buttons || []).find((button) => button.args?.[1]?.fromcurrent);
    const duration = play?.args[1].frame.duration || 550;
    const annotations = original.annotations.map((annotation) => ({ ...annotation, font: { size: 13, color: '#233342' } }));
    let cursor = 0;
    let playing = false;
    let playbackSession = 0;
    let timer;
    let revision = 0;
    let queue = Promise.resolve();
    let lastWidth = 0;

    function titleParts(frame) {
      const text = frame.layout?.title?.text || original.title.text;
      const parsed = new DOMParser().parseFromString(text, 'text/html');
      return { title: parsed.body.firstChild?.textContent || '', context: parsed.querySelector('sup')?.textContent || '' };
    }
    const metadata = frames.map(titleParts);
    const groups = new Map();
    if (heatmap) metadata.forEach((meta, index) => {
      const video = meta.context.match(/\bV\d{2}\b/)?.[0];
      if (video && !groups.has(video)) groups.set(video, index);
    });

    const header = document.createElement('header');
    header.className = 'chart-header';
    const heading = document.createElement('div');
    const title = document.createElement('h1');
    title.className = 'chart-title';
    title.textContent = metadata[0].title;
    const context = document.createElement('p');
    context.className = 'chart-context';
    heading.append(title, context);
    header.append(heading);

    let videoSelect;
    if (groups.size) {
      const label = document.createElement('label');
      label.className = 'video-field';
      label.append(document.createTextNode('Vídeo'));
      videoSelect = document.createElement('select');
      videoSelect.setAttribute('aria-label', 'Seleccionar vídeo de la figura');
      groups.forEach((index, video) => videoSelect.add(new Option(video, String(index))));
      videoSelect.addEventListener('change', () => { stop(); show(Number(videoSelect.value)); });
      label.append(videoSelect);
      header.append(label);
    }

    const toolbar = document.createElement('div');
    toolbar.className = 'chart-toolbar';
    toolbar.setAttribute('role', 'group');
    toolbar.setAttribute('aria-label', 'Controles de reproducción');
    toolbar.innerHTML = '<div class="playback"><button type="button" class="chart-button play-button" aria-pressed="false"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 3l11 7-11 7z"/></svg><span>Reproducir</span></button><button type="button" class="chart-button step-button previous" aria-label="Muestra anterior" title="Muestra anterior"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 10H4m5-5-5 5 5 5"/></svg></button><button type="button" class="chart-button step-button next" aria-label="Muestra siguiente" title="Muestra siguiente"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h12m-5-5 5 5-5 5"/></svg></button></div><div class="timeline"><input type="range" min="0" step="1"><span class="sample-count"></span></div>';
    const toggle = toolbar.querySelector('.play-button');
    const previous = toolbar.querySelector('.previous');
    const next = toolbar.querySelector('.next');
    const range = toolbar.querySelector('input');
    const count = toolbar.querySelector('.sample-count');
    range.max = String(frames.length - 1);
    range.setAttribute('aria-label', heatmap ? (frames.length === 10 ? 'Recorrer vídeos' : 'Recorrer intervalos') : 'Recorrer fotogramas');
    const error = document.createElement('p');
    error.className = 'chart-error';
    error.setAttribute('role', 'status');
    error.hidden = true;
    graph.before(header, toolbar, error);
    document.body.classList.add('figure-enhanced');
    document.body.classList.toggle('embedded', embedded);

    function update() {
      context.textContent = metadata[cursor].context;
      range.value = String(cursor);
      range.setAttribute('aria-valuetext', metadata[cursor].context);
      count.textContent = `${cursor + 1} / ${frames.length}`;
      previous.disabled = cursor === 0;
      next.disabled = cursor === frames.length - 1;
      if (videoSelect) {
        const video = metadata[cursor].context.match(/\bV\d{2}\b/)?.[0];
        if (groups.has(video)) videoSelect.value = String(groups.get(video));
      }
    }
    function stop() {
      playing = false;
      playbackSession++;
      clearTimeout(timer);
      toggle.setAttribute('aria-pressed', 'false');
      toggle.querySelector('span').textContent = 'Reproducir';
      toggle.querySelector('svg').innerHTML = '<path d="M6 3l11 7-11 7z"/>';
    }
    pausePlayback = stop;
    function show(index) {
      const target = Math.max(0, Math.min(frames.length - 1, index));
      const request = ++revision;
      queue = queue.catch(() => {}).then(async () => {
        if (request !== revision) return;
        await plotly.animate(graph, [frames[target].name], {
          mode: 'immediate', frame: { duration: 0, redraw: true }, transition: { duration: 0 },
        });
        cursor = target;
        error.hidden = true;
        update();
        reportSize();
      }).catch(() => {
        stop();
        error.textContent = 'No se ha podido mostrar esta muestra. Vuelve a seleccionarla para reintentar.';
        error.hidden = false;
        reportSize();
      });
      return queue;
    }
    async function advance(session) {
      if (!playing || session !== playbackSession) return;
      const started = performance.now();
      await show(cursor + 1);
      if (!playing || session !== playbackSession) return;
      if (cursor === frames.length - 1) stop();
      else timer = setTimeout(() => advance(session), Math.max(0, duration - (performance.now() - started)));
    }
    toggle.addEventListener('click', () => {
      if (playing) return stop();
      const session = ++playbackSession;
      playing = true;
      toggle.setAttribute('aria-pressed', 'true');
      toggle.querySelector('span').textContent = 'Pausar';
      toggle.querySelector('svg').innerHTML = '<path d="M5 3h4v14H5zm6 0h4v14h-4z"/>';
      const schedule = () => {
        if (playing && session === playbackSession) timer = setTimeout(() => advance(session), duration);
      };
      if (cursor === frames.length - 1) show(0).then(schedule);
      else schedule();
    });
    previous.addEventListener('click', () => { stop(); show(cursor - 1); });
    next.addEventListener('click', () => { stop(); show(cursor + 1); });
    range.addEventListener('input', () => { stop(); show(Number(range.value)); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    window.addEventListener('pagehide', stop);

    async function fit() {
      const width = graph.parentElement.clientWidth;
      if (Math.abs(width - lastWidth) < 2) return;
      lastWidth = width;
      const narrow = width < 560;
      const settings = {
        width, autosize: false,
        font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif', size: 12, color: '#233342' },
        paper_bgcolor: '#ffffff', plot_bgcolor: '#ffffff', updatemenus: [], sliders: [],
        hoverlabel: { bgcolor: '#ffffff', bordercolor: '#dce3e9', font: { family: 'sans-serif', size: 12, color: '#233342' } },
      };
      let height;
      const labels = annotations.map((annotation) => ({ ...annotation, font: { ...annotation.font } }));
      if (heatmap) {
        const margin = narrow ? { l: 40, r: 74, t: 30, b: 36 } : { l: 52, r: 94, t: 38, b: 40 };
        const mapHeight = Math.max(70, (width - margin.l - margin.r) * (narrow ? 1 : .455) * .5625);
        const plotHeight = narrow ? 2 * mapHeight + 72 : mapHeight;
        height = Math.ceil(plotHeight + margin.t + margin.b);
        settings.margin = margin;
        for (let i = 0; i < 2; i++) {
          const x = i ? 'xaxis2' : 'xaxis';
          const y = i ? 'yaxis2' : 'yaxis';
          settings[`${x}.domain`] = narrow ? [0, 1] : original[x].domain;
          settings[`${y}.domain`] = narrow ? (i ? [0, mapHeight / plotHeight] : [(mapHeight + 72) / plotHeight, 1]) : [0, 1];
          settings[`${x}.range`] = [0, 1];
          settings[`${y}.range`] = [1, 0];
          settings[`${x}.constrain`] = 'domain';
          labels[i].x = narrow ? .5 : annotations[i].x;
          labels[i].y = narrow && i ? mapHeight / plotHeight : 1;
        }
        settings['coloraxis.colorbar.thickness'] = 10;
        settings['coloraxis.colorbar.len'] = narrow ? .8 : 1;
        settings['coloraxis.colorbar.tickfont'] = { size: 11, color: '#526576' };
        settings['coloraxis.colorbar.title.font'] = { size: 11, color: '#526576' };
        settings['coloraxis.colorbar.outlinewidth'] = 0;
      } else {
        const columns = narrow ? 1 : 2;
        const rows = 10 / columns;
        const gap = narrow ? .035 : .055;
        const panelHeight = (1 - gap * (rows - 1)) / rows;
        height = narrow ? 1740 : 930;
        settings.margin = { l: 48, r: 16, t: 30, b: 40 };
        for (let i = 0; i < 10; i++) {
          const suffix = i ? String(i + 1) : '';
          const row = Math.floor(i / columns);
          const top = 1 - row * (panelHeight + gap);
          const column = i % columns;
          settings[`xaxis${suffix}.domain`] = narrow ? [0, 1] : original[`xaxis${suffix}`].domain;
          settings[`yaxis${suffix}.domain`] = [top - panelHeight, top];
          settings[`xaxis${suffix}.nticks`] = narrow ? 5 : 6;
          settings[`xaxis${suffix}.gridcolor`] = '#e6edf2';
          settings[`yaxis${suffix}.gridcolor`] = '#e6edf2';
          labels[i].x = narrow ? .5 : (column ? .7725 : .2275);
          labels[i].y = top;
        }
      }
      Object.keys(original).filter((key) => /^([xy])axis\d*$/.test(key)).forEach((key) => {
        settings[`${key}.tickfont`] = { size: 11, color: '#526576' };
        settings[`${key}.title.font`] = { size: 12, color: '#526576' };
        settings[`${key}.title.standoff`] = 8;
      });
      settings.annotations = labels;
      settings.height = height;
      graph.style.height = `${height}px`;
      await queue;
      await plotly.relayout(graph, settings);
      reportSize();
    }
    update();
    await fit();
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => fit().catch(() => {}), 100);
    });
    new ResizeObserver(reportSize).observe(document.body);
    reportSize();
  }
  ready();
})();
