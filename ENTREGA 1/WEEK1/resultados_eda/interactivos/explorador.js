(() => {
  'use strict';
  const frames = [...document.querySelectorAll('iframe')];
  const status = (frame) => frame.parentElement.querySelector('.chart-status');

  frames.forEach((frame) => {
    const message = status(frame);
    function failed() {
      message.replaceChildren('No se ha podido cargar la figura.');
      const retry = document.createElement('a');
      retry.href = '#';
      retry.textContent = 'Reintentar';
      retry.addEventListener('click', (event) => {
        event.preventDefault();
        message.textContent = 'Cargando la figura…';
        frame.hidden = false;
        frame.src = frame.getAttribute('src');
      });
      const direct = document.createElement('a');
      direct.href = frame.getAttribute('src');
      direct.textContent = 'Abrir el archivo';
      message.append(retry, direct);
      message.hidden = false;
      frame.hidden = true;
    }
    frame.addEventListener('load', () => {
      try {
        if (frame.contentDocument && !frame.contentDocument.querySelector('.plotly-graph-div')) return failed();
      } catch { /* El navegador puede aislar los archivos abiertos sin servidor. */ }
      message.hidden = true;
      frame.contentWindow.postMessage({ type: 'pids:request-size' }, '*');
    });
    frame.addEventListener('error', failed);
  });
  window.addEventListener('message', (event) => {
    const frame = frames.find((item) => item.contentWindow === event.source);
    if (!frame || event.data?.type !== 'pids:figure-size') return;
    const height = event.data.height;
    if (typeof height !== 'number' || !Number.isFinite(height) || height < 200 || height > 6000) return;
    frame.height = String(Math.ceil(height));
    status(frame).hidden = true;
  });
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) entry.target.contentWindow.postMessage({ type: 'pids:pause' }, '*');
    });
  });
  frames.forEach((frame) => observer.observe(frame));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) frames.forEach((frame) => frame.contentWindow.postMessage({ type: 'pids:pause' }, '*'));
  });
})();
