/* Controles normalizados. El servidor aplica los límites físicos. */
(function (global) {
  "use strict";
  const teclas = {
    adelante: "KeyW", atras: "KeyS", izquierda: "KeyA", derecha: "KeyD",
    mirar_izquierda: "ArrowLeft", mirar_derecha: "ArrowRight",
    mirar_arriba: "ArrowUp", mirar_abajo: "ArrowDown",
    girar_izquierda: "KeyZ", girar_derecha: "KeyX",
    moonwalk: "KeyQ", waka: "KeyE", superestrella: "KeyF", risa: "KeyC",
    parar: "Space", ajustes: "Tab"
  };
  const botones = {
    disparo: 7, girar_izquierda: 4, girar_derecha: 5, moonwalk: 2, waka: 3, superestrella: 1, risa: 0, parar: 8, ajustes: 9
  };
  function curva(valor, zona) {
    const v = Math.max(-1, Math.min(1, Number(valor) || 0));
    const magnitud = Math.max(0, (Math.abs(v) - zona) / (1 - zona));
    return Math.sign(v) * magnitud * magnitud;
  }
  function mayor(a, b) { return Math.abs(a) >= Math.abs(b) ? a : b; }
  function combinar(teclado, mando) {
    return {
      mover: teclado.mover.map((v, i) => mayor(v, mando.mover[i])),
      mirar: teclado.mirar.map((v, i) => mayor(v, mando.mirar[i])),
      disparo: teclado.disparo || mando.disparo,
      girar: mayor(teclado.girar || 0, mando.girar || 0)
    };
  }
  function vacio() { return { mover: [0, 0], mirar: [0, 0], disparo: false, girar: 0 }; }
  // Botones que se mantienen pulsados: se leen en cada ciclo, no al pulsarlos.
  const mantenidos = ["disparo", "girar_izquierda", "girar_derecha"];
  function editable(elemento) {
    return elemento && (elemento.isContentEditable || /INPUT|SELECT|TEXTAREA/.test(elemento.tagName));
  }
  class Entrada {
    constructor(opciones) {
      this.opciones = opciones;
      this.pulsadas = new Set();
      this.raton = false;
      this.anterior = [];
      this.juego = vacio();
      this.captura = null;
      this.config = {};
      this.fuente = null;
      this.asignar({});
      document.addEventListener("keydown", e => this.tecla(e, true));
      document.addEventListener("keyup", e => this.tecla(e, false));
      opciones.superficie.addEventListener("mousedown", e => {
        if (e.button === 0 && opciones.activo()) { this.raton = true; this.usada("teclado"); e.preventDefault(); }
      });
      window.addEventListener("mouseup", () => { this.raton = false; });
      window.addEventListener("gamepaddisconnected", () => opciones.parar("Mando desconectado"));
      this.leerMando = this.leerMando.bind(this);
      requestAnimationFrame(this.leerMando);
    }
    asignar(config) {
      this.config = config;
      this.teclas = Object.assign({}, teclas, config.controles && config.controles.teclado);
      this.botones = Object.assign({}, botones, config.controles && config.controles.mando);
    }
    // Último dispositivo usado (teclado o mando), para dibujar sus controles en pantalla.
    usada(fuente) {
      if (this.fuente === fuente) return;
      this.fuente = fuente;
      if (this.opciones.fuente) this.opciones.fuente(fuente);
    }
    limpiar() {
      this.pulsadas.clear();
      this.raton = false;
      this.juego = vacio();
    }
    tecla(e, abajo) {
      if (this.captura && this.captura.tipo === "teclado" && abajo) {
        e.preventDefault();
        if (e.code !== "Escape") this.opciones.reasignar(this.captura.accion, "teclado", e.code);
        this.captura = null;
        return;
      }
      if (e.code === "Escape" && abajo) {
        this.opciones.parar("Parada de emergencia");
        return;
      }
      if (editable(e.target) || (this.opciones.bloqueado && this.opciones.bloqueado())) return;
      if (!Object.values(this.teclas).includes(e.code)) return;
      e.preventDefault();
      if (!abajo) { this.pulsadas.delete(e.code); return; }
      if (e.repeat) return;
      this.usada("teclado");
      if (e.code === this.teclas.parar) { this.opciones.parar("Parada de emergencia"); return; }
      if (e.code === this.teclas.ajustes) { this.opciones.ajustes(); return; }
      if (!this.opciones.activo()) return;
      this.pulsadas.add(e.code);
      for (const nombre of ["moonwalk", "waka", "superestrella", "risa"]) {
        if (e.code === this.teclas[nombre]) this.opciones.emote(nombre);
      }
    }
    leerMando() {
      const disponibles = navigator.getGamepads ? [...navigator.getGamepads()].filter(p => p && p.connected) : [];
      const pad = disponibles.find(p => p.mapping === "standard") || disponibles[0] || null;
      this.opciones.mando(pad);
      if (!pad) {
        this.juego = vacio();
        this.anterior = [];
      } else {
        const valores = pad.buttons.map(b => b.value);
        if (valores.some((v, n) => v > 0.5 && !(this.anterior[n] > 0.5)) ||
            [...pad.axes].slice(0, 4).some(a => Math.abs(a) > 0.35)) this.usada("mando");
        if (this.captura && this.captura.tipo === "mando") {
          const i = valores.findIndex((v, n) => v > 0.5 && !(this.anterior[n] > 0.5));
          if (i >= 0) {
            this.opciones.reasignar(this.captura.accion, "mando", i);
            this.captura = null;
          }
        } else if (pad.mapping === "standard") {
          for (const [accion, i] of Object.entries(this.botones)) {
            if (mantenidos.includes(accion) || !(valores[i] > 0.5) || this.anterior[i] > 0.5) continue;
            if (accion === "parar") this.opciones.parar("Parada desde SHARE");
            else if (accion === "ajustes") this.opciones.ajustes();
            else if (this.opciones.activo()) this.opciones.emote(accion);
          }
          if (this.opciones.activo()) {
            const d = Number(this.config.zona_muerta ?? 0.15);
            const s = Number(this.config.sensibilidad ?? 1);
            const eje = i => curva(pad.axes[i], d) * s;
            this.juego = {
              mover: [-eje(1), eje(0)],
              mirar: [eje(2), -eje(3) * (this.config.invertir ? -1 : 1)],
              disparo: valores[this.botones.disparo] > 0.5,
              girar: (valores[this.botones.girar_derecha] > 0.5 ? 1 : 0) -
                (valores[this.botones.girar_izquierda] > 0.5 ? 1 : 0)
            };
          } else this.juego = vacio();
        } else this.juego = vacio();
        this.anterior = valores;
      }
      requestAnimationFrame(this.leerMando);
    }
    leer() {
      if (!this.opciones.activo()) return vacio();
      const si = nombre => this.pulsadas.has(this.teclas[nombre]) ? 1 : 0;
      const teclado = {
        mover: [si("adelante") - si("atras"), si("derecha") - si("izquierda")],
        mirar: [
          si("mirar_derecha") - si("mirar_izquierda"),
          (si("mirar_arriba") - si("mirar_abajo")) * (this.config.invertir ? -1 : 1)
        ],
        disparo: this.raton,
        girar: si("girar_derecha") - si("girar_izquierda")
      };
      return combinar(teclado, this.juego);
    }
  }
  global.ControlRM = { Entrada, curva, combinar, vacio, teclas, botones };
})(typeof window !== "undefined" ? window : globalThis);


