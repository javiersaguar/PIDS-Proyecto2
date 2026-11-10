(function () {
  "use strict";
  const el = id => document.getElementById(id);
  const nombres = { moonwalk: "Moonwalk", waka: "Waka Waka", superestrella: "Super Estrella", risa: "Risa" };
  const canciones = { moonwalk: "Billie Jean", waka: "Shakira · bandera de España", superestrella: "Aitana", risa: "Gato" };
  const duraciones = { moonwalk: 24.615, waka: 11.681, superestrella: 27.131, risa: 3.15 };
  const defaults = {
    modo: "free", velocidad: .5, angular: 30, automatico: false, asistente: false,
    umbral: .95, intervalo: .3, audio: "ordenador", volumen: .7, volumen_motor: .3,
    motor: true, detector: "gpu", cajas: true, zona_muerta: .15, sensibilidad: 1,
    invertir: false, retardo_ms: 0, relativo_camara: true
  };
  let config = Object.assign({}, defaults);
  try { config = Object.assign(config, JSON.parse(localStorage.getItem("robomaster-config") || "{}")); } catch (_) {}
  // Preferencias de la pantalla: solo de este navegador, el servidor no las necesita.
  const interfaz = { vista: "teclado", vibracion: true, atenuar: true };
  try { Object.assign(interfaz, JSON.parse(localStorage.getItem("robomaster-interfaz") || "{}")); } catch (_) {}
  if (interfaz.vista !== "mando") interfaz.vista = "teclado";
  let intencionAuto = false;
  config.automatico = false;
  let ws, activo = false, estado = {}, conexionAbierta = false, primerEstado = true;
  let disparos = null, ultimoEmote = null, ultimoMensaje = 0, avisoTemporal = "", avisoHasta = 0;
  let marcaTimer = null, activadoEn = 0;
  let cartelTimer = null, rafagaTimer = null, rafaga = 0, ultimoUso = performance.now(), habiaMando = false;
  const dialogo = el("dialogo");
  const sonido = new AudioRM(mensaje => avisar(mensaje, 6000));

  // Lo que dibuja la escena 3D (escena3d.js lo lee en cada fotograma).
  const HUD = window.HUD = {
    vista: interfaz.vista,
    activo: false,
    pad: { conectado: false, estandar: false, ejes: [0, 0, 0, 0], botones: [] },
    teclas: {}, raton: false,
    etiquetas: {}, version: 0,
    robot: { yaw: 0, pitch: 0, velocidad: [0, 0], girar: 0 },
    emote: null, disparoEn: -1e9, sin3d: false
  };

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
  function guardarInterfaz() {
    try { localStorage.setItem("robomaster-interfaz", JSON.stringify(interfaz)); } catch (_) {}
  }
  function vibrar(duracion, fuerte, debil) {
    if (!interfaz.vibracion || !navigator.getGamepads) return;
    for (const pad of navigator.getGamepads()) {
      if (!pad || !pad.connected || !pad.vibrationActuator || !pad.vibrationActuator.playEffect) continue;
      pad.vibrationActuator.playEffect("dual-rumble", {
        duration: duracion, strongMagnitude: fuerte, weakMagnitude: debil
      }).catch(() => {});
    }
  }

  // --- vista: qué se dibuja en pantalla, el teclado o el mando ---------------------------
  function ponerVista(vista, recordar = true) {
    interfaz.vista = HUD.vista = vista === "mando" ? "mando" : "teclado";
    if (recordar) guardarInterfaz();
    for (const b of document.querySelectorAll("[data-vista]")) {
      b.classList.toggle("seleccionada", b.dataset.vista === interfaz.vista);
      b.setAttribute("aria-pressed", String(b.dataset.vista === interfaz.vista));
    }
    estadoMando();
  }
  function uso() {
    ultimoUso = performance.now();
    el("cabina").classList.remove("en-reposo");
  }
  let padActual = null;
  function estadoMando() {
    const pad = padActual;
    let texto;
    if (interfaz.vista === "teclado") texto = pad ? "Teclado · mando conectado" : "Teclado y ratón";
    else if (!pad) texto = "Pulsa un botón del mando";
    else texto = pad.mapping === "standard" ? "Mando conectado" : "Mando sin mapeo estándar · abre la prueba";
    if (el("mando-estado").textContent !== texto) el("mando-estado").textContent = texto;
    const id = pad ? pad.id : "Sin mando";
    if (el("tele-mando").textContent !== id) el("tele-mando").textContent = id;
  }

  // --- carteles: lo que acaba de lanzar un botón o una tecla ------------------------------
  const clasesPS = { 0: "equis", 1: "circulo", 2: "cuadrado", 3: "triangulo" };
  function simboloDe(accion, destino) {
    destino.className = "cartel-simbolo";
    if (interfaz.vista === "mando" && entrada.botones[accion] !== undefined) {
      const boton = entrada.botones[accion];
      destino.textContent = etiquetaBoton(boton);
      destino.classList.add(clasesPS[boton] ? "ps" : "tecla");
      if (clasesPS[boton]) destino.classList.add(clasesPS[boton]);
    } else {
      destino.textContent = accion === "disparo" ? "CLIC" : etiquetaTecla(entrada.teclas[accion] || "");
      destino.classList.add("tecla");
    }
  }
  function cartel(accion, titulo, sub, clase, duracion) {
    const c = el("cartel");
    clearTimeout(cartelTimer);
    simboloDe(accion, el("cartel-simbolo"));
    el("cartel-titulo").textContent = titulo;
    el("cartel-sub").textContent = sub || "";
    c.className = "cartel " + (clase || "");
    c.hidden = false;
    // Reinicia la animación de entrada
    void c.offsetWidth;
    c.classList.add("visible");
    if (clase === "emote") cartelTimer = setTimeout(() => c.classList.add("compacto"), 2600);
    else cartelTimer = setTimeout(quitarCartel, duracion || 1400);
  }
  function quitarCartel() {
    clearTimeout(cartelTimer);
    el("cartel").hidden = true;
    el("cartel").className = "cartel";
  }
  function cartelEmote(nombre) {
    cartel(nombre, nombres[nombre] || nombre, canciones[nombre], "emote");
  }
  function marcarRafaga(automatico) {
    rafaga++;
    const control = el("rafaga-control");
    if (automatico) control.textContent = "AUTO";
    else control.textContent = interfaz.vista === "mando" ? etiquetaBoton(entrada.botones.disparo) : "CLIC";
    el("rafaga-cuenta").textContent = "×" + rafaga;
    el("rafaga").hidden = false;
    clearTimeout(rafagaTimer);
    rafagaTimer = setTimeout(() => { el("rafaga").hidden = true; rafaga = 0; }, 900);
  }

  function parar(motivo = "Controles en pausa", conservarAuto = false) {
    const estabaActivo = activo;
    activo = HUD.activo = false;
    entrada.limpiar();
    if (!conservarAuto) intencionAuto = false;
    config.automatico = intencionAuto;
    enviar({ tipo: "parar" });
    sonido.parar();
    el("control-estado").textContent = motivo;
    el("cabina").classList.remove("activo", "en-reposo");
    el("activar").disabled = !conexionAbierta;
    el("auto").hidden = true;
    el("pantalla").classList.remove("auto-disparando");
    if (estabaActivo && /emergencia|SHARE/.test(motivo)) {
      cartel("parar", "Parada", "Controles en pausa", "parada", 1600);
      vibrar(220, .9, .4);
    }
    refrescarFormulario();
  }
  function abrirAjustes(origen) {
    if (dialogo.open) { dialogo.close(); return; }
    parar("Ajustes abiertos", true);
    refrescarFormulario();
    const marca = el("origen-ajustes");
    marca.hidden = !origen;
    if (origen) {
      marca.textContent = origen === "mando" ? etiquetaBoton(entrada.botones.ajustes) : etiquetaTecla(entrada.teclas.ajustes);
      marca.classList.remove("destello");
      void marca.offsetWidth;
      marca.classList.add("destello");
    }
    dialogo.showModal();
  }
  function emote(nombre) {
    if (!activo || dialogo.open || estado.emote) return;
    enviar({ tipo: "emote", nombre });
  }
  function etiquetaTecla(codigo) {
    const especiales = { ArrowUp: "↑", ArrowDown: "↓", ArrowLeft: "←", ArrowRight: "→", Space: "Espacio", Tab: "Tab" };
    return especiales[codigo] || String(codigo).replace(/^Key|^Digit/, "");
  }
  function etiquetaBoton(i) {
    return ({ 0: "✕", 1: "○", 2: "□", 3: "△", 4: "L1", 5: "R1", 6: "L2", 7: "R2", 8: "SHARE", 9: "OPTIONS" })[i] || "Botón " + i;
  }
  const acciones = {
    adelante: "Adelante", atras: "Atrás", izquierda: "Izquierda", derecha: "Derecha",
    mirar_izquierda: "Mirar a la izquierda", mirar_derecha: "Mirar a la derecha",
    mirar_arriba: "Mirar arriba", mirar_abajo: "Mirar abajo",
    girar_izquierda: "Girar el chasis a la izquierda", girar_derecha: "Girar el chasis a la derecha",
    disparo: "Disparar", moonwalk: "Moonwalk", waka: "Waka Waka",
    superestrella: "Super Estrella", risa: "Risa", parar: "Parada", ajustes: "Ajustes"
  };
  // Etiquetas de las teclas y botones asignados, para dibujarlas en la escena 3D.
  function publicarEtiquetas() {
    const teclado = {}, mando = {};
    for (const accion of Object.keys(acciones)) {
      if (entrada.teclas[accion] !== undefined) teclado[accion] = etiquetaTecla(entrada.teclas[accion]);
      if (entrada.botones[accion] !== undefined) mando[accion] = entrada.botones[accion];
    }
    HUD.etiquetas = { teclado, mando };
    HUD.version++;
  }
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
    publicarEtiquetas();
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
    parar, emote, reasignar,
    ajustes: () => abrirAjustes(entrada.fuente || "teclado"),
    fuente: fuente => ponerVista(fuente),
    mando: pad => {
      padActual = pad;
      const p = HUD.pad;
      p.conectado = !!pad;
      p.estandar = !!pad && pad.mapping === "standard";
      if (pad) {
        for (let i = 0; i < 4; i++) p.ejes[i] = Number(pad.axes[i]) || 0;
        p.botones = pad.buttons.map(b => b.value);
        if (p.botones.some(v => v > .5) || p.ejes.some(a => Math.abs(a) > .35)) uso();
      } else {
        p.ejes = [0, 0, 0, 0];
        p.botones = [];
      }
      if (!!pad !== habiaMando) {
        habiaMando = !!pad;
        ponerVista(pad ? "mando" : "teclado", false);
        if (pad) vibrar(120, .3, .6);
      }
      estadoMando();
    }
  });
  entrada.asignar(config);
  sonido.configurar(config);

  // Teclas pulsadas, para dibujarlas aunque los controles estén en pausa.
  function teclaVista(e, abajo) {
    if (dialogo.open) return;
    for (const [accion, codigo] of Object.entries(entrada.teclas)) {
      if (codigo === e.code) HUD.teclas[accion] = abajo;
    }
    if (abajo) uso();
  }
  document.addEventListener("keydown", e => teclaVista(e, true));
  document.addEventListener("keyup", e => teclaVista(e, false));
  el("video").addEventListener("mousedown", e => { if (e.button === 0) { HUD.raton = true; uso(); } });
  window.addEventListener("mouseup", () => { HUD.raton = false; });
  window.addEventListener("mousemove", uso);

  function refrescarFormulario() {
    for (const campo of document.querySelectorAll("[data-config]")) {
      const valor = config[campo.dataset.config];
      if (campo.type === "checkbox") campo.checked = !!valor;
      else if (valor !== undefined) campo.value = valor;
    }
    for (const campo of document.querySelectorAll("[data-interfaz]")) campo.checked = !!interfaz[campo.dataset.interfaz];
    el("opcion-fps").disabled = !config.fps_habilitado;
  }
  function marcaDisparo() {
    HUD.disparoEn = performance.now();
    el("reticula").classList.add("disparando");
    if (estado.automatico) el("pantalla").classList.add("auto-disparando");
    clearTimeout(marcaTimer);
    marcaTimer = setTimeout(() => {
      el("reticula").classList.remove("disparando");
      el("pantalla").classList.remove("auto-disparando");
    }, 150);
  }
  function nivel(elemento, alerta, critico) {
    elemento.classList.toggle("alerta", alerta && !critico);
    elemento.classList.toggle("critico", critico);
  }
  function finEmote() {
    sonido.pararEmote();
    ultimoEmote = null;
    estado.emote = null;
    HUD.emote = null;
    quitarCartel();
    vibrar(160, .2, .7);
  }
  function inicioEmote(nombre, progreso) {
    ultimoEmote = nombre;
    const duracion = duraciones[nombre] || 0;
    HUD.emote = { nombre, inicio: performance.now() - Number(progreso || 0) * duracion * 1000 };
    sonido.baile(nombre, Number(progreso || 0), duracion);
    cartelEmote(nombre);
  }
  function recibir(nuevo) {
    if (nuevo.tipo === "error") {
      avisar(nuevo.mensaje || "Orden rechazada por el servidor", 6000);
      parar("Orden rechazada");
      return;
    }
    if (nuevo.tipo === "disparo") {
      marcaDisparo();
      marcarRafaga(!!estado.automatico);
      sonido.tocar("scar");
      vibrar(70, .5, .9);
      return;
    }
    if (nuevo.tipo === "fin_emote") {
      // Los controles siguen activos: se vuelve a conducir sin pulsar Activar.
      finEmote();
      return;
    }
    if (nuevo.tipo === "desarmado") {
      if (activo) parar("Controles desactivados en el robot: " + (nuevo.motivo || "sin órdenes") + ". Pulsa «Activar controles».");
      return;
    }
    if (nuevo.tipo === "aviso") { avisar(nuevo.mensaje || "Aviso del robot", 5000); return; }
    if (nuevo.tipo === "emote") {
      if (nuevo.nombre !== ultimoEmote) inicioEmote(nuevo.nombre, 0);
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
      // Con los ajustes abiertos no se pisa lo que se está editando
      if (!dialogo.open) refrescarFormulario();
      if (primerEstado) tablaControles();
    }
    primerEstado = false;
    const bateria = Number.isFinite(nuevo.bateria) ? nuevo.bateria + " %" : "—";
    el("bateria").textContent = el("tele-bateria").textContent = bateria;
    nivel(el("dato-bateria"), nuevo.bateria < 20, nuevo.bateria < 10);
    const fps = Number(nuevo.fps || 0);
    el("fps").textContent = el("tele-fps").textContent = fps.toFixed(1).replace(".", ",") + " fps";
    nivel(el("dato-fps"), fps < 10, fps < 4);
    el("detector").textContent = nuevo.detector || "Sin detector";
    el("inferencia").textContent = Number.isFinite(nuevo.ms_detector) ? Math.round(nuevo.ms_detector) + " ms" : "— ms";
    const antiguedad = nuevo.edad_frame_ms ?? nuevo.age_ms ?? nuevo.retraso_ms;
    el("retraso").textContent = Number.isFinite(antiguedad) ? Math.round(antiguedad) + " ms" : "Sin medir";
    // La edad de la detección solo sube a la tira cuando es un problema
    const vieja = Number.isFinite(antiguedad) && antiguedad > 1000;
    el("dato-retraso").hidden = !vieja;
    if (vieja) {
      el("retraso-tira").textContent = (antiguedad / 1000).toFixed(1) + " s";
      nivel(el("dato-retraso"), true, antiguedad > 3000);
    }
    el("modo").textContent = nuevo.modo === "fps" ? "FPS" : "LIBRE";
    el("auto").hidden = !nuevo.automatico;
    const grados = v => ((Math.round(Number(v || 0) * 10) / 10) || 0).toFixed(1).replace(".", ",") + "°";
    const angulos = "YAW " + grados(nuevo.yaw) + " · PITCH " + grados(nuevo.pitch);
    el("angulos").textContent = el("tele-angulos").textContent = angulos;
    el("velocidad").textContent = Math.hypot(...(nuevo.velocidad || [0, 0])).toFixed(2).replace(".", ",") + " m/s";
    HUD.robot.yaw = Number(nuevo.yaw || 0);
    HUD.robot.pitch = Number(nuevo.pitch || 0);
    HUD.robot.velocidad = nuevo.velocidad || [0, 0];
    if (disparos !== null && nuevo.disparos > disparos) marcaDisparo();
    disparos = nuevo.disparos || 0;
    el("tele-disparos").textContent = disparos;
    if (!nuevo.emote && ultimoEmote) finEmote();
    if (nuevo.emote && nuevo.emote !== ultimoEmote) inicioEmote(nuevo.emote, nuevo.progreso);
    el("progreso").value = Math.max(0, Math.min(1, Number(nuevo.progreso || 0)));
    // Red de seguridad por si se pierde el aviso: el robot ya no obedece.
    if (activo && nuevo.armado === false && performance.now() - activadoEn > 1500) {
      parar("Controles desactivados en el robot. Pulsa «Activar controles».");
    }
    if (nuevo.error) {
      avisar(nuevo.error, 6000);
      if (activo) parar("Error del robot");
    }
    el("detector-ayuda").textContent = nuevo.aviso || "Detector en proceso independiente. Su estado está en la pestaña Telemetría.";
    sonido.mover(activo ? nuevo.velocidad || [0, 0] : [0, 0]);
  }
  function conectar() {
    el("conexion").textContent = "Conectando con el robot…";
    ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
    ws.addEventListener("open", () => {
      conexionAbierta = true;
      primerEstado = true;
      disparos = null;
      ultimoMensaje = performance.now();
      el("conexion").textContent = "Conectado";
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
      // Una página que se está cerrando no reconecta: le quitaría la sesión a la nueva
      if (!saliendo) setTimeout(conectar, 2000);
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
    activo = HUD.activo = true;
    activadoEn = performance.now();
    config.automatico = intencionAuto;
    enviar(Object.assign({ tipo: "activar", config }, ControlRM.vacio()));
    el("control-estado").textContent = "Controles activos";
    el("cabina").classList.add("activo");
    el("activar").blur();
    uso();
  });
  el("parar").addEventListener("click", () => parar("Parada de emergencia"));
  el("ajustes").addEventListener("click", () => abrirAjustes());
  const cerrarAjustes = () => { dialogo.close(); entrada.captura = null; el("captura").textContent = ""; };
  el("cerrar-ajustes").addEventListener("click", cerrarAjustes);
  el("hecho").addEventListener("click", cerrarAjustes);
  dialogo.addEventListener("cancel", () => { entrada.captura = null; parar("Controles en pausa"); });
  dialogo.addEventListener("close", () => { HUD.teclas = {}; });
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
  for (const campo of document.querySelectorAll("[data-interfaz]")) {
    campo.addEventListener("change", () => {
      interfaz[campo.dataset.interfaz] = campo.checked;
      guardarInterfaz();
      if (campo.dataset.interfaz === "vibracion" && campo.checked) vibrar(150, .4, .8);
      if (!interfaz.atenuar) el("cabina").classList.remove("en-reposo");
    });
  }
  for (const b of document.querySelectorAll("[data-vista]")) b.addEventListener("click", () => ponerVista(b.dataset.vista));
  el("restablecer").addEventListener("click", () => { delete config.controles; guardar(); tablaControles(); });
  el("pantalla-completa").addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await el("cabina").requestFullscreen();
    } catch (_) { avisar("Pantalla completa no disponible"); }
  });
  window.addEventListener("blur", () => { HUD.teclas = {}; HUD.raton = false; parar("Ventana en segundo plano"); });
  document.addEventListener("visibilitychange", () => { if (document.hidden) parar("Pestaña oculta"); });
  let saliendo = false;
  window.addEventListener("pagehide", () => { saliendo = true; parar("Página cerrada"); if (ws) ws.close(); });
  // Si el navegador recupera la página (botón Atrás), vuelve a conectar
  window.addEventListener("pageshow", e => { if (e.persisted && saliendo) { saliendo = false; conectar(); } });
  el("video").addEventListener("error", () => avisar("Esperando vídeo del robot", 5000));
  setInterval(() => {
    const ahora = performance.now();
    if (activo && ahora - ultimoMensaje > 1500) parar("Sin estado del servidor");
    if (activo && !document.hidden && !dialogo.open) {
      const orden = entrada.leer();
      HUD.robot.girar = orden.girar || 0;
      enviar(Object.assign({ tipo: "control" }, orden));
    } else HUD.robot.girar = 0;
    if (ahora >= avisoHasta) el("aviso").textContent = estado.aviso || "";
    // Sin tocar nada, los controles dibujados se atenúan para dejar ver la cámara
    if (interfaz.atenuar && activo && !estado.emote && ahora - ultimoUso > 4000) el("cabina").classList.add("en-reposo");
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
  ponerVista(interfaz.vista, false);
  el("activar").disabled = true;
  conectar();
  dibujar();
})();
