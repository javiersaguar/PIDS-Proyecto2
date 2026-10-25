/* Figuras locales: datos originales, controles nativos y disposición adaptable. */
(() => {
  'use strict';

  const clone = value => JSON.parse(JSON.stringify(value));
  const colors = { '#A6B4C2': '#788797', '#6E9BCB': '#527fad' };
  const states = [];
  const select = document.getElementById('experimento');
  if (window.Plotly) Plotly.register({
    moduleType: 'locale', name: 'es',
    dictionary: {
      'Zoom': 'Ampliar una zona', 'Pan': 'Desplazar', 'Zoom in': 'Acercar',
      'Zoom out': 'Alejar', 'Autoscale': 'Ajustar ejes', 'Reset axes': 'Restablecer ejes',
      'Box Select': 'Seleccionar una zona', 'Lasso Select': 'Selección libre',
      'Toggle Spike Lines': 'Mostrar guías', 'Show closest data on hover': 'Mostrar el punto más cercano',
      'Compare data on hover': 'Comparar valores',
      'Double-click on legend to isolate one trace': 'Haz doble clic en la leyenda para aislar una serie',
      'Double-click to zoom back out': 'Haz doble clic para restablecer la vista'
    },
    format: { decimal: ',', thousands: '.', grouping: [3] }
  });
  const config = {
    locale: 'es', displaylogo: false, responsive: false, scrollZoom: false, showTips: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
    toImageButtonOptions: { format: 'png', scale: 2 }
  };

  function layoutFor(state) {
    const layout = clone(state.source.layout);
    const width = Math.floor(state.plot.getBoundingClientRect().width);
    const narrow = width < 680;
    const paired = Boolean(layout.xaxis2);
    delete layout.template;
    delete layout.updatemenus;
    layout.width = width;
    layout.autosize = false;
    layout.paper_bgcolor = '#ffffff';
    layout.plot_bgcolor = '#ffffff';
    layout.font = { family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif', size: 12, color: '#233342' };
    layout.hoverlabel = { bgcolor: '#ffffff', font: { size: 12 }, namelength: -1 };
    layout.legend = { orientation: 'h', x: 0, y: narrow ? -0.14 : -0.20, yanchor: 'top', font: { size: narrow ? 11 : 12 }, groupclick: 'togglegroup' };
    layout.margin = { l: narrow ? 52 : 60, r: narrow ? 12 : 24, t: 48, b: narrow ? 170 : 110 };
    layout.height = narrow ? 850 : 510;
    layout.dragmode = 'zoom';
    layout.uirevision = `${state.name}-${state.selected}`;
    layout.separators = ',.';

    if (state.name === 'epocas') {
      Object.assign(layout, clone(state.presets[state.selected].args[1]));
    }
    if (paired) {
      layout.xaxis.domain = narrow ? [0, 1] : [0, 0.43];
      layout.xaxis2.domain = narrow ? [0, 1] : [0.59, 1];
      layout.yaxis.domain = narrow ? [0.60, 1] : [0, 1];
      layout.yaxis2.domain = narrow ? [0, 0.40] : [0, 1];
      layout.annotations = (layout.annotations || []).map((annotation, i) => {
        if (i > 1) return annotation;
        return { ...annotation, x: i === 0 || narrow ? 0 : 0.59, y: narrow && i === 1 ? 0.46 : 1.07,
          xanchor: 'left', font: { size: 13, color: '#233342' } };
      });
      if (layout.shapes) layout.shapes.forEach((shape, i) => {
        shape.y0 = narrow && i === 0 ? 0.60 : 0;
        shape.y1 = narrow && i === 1 ? 0.40 : 1;
      });
    } else {
      layout.height = narrow ? 850 : 730;
      layout.margin = { l: narrow ? 115 : 130, r: narrow ? 12 : 24, t: 16, b: narrow ? 175 : 100 };
      layout.legend.y = -0.10;
    }

    for (const key of ['xaxis', 'xaxis2', 'yaxis', 'yaxis2']) {
      if (!layout[key]) continue;
      Object.assign(layout[key], {
        gridcolor: '#e7edf2', zerolinecolor: '#dce3e9', linecolor: '#dce3e9',
        tickfont: { size: narrow ? 10 : 11, color: '#526576' }, automargin: true,
        title: { ...layout[key].title, font: { size: 12, color: '#526576' }, standoff: 10 }
      });
    }
    if (state.name === 'grupos') {
      layout.xaxis2.tickvals = ['Falsos positivos', 'Robots perdidos', 'Perdidos difficult'];
      layout.xaxis2.ticktext = ['Falsos<br>positivos', 'Robots<br>perdidos', 'Perdidos<br>difficult'];
      layout.yaxis2.title.text = 'Errores';
    }
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

  function sincronizarExperimento() {
    const state = states.find(item => item.name === 'epocas');
    if (state?.ready && !select.disabled && Number(select.value) !== state.selected) {
      select.dispatchEvent(new Event('change'));
    }
  }

  async function draw(state) {
    state.status.textContent = 'Cargando la figura…';
    state.status.hidden = false;
    try {
      if (!window.Plotly || !state.source) throw new Error('Faltan los recursos locales');
      const data = clone(state.source.data);
      data.forEach(trace => {
        if (trace.line && colors[trace.line.color]) trace.line.color = colors[trace.line.color];
        if (trace.marker && colors[trace.marker.color]) trace.marker.color = colors[trace.marker.color];
      });
      if (state.presets) data.forEach((trace, i) => { trace.visible = state.presets[state.selected].args[0].visible[i]; });
      await Plotly.newPlot(state.plot, data, layoutFor(state), config);
      state.ready = true;
      state.width = Math.floor(state.plot.getBoundingClientRect().width);
      state.status.hidden = true;
      state.stage.querySelectorAll('[data-export]').forEach(button => { button.disabled = false; });
      if (state.presets) {
        select.disabled = false;
        sincronizarExperimento();
      }
    } catch (error) {
      state.ready = false;
      showError(state);
      console.error('No se pudo dibujar ' + state.name, error);
    }
  }

  document.querySelectorAll('[data-figure]').forEach(stage => {
    const name = stage.dataset.figure;
    const source = window.PIDS_BLOQUE2?.[name];
    const state = { name, stage, source, plot: stage.querySelector('.plot'), status: stage.querySelector('.chart-status'), selected: 2, ready: false };
    if (name === 'epocas' && source) {
      state.presets = source.layout.updatemenus[0].buttons;
      state.presets.forEach((preset, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = preset.label;
        option.selected = index === state.selected;
        select.append(option);
      });
      select.addEventListener('change', async () => {
        select.disabled = true;
        state.selected = Number(select.value);
        try {
          await Plotly.update(state.plot, clone(state.presets[state.selected].args[0]), layoutFor(state));
        } catch (error) {
          showError(state);
          console.error(error);
        } finally { select.disabled = false; }
      });
    }
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
  // El historial puede restaurar el selector después de cargar el documento.
  window.addEventListener('pageshow', () => requestAnimationFrame(sincronizarExperimento));
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
  (async () => { for (const state of states) await draw(state); })();
})();
