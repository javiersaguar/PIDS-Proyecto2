/* Figuras de la cadena de entrenamientos: una figura por bloque [data-cadena], con selectores generados
   a partir de los datos (window.PIDS_CADENA, ver herramientas/construir_web_cadena.py). */
(() => {
  'use strict';

  const clone = value => JSON.parse(JSON.stringify(value));
  const states = [];
  if (window.Plotly) Plotly.register({
    moduleType: 'locale', name: 'es',
    dictionary: {
      'Zoom': 'Ampliar una zona', 'Pan': 'Desplazar', 'Zoom in': 'Acercar', 'Zoom out': 'Alejar',
      'Autoscale': 'Ajustar ejes', 'Reset axes': 'Restablecer ejes', 'Toggle Spike Lines': 'Mostrar guías',
      'Show closest data on hover': 'Mostrar el punto más cercano', 'Compare data on hover': 'Comparar valores',
      'Double-click on legend to isolate one trace': 'Haz doble clic en la leyenda para aislar una serie',
      'Double-click to zoom back out': 'Haz doble clic para restablecer la vista'
    },
    format: { decimal: ',', thousands: '.', grouping: [3] }
  });
  const config = {
    locale: 'es', displaylogo: false, responsive: false, scrollZoom: false, showTips: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage']
  };

  const key = state => state.selected.join('|');

  function layoutFor(state) {
    const variant = state.source.variantes[key(state)];
    const layout = clone(variant.layout);
    const width = Math.floor(state.plot.getBoundingClientRect().width);
    const narrow = width < 680;
    const heatmap = variant.data.some(trace => trace.type === 'heatmap');
    const custom = layout.margin || {};
    layout.width = width;
    layout.autosize = false;
    layout.paper_bgcolor = '#ffffff';
    layout.plot_bgcolor = '#ffffff';
    layout.font = { family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif', size: 12, color: '#233342' };
    layout.hoverlabel = { bgcolor: '#ffffff', font: { size: 12 }, namelength: -1 };
    layout.hovermode = 'closest';
    layout.dragmode = 'zoom';
    layout.separators = ',.';
    layout.uirevision = `${state.name}-${key(state)}`;
    layout.showlegend = !heatmap && variant.data.length > 1;
    layout.legend = { orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom', font: { size: narrow ? 11 : 12 }, groupclick: 'togglegroup' };
    const hasSideAxis = Boolean(layout.yaxis2);
    // En pantallas estrechas la leyenda ocupa una línea por serie: se reserva su altura arriba.
    const entradas = new Set(variant.data.filter(trace => trace.showlegend !== false).map(trace => trace.legendgroup || trace.name)).size;
    layout.margin = {
      l: narrow ? Math.min(custom.l || 56, 150) : custom.l || 64, r: hasSideAxis ? (narrow ? 56 : 72) : (narrow ? 14 : 28),
      t: heatmap ? custom.t || 80 : narrow ? 64 + 21 * entradas : 64, b: custom.b || (narrow ? 70 : 64)
    };
    layout.height = layout.height ? layout.height + (narrow ? 80 : 0) : (narrow ? 460 : 500);
    for (const name of ['xaxis', 'yaxis', 'yaxis2']) {
      if (!layout[name]) continue;
      Object.assign(layout[name], {
        gridcolor: '#e7edf2', zerolinecolor: '#dce3e9', linecolor: '#dce3e9', automargin: true,
        tickfont: { size: narrow ? 10 : 11, color: '#526576' },
        title: { ...(layout[name].title || {}), font: { size: 12, color: '#526576' }, standoff: 10 }
      });
    }
    if (heatmap) { layout.xaxis.showgrid = false; layout.yaxis.showgrid = false; }
    return layout;
  }

  function showError(state) {
    state.status.hidden = false;
    state.status.replaceChildren(document.createTextNode('No se pudo cargar la figura.'));
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'retry';
    retry.textContent = 'Reintentar';
    retry.addEventListener('click', () => draw(state), { once: true });
    state.status.append(retry);
  }

  async function draw(state) {
    state.status.textContent = 'Cargando la figura…';
    state.status.hidden = false;
    try {
      if (!window.Plotly || !state.source) throw new Error('Faltan los recursos locales');
      const variant = state.source.variantes[key(state)];
      await Plotly.react(state.plot, clone(variant.data), layoutFor(state), config);
      state.ready = true;
      state.width = Math.floor(state.plot.getBoundingClientRect().width);
      state.status.hidden = true;
      state.stage.querySelectorAll('[data-export]').forEach(button => { button.disabled = false; });
    } catch (error) {
      state.ready = false;
      showError(state);
      console.error('No se pudo dibujar ' + state.name, error);
    }
  }

  function crearControles(state) {
    const box = state.stage.querySelector('.chart-controls');
    (state.source?.controles || []).forEach((control, index) => {
      const id = `cadena-${state.name}-${index}`;
      const label = document.createElement('label');
      label.htmlFor = id;
      label.textContent = control.etiqueta;
      const select = document.createElement('select');
      select.id = id;
      select.setAttribute('aria-controls', `grafica-cadena-${state.name}`);
      control.opciones.forEach((texto, i) => {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = texto;
        select.append(option);
      });
      select.addEventListener('change', () => {
        state.selected[index] = Number(select.value);
        draw(state);
      });
      const inicial = control.predeterminado || 0;
      select.value = inicial;
      state.selected.push(inicial);
      box.append(label, select);
    });
    if (!box.children.length) box.remove();
  }

  document.querySelectorAll('[data-cadena]').forEach(stage => {
    const name = stage.dataset.cadena;
    const state = {
      name, stage, source: window.PIDS_CADENA?.[name], plot: stage.querySelector('.plot'),
      status: stage.querySelector('.chart-status'), selected: [], ready: false
    };
    if (!state.selected.length && state.source && !state.source.controles.length) state.selected = [0];
    crearControles(state);
    const message = document.createElement('p');
    message.className = 'export-status';
    message.setAttribute('role', 'status');
    stage.querySelector('.figure-caption').append(message);
    stage.querySelectorAll('[data-export]').forEach(button => {
      button.addEventListener('click', async () => {
        button.disabled = true;
        message.textContent = 'Preparando la descarga…';
        try {
          await Plotly.downloadImage(state.plot, { format: button.dataset.export, filename: `bloque2-${name}`, width: state.width, height: state.plot.layout.height, scale: 2 });
          message.textContent = 'Descarga preparada.';
        } catch (error) {
          message.textContent = 'No se pudo preparar la descarga. Vuelve a intentarlo.';
          console.error(error);
        } finally { button.disabled = false; }
      });
    });
    states.push(state);
  });

  let timer;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      for (const state of states) {
        const width = Math.floor(state.plot.getBoundingClientRect().width);
        if (!state.ready || width === state.width) continue;
        state.width = width;
        await Plotly.relayout(state.plot, layoutFor(state));
      }
    }, 150);
  });

  // Se dibujan cuando se acercan a la pantalla: son diez figuras y no todas hacen falta de entrada.
  const observer = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      const state = states.find(item => item.stage === entry.target);
      if (state) draw(state);
    });
  }, { rootMargin: '600px 0px' }) : null;
  states.forEach(state => observer ? observer.observe(state.stage) : draw(state));
})();
