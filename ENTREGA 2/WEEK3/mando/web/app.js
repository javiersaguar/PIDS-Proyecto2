(function () {
  "use strict";
  const el = id => document.getElementById(id);
  const nombres = { moonwalk: "Moonwalk", waka: "Waka Waka", superestrella: "Super Estrella", risa: "Risa" };
  const duraciones = { moonwalk: 24.615, waka: 11.681, superestrella: 27.131, risa: 3.15 };
  const defaults = {
    modo: "free", velocidad: .5, angular: 30, automatico: false, asistente: false,
    umbral: .95, intervalo: .3, audio: "ordenador", volumen: .7, volumen_motor: .3,
    motor: true, detector: "gpu", cajas: true, zona_muerta: .15, sensibilidad: 1,
    invertir: false, retardo_ms: 0
  };
  let config = Object.assign({}, defaults);
  try { config = Object.assign(config, JSON.parse(localStorage.getItem("robomaster-config") || "{}")); } catch (_) {}
  let intencionAuto = false;
  config.automatico = false;
  let ws, activo = false, estado = {}, conexionAbierta = false, primerEstado = true;
  let disparos = null, ultimoEmote = null, ultimoMensaje = 0, avisoTemporal = "", avisoHasta = 0;
  let capturaTimer = null, marcaTimer = null, disparoEvento = false;
  const dialogo = el("dialogo");
  const sonido = new AudioRM(mensaje => avisar(mensaje, 6000));
  function avisar(mensaje, duracion = 3500) {
    avisoTemporal = mensaje;
    avisoHasta = performance.now() + duracion;
    el("aviso").textContent = mensaje;
  }
  function enviar(mensaje) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(mensaje));
  }
  function guardar() {
    try { localStorage.setItem("robomaster-config", JSON.stringify(config)); } catch (_) {}
    entrada.asignar(config);
    sonido.configurar(config);
    enviar({ tipo: "config", config: Object.assign({}, config, { automatico: activo && intencionAuto }) });
    el("guardado").textContent = "Cambios enviados al servidor.";
    refrescarFormulario();
  }
  function parar(motivo = "Controles en pausa", conservarAuto = false) {
    activo = false;
    entrada.limpiar();
    if (!conservarAuto) intencionAuto = false;
    config.automatico = intencionAuto;
    enviar({ tipo: "parar" });
    sonido.parar();
    el("control-estado").textContent = motivo;
    el("activar").textContent = "Activar controles";
    el("activar").disabled = !conexionAbierta;
    el("auto").hidden = true;
    el("pantalla").classList.remove("auto-disparando");
    document.querySelectorAll(".emote").forEach(b => { b.disabled = true; });
    refrescarFormulario();
  }
  function abrirAjustes() {
    if (dialogo.open) { dialogo.close(); return; }
    parar("Ajustes abiertos", true);
    refrescarFormulario();
    dialogo.showModal();
  }
  function emote(nombre) {
    if (!activo || dialogo.open || estado.emote) return;
    enviar({ tipo: "emote", nombre });
  }
  function etiquetaTecla(codigo) {
    const especiales = { ArrowUp: "↑", ArrowDown: "↓", ArrowLeft: "←", ArrowRight: "→", Space: "Espacio" };
    return especiales[codigo] || codigo.replace(/^Key|^Digit/, "");
  }
  function etiquetaBoton(i) {
    return ({ 0: "✕", 1: "○", 2: "□", 3: "△", 4: "L1", 5: "R1", 6: "L2", 7: "R2", 8: "SHARE", 9: "OPTIONS" })[i] || "Botón " + i;
  }
  const acciones = {
    adelante: "Adelante", atras: "Atrás", izquierda: "Izquierda", derecha: "Derecha",
    mirar_izquierda: "Mirar a la izquierda", mirar_derecha: "Mirar a la derecha",
    mirar_arriba: "Mirar arriba", mirar_abajo: "Mirar abajo",
    disparo: "Disparar", moonwalk: "Moonwalk", waka: "Waka Waka",
    superestrella: "Super Estrella", risa: "Risa", parar: "Parada", ajustes: "Ajustes"
  };
  function tablaControles() {
    const cuerpo = el("asignaciones");
    cuerpo.replaceChildren();
    for (const [accion, titulo] of Object.entries(acciones)) {
      const fila = document.createElement("tr");
      const tituloCelda = document.createElement("td");
      tituloCelda.textContent = titulo;
      fila.append(tituloCelda);
      for (const tipo of ["teclado", "mando"]) {
        const celda = document.createElement("td");
        const valor = tipo === "teclado" ? entrada.teclas[accion] : entrada.botones[accion];
        if (valor === undefined) {
          celda.textContent = tipo === "teclado" ? "Clic izquierdo" : (accion.startsWith("mirar") ? "Joystick derecho" : "Joystick izquierdo");
        } else {
          const boton = document.createElement("button");
          boton.type = "button";
          boton.textContent = tipo === "teclado" ? etiquetaTecla(valor) : etiquetaBoton(valor);
          boton.setAttribute("aria-label", "Reasignar " + titulo + " en " + tipo);
          boton.addEventListener("click", () => {
            entrada.captura = { tipo, accion };
            el("captura").textContent = "Pulsa " + (tipo === "teclado" ? "una tecla" : "un botón del mando") + " para «" + titulo + "». Esc cancela.";
          });
          celda.append(boton);
        }
        fila.append(celda);
      }
      cuerpo.append(fila);
    }
    for (const b of document.querySelectorAll("[data-tecla]")) b.textContent = etiquetaTecla(entrada.teclas[b.dataset.tecla]);
  }
  function reasignar(accion, tipo, valor) {
    const mapa = Object.assign({}, tipo === "teclado" ? entrada.teclas : entrada.botones);
    const conflicto = Object.keys(mapa).find(k => k !== accion && mapa[k] === valor);
    if (conflicto) {
      el("captura").textContent = "Ese control ya está asignado a «" + acciones[conflicto] + "». Elige otro.";
      return;
    }
    config.controles = Object.assign({}, config.controles);
    mapa[accion] = valor;
    config.controles[tipo] = mapa;
    el("captura").textContent = "Control reasignado.";
    guardar();
    tablaControles();
  }
  const entrada = new ControlRM.Entrada({
    superficie: el("video"),
    bloqueado: () => dialogo.open,
    activo: () => activo && conexionAbierta && !dialogo.open && !document.hidden && !estado.emote,
    parar, ajustes: abrirAjustes, emote, reasignar,
    mando: pad => {
      el("mando-estado").textContent = pad ? (pad.mapping === "standard" ? "Mando conectado / estándar" : "Mando sin mapeo estándar / abre la prueba") : "Pulsa un botón del mando";
      el("mando-estado").title = pad ? pad.id : "Conecta por USB o Bluetooth y pulsa un botón";
    }
  });
  entrada.asignar(config);
  sonido.configurar(config);
  function refrescarFormulario() {
    for (const campo of document.querySelectorAll("[data-config]")) {
      const valor = config[campo.dataset.config];
      if (campo.type === "checkbox") campo.checked = !!valor;
      else if (valor !== undefined) campo.value = valor;
    }
    el("opcion-fps").disabled = !config.fps_habilitado;
  }
  function marcaDisparo() {
    el("reticula").classList.add("disparando");
    if (estado.automatico) el("pantalla").classList.add("auto-disparando");
    clearTimeout(marcaTimer);
    marcaTimer = setTimeout(() => {
      el("reticula").classList.remove("disparando");
      el("pantalla").classList.remove("auto-disparando");
    }, 150);
  }
  function recibir(nuevo) {
    if (nuevo.tipo === "error") {
      avisar(nuevo.mensaje || "Orden rechazada por el servidor", 6000);
      parar("Orden rechazada");
      return;
    }
    if (nuevo.tipo === "disparo") {
      disparoEvento = true;
      marcaDisparo();
      sonido.tocar("scar");
      return;
    }
    if (nuevo.tipo === "fin_emote") { sonido.pararEmote(); ultimoEmote = null; return; }
    if (nuevo.tipo === "emote") {
      if (nuevo.nombre !== ultimoEmote) {
        ultimoEmote = nuevo.nombre;
        sonido.baile(nuevo.nombre);
        avisar(nombres[nuevo.nombre] || nuevo.nombre);
      }
      return;
    }
    if (nuevo.tipo !== "estado") return;
    ultimoMensaje = performance.now();
    estado = nuevo;
    if (nuevo.config) {
      config = Object.assign({}, defaults, nuevo.config);
      config.automatico = intencionAuto;
      entrada.asignar(config);
      sonido.configurar(config);
      refrescarFormulario();
      if (primerEstado) tablaControles();
    }
    primerEstado = false;
    el("bateria").textContent = Number.isFinite(nuevo.bateria) ? nuevo.bateria + " %" : "—";
    el("bateria").style.color = nuevo.bateria < 20 ? "#ffbc72" : "";
    el("fps").textContent = Number(nuevo.fps || 0).toFixed(1) + " fps";
    el("detector").textContent = nuevo.detector || "Sin detector";
    el("inferencia").textContent = Number.isFinite(nuevo.ms_detector) ? Math.round(nuevo.ms_detector) + " ms" : "— ms";
    const antiguedad = nuevo.edad_frame_ms ?? nuevo.age_ms ?? nuevo.retraso_ms;
    el("retraso").textContent = Number.isFinite(antiguedad) ? Math.round(antiguedad) + " ms" : "Sin medir";
    el("modo").textContent = nuevo.modo === "fps" ? "FPS" : "LIBRE";
    el("auto").hidden = !nuevo.automatico;
    el("angulos").textContent = "YAW " + Number(nuevo.yaw || 0).toFixed(1) + "° · PITCH " + Number(nuevo.pitch || 0).toFixed(1) + "°";
    el("velocidad").textContent = Math.hypot(...(nuevo.velocidad || [0, 0])).toFixed(2) + " m/s";
    if (disparos !== null && nuevo.disparos > disparos) {
      marcaDisparo();
      // El audio se sincroniza con el evento de disparo, sin duplicarlo por el recuento.
    }
    disparos = nuevo.disparos || 0;
    if (!nuevo.emote && ultimoEmote) { sonido.pararEmote(); ultimoEmote = null; }
    if (nuevo.emote && nuevo.emote !== ultimoEmote) {
      ultimoEmote = nuevo.emote;
      sonido.baile(nuevo.emote, Number(nuevo.progreso || 0), duraciones[nuevo.emote] || 0);
      avisar(nombres[nuevo.emote] || nuevo.emote);
    }
    const progreso = Math.max(0, Math.min(1, Number(nuevo.progreso || 0)));
    el("progreso").value = progreso;
    el("baile-nombre").textContent = nuevo.emote ? (nombres[nuevo.emote] || nuevo.emote) + " · " + Math.round(progreso * 100) + " %" : "Emotes";
    for (const b of document.querySelectorAll(".emote")) {
      b.classList.toggle("activo", nuevo.emote === b.dataset.emote);
      b.disabled = !activo || !!nuevo.emote;
    }
    if (nuevo.error) {
      avisar(nuevo.error, 6000);
      if (activo) parar("Error del robot");
    }
    el("detector-ayuda").textContent = nuevo.aviso || "Detector en proceso independiente. Su estado aparece en el HUD.";
    sonido.mover(activo ? nuevo.velocidad || [0, 0] : [0, 0]);
  }
  function conectar() {
    el("conexion").textContent = "Conectando con el robot…";
    ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
    ws.addEventListener("open", () => {
      conexionAbierta = true;
      primerEstado = true;
      disparos = null;
      disparoEvento = false;
      ultimoMensaje = performance.now();
      el("conexion").textContent = "Servidor conectado";
      el("conexion-luz").className = "luz conectada";
      el("activar").disabled = false;
      enviar({ tipo: "parar" });
    });
    ws.addEventListener("message", e => {
      try { recibir(JSON.parse(e.data)); } catch (_) { avisar("Mensaje de estado no válido"); }
    });
    ws.addEventListener("close", () => {
      conexionAbierta = false;
      parar("Conexión perdida");
      el("conexion").textContent = "Sin conexión · reintentando";
      el("conexion-luz").className = "luz error";
      setTimeout(conectar, 2000);
    });
    ws.addEventListener("error", () => { el("conexion").textContent = "Error de conexión con el servidor"; });
  }
  el("activar").addEventListener("click", async () => {
    try { await sonido.activar(); } catch (_) { avisar("El navegador no pudo activar el audio"); }
    if (!conexionAbierta || estado.error || estado.listo === false || dialogo.open) {
      if (estado.listo === false) avisar(estado.aviso || "Preparando el robot y sus audios");
      return;
    }
    entrada.limpiar();
    activo = true;
    config.automatico = intencionAuto;
    enviar(Object.assign({ tipo: "activar", config }, ControlRM.vacio()));
    el("control-estado").textContent = "Controles activos";
    el("activar").textContent = "Controles activos";
    for (const b of document.querySelectorAll(".emote")) b.disabled = !!estado.emote;
  });
  el("parar").addEventListener("click", () => parar("Parada de emergencia"));
  el("ajustes").addEventListener("click", abrirAjustes);
  const cerrarAjustes = () => { dialogo.close(); entrada.captura = null; el("captura").textContent = ""; };
  el("cerrar-ajustes").addEventListener("click", cerrarAjustes);
  el("hecho").addEventListener("click", cerrarAjustes);
  dialogo.addEventListener("cancel", () => { entrada.captura = null; parar("Controles en pausa"); });
  for (const boton of document.querySelectorAll("[data-panel]")) {
    boton.addEventListener("click", () => {
      for (const b of document.querySelectorAll("[data-panel]")) b.classList.toggle("seleccionada", b === boton);
      for (const panel of document.querySelectorAll(".panel-ajustes")) panel.hidden = panel.id !== "panel-" + boton.dataset.panel;
    });
  }
  for (const campo of document.querySelectorAll("[data-config]")) {
    campo.addEventListener("change", () => {
      if (!campo.checkValidity()) { campo.reportValidity(); return; }
      config[campo.dataset.config] = campo.type === "checkbox" ? campo.checked :
        (campo.type === "number" || campo.type === "range" ? Number(campo.value) : campo.value);
      if (campo.dataset.config === "automatico") intencionAuto = campo.checked;
      guardar();
    });
  }
  el("restablecer").addEventListener("click", () => { delete config.controles; guardar(); tablaControles(); });
  for (const b of document.querySelectorAll(".emote")) b.addEventListener("click", () => emote(b.dataset.emote));
  el("pantalla-completa").addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await el("cabina").requestFullscreen();
    } catch (_) { avisar("Pantalla completa no disponible"); }
  });
  window.addEventListener("blur", () => parar("Ventana en segundo plano"));
  document.addEventListener("visibilitychange", () => { if (document.hidden) parar("Pestaña oculta"); });
  window.addEventListener("pagehide", () => { parar("Página cerrada"); if (ws) ws.close(); });
  el("video").addEventListener("error", () => avisar("Esperando vídeo del robot", 5000));
  setInterval(() => {
    if (activo && performance.now() - ultimoMensaje > 1500) parar("Sin estado del servidor");
    if (activo && !document.hidden && !dialogo.open) enviar(Object.assign({ tipo: "control" }, entrada.leer()));
    if (performance.now() >= avisoHasta) el("aviso").textContent = estado.aviso || "";
  }, 50);
  function dibujar() {
    const canvas = el("cajas"), video = el("video");
    const rect = video.getBoundingClientRect();
    const escala = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(rect.width * escala) || canvas.height !== Math.round(rect.height * escala)) {
      canvas.width = Math.round(rect.width * escala); canvas.height = Math.round(rect.height * escala);
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(escala, 0, 0, escala, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);
    const d = estado.deteccion;
    if (config.cajas && d && d.width > 0 && d.height > 0) {
      const factor = Math.min(rect.width / d.width, rect.height / d.height);
      const izq = (rect.width - d.width * factor) / 2, arriba = (rect.height - d.height * factor) / 2;
      ctx.lineWidth = 1.5; ctx.font = "12px Segoe UI";
      (d.boxes || []).forEach((b, i) => {
        const confianza = Number((d.scores || [])[i] || 0);
        if (confianza < .3) return;
        const x = izq + b[0] * factor, y = arriba + b[1] * factor;
        const color = confianza >= Number(config.umbral || .95) ? "#83e8c0" : "#ffba72";
        ctx.strokeStyle = color; ctx.strokeRect(x, y, (b[2] - b[0]) * factor, (b[3] - b[1]) * factor);
        const texto = "ROBOT " + (confianza * 100).toFixed(1) + "%";
        const ancho = ctx.measureText(texto).width + 10;
        ctx.fillStyle = "#101b24e8"; ctx.fillRect(x, Math.max(arriba, y - 22), ancho, 20);
        ctx.fillStyle = color; ctx.fillText(texto, x + 5, Math.max(arriba + 14, y - 8));
      });
    }
    requestAnimationFrame(dibujar);
  }
  tablaControles();
  refrescarFormulario();
  el("activar").disabled = true;
  for (const b of document.querySelectorAll(".emote")) b.disabled = true;
  conectar();
  dibujar();
})();


