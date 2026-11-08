/* Mezcla local mediante Web Audio, habilitada por un gesto del usuario. */
(function (global) {
  "use strict";
  class AudioRM {
    constructor(aviso) {
      this.aviso = aviso;
      this.contexto = null;
      this.buffers = new Map();
      this.pendientes = new Map();
      this.motor = null;
      this.emote = null;
      this.avisados = new Set();
      this.generacion = 0;
      this.config = {};
    }
    async activar() {
      if (!this.contexto) {
        this.contexto = new (window.AudioContext || window.webkitAudioContext)();
        this.general = this.contexto.createGain();
        this.general.connect(this.contexto.destination);
      }
      await this.contexto.resume();
      this.configurar(this.config);
      for (const n of ["scar", "motor"]) {
        this.cargar(n).catch(() => {});
      }
    }
    configurar(config) {
      this.config = config;
      if (this.general) this.general.gain.setTargetAtTime(Number(config.volumen ?? 0.7), this.contexto.currentTime, 0.04);
      if (config.audio === "robot") this.parar();
    }
    local() { return this.contexto && this.contexto.state === "running" && this.config.audio !== "robot"; }
    async cargar(nombre) {
      if (this.buffers.has(nombre)) return this.buffers.get(nombre);
      if (!this.pendientes.has(nombre)) {
        this.pendientes.set(nombre, (async () => {
          const respuesta = await fetch("/audio/" + nombre + ".ogg");
          if (!respuesta.ok) throw new Error(nombre);
          const buffer = await this.contexto.decodeAudioData(await respuesta.arrayBuffer());
          this.buffers.set(nombre, buffer);
          return buffer;
        })().catch(() => {
          if (!this.avisados.has(nombre)) { this.avisados.add(nombre); this.aviso("Falta el audio local de " + nombre); }
          return null;
        }));
      }
      return this.pendientes.get(nombre);
    }
    async tocar(nombre, desplazamiento = 0) {
      if (!this.local()) return;
      const generacion = this.generacion;
      const buffer = await this.cargar(nombre);
      if (!buffer || !this.local() || generacion !== this.generacion) return;
      const fuente = this.contexto.createBufferSource();
      fuente.buffer = buffer;
      fuente.connect(this.general);
      fuente.start(0, Math.min(Math.max(0, desplazamiento), Math.max(0, buffer.duration - 0.01)));
      return fuente;
    }
    async baile(nombre, progreso = 0, duracion = 0) {
      this.pararEmote();
      // Los emotes se reproducen en el robot, desde los WAV precargados.
    }
    pararEmote() {
      if (this.emote) { try { this.emote.stop(); } catch (_) {} }
      this.emote = null;
    }
    async mover(velocidad) {
      const nivel = Math.min(1, Math.hypot(...velocidad) / Math.max(.01, Number(this.config.velocidad || .5)));
      if (!this.local() || !this.config.motor) { this.frenarMotor(); return; }
      if (!this.motor && nivel > .01) {
        if (this.creandoMotor) return;
        this.creandoMotor = true;
        const generacion = this.generacion;
        const buffer = await this.cargar("motor");
        this.creandoMotor = false;
        if (!buffer || !this.local() || generacion !== this.generacion) return;
        const fuente = this.contexto.createBufferSource();
        const volumen = this.contexto.createGain();
        fuente.buffer = buffer;
        fuente.loop = true;
        fuente.connect(volumen);
        volumen.connect(this.general);
        volumen.gain.value = 0;
        fuente.start();
        this.motor = { fuente, volumen };
      }
      if (this.motor) {
        const t = this.contexto.currentTime;
        this.motor.volumen.gain.cancelScheduledValues(t);
        this.motor.volumen.gain.setValueAtTime(this.motor.volumen.gain.value, t);
        this.motor.volumen.gain.linearRampToValueAtTime(nivel > .01 ? Number(this.config.volumen_motor ?? .3) : 0, t + .3);
        this.motor.fuente.playbackRate.setTargetAtTime(.8 + .5 * nivel, t, .1);
      }
    }
    frenarMotor() {
      if (!this.motor) return;
      const anterior = this.motor;
      this.motor = null;
      const t = this.contexto.currentTime;
      anterior.volumen.gain.cancelScheduledValues(t);
      anterior.volumen.gain.setValueAtTime(anterior.volumen.gain.value, t);
      anterior.volumen.gain.linearRampToValueAtTime(0, t + .3);
      anterior.fuente.stop(t + .31);
    }
    parar() {
      this.generacion++;
      this.frenarMotor();
      this.pararEmote();
    }
  }
  global.AudioRM = AudioRM;
})(window);
