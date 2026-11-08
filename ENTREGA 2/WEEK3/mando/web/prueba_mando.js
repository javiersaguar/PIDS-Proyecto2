(function () {
  "use strict";
  const nombres = ["✕", "○", "□", "△", "L1", "R1", "L2", "R2", "SHARE", "OPTIONS", "L3", "R3", "↑", "↓", "←", "→", "PS", "TOUCHPAD"];
  const vistos = new Map();
  const el = id => document.getElementById(id);
  let conectado = null;
  function registro(pad) {
    if (!vistos.has(pad.id)) vistos.set(pad.id, {
      botones: pad.buttons.map(() => ({min: 1, max: 0})),
      ejes: pad.axes.map(() => ({min: 1, max: -1})),
      muestras: 0
    });
    return vistos.get(pad.id);
  }
  function construir(pad) {
    el("botones").replaceChildren();
    pad.buttons.forEach((_, i) => {
      const div = document.createElement("div");
      div.className = "boton-pad";
      div.id = "boton-" + i;
      const titulo = document.createElement("strong");
      titulo.textContent = (nombres[i] || "BOTÓN") + " / " + i;
      const valor = document.createElement("small");
      div.append(titulo, valor);
      el("botones").append(div);
    });
    el("ejes").replaceChildren();
    pad.axes.forEach((_, i) => {
      const div = document.createElement("div");
      div.className = "eje";
      div.id = "eje-" + i;
      const titulo = document.createElement("strong");
      titulo.textContent = "EJE " + i + " · " + ["izquierdo X", "izquierdo Y", "derecho X", "derecho Y"][i % 4];
      const barra = document.createElement("progress");
      barra.max = 2;
      barra.setAttribute("aria-label", "Eje " + i);
      const valor = document.createElement("small");
      div.append(titulo, barra, valor);
      el("ejes").append(div);
    });
  }
  function actualizar() {
    let pads = [];
    try { pads = navigator.getGamepads ? [...navigator.getGamepads()].filter(Boolean) : []; }
    catch (_) { el("estado").textContent = "Este navegador no permite leer mandos"; }
    const pad = pads.find(p => p.mapping === "standard") || pads[0];
    if (!pad) {
      el("estado").textContent = conectado ? "Mando desconectado" : "Pulsa un botón del mando";
      conectado = null;
    } else {
      const r = registro(pad);
      r.muestras++;
      if (conectado !== pad.id) construir(pad);
      conectado = pad.id;
      el("estado").textContent = "Mando detectado";
      el("identificador").textContent = pad.id;
      el("mapeo").textContent = "Mapeo " + (pad.mapping || "sin estándar") + " · " + pad.axes.length + " ejes · " + pad.buttons.length + " botones";
      pad.buttons.forEach((b, i) => {
        const valor = b.value;
        const dato = r.botones[i];
        dato.min = Math.min(dato.min, valor);
        dato.max = Math.max(dato.max, valor);
        const celda = el("boton-" + i);
        celda.classList.toggle("pulsado", b.pressed);
        celda.lastChild.textContent = valor.toFixed(2) + " · máx " + dato.max.toFixed(2);
      });
      pad.axes.forEach((v, i) => {
        r.ejes[i].min = Math.min(r.ejes[i].min, v);
        r.ejes[i].max = Math.max(r.ejes[i].max, v);
        const celda = el("eje-" + i);
        celda.querySelector("progress").value = v + 1;
        celda.lastChild.textContent = v.toFixed(3) + " · rango " + r.ejes[i].min.toFixed(2) + " / " + r.ejes[i].max.toFixed(2);
      });
      const estado = i => r.botones[i] && r.botones[i].max > .5 ? "OBSERVADO" : "pendiente";
      const r2 = r.botones[7];
      const ejes = r.ejes.slice(0, 4).map((e, i) => "Eje " + i + " " + (e.min < -.8 && e.max > .8 ? "RECORRIDO COMPLETO" : "pendiente de mover en ambos sentidos"));
      el("resumen").textContent = [
        "Mapeo estándar " + (pad.mapping === "standard" ? "SÍ" : "NO, requiere asignación"),
        ...[0, 1, 2, 3, 8, 9].map(i => nombres[i] + " [" + i + "] " + estado(i)),
        "R2 [7] " + (r2 ? r2.min.toFixed(2) + " → " + r2.max.toFixed(2) : "ausente"),
        ...ejes,
        "Muestras de lectura " + r.muestras
      ].join(String.fromCharCode(10));
    }
    requestAnimationFrame(actualizar);
  }
  actualizar();
})();
