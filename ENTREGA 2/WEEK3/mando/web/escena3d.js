/* Escenas 3D del mando: el mando o el teclado con lo que se pulsa, y un robot pequeño con la
   torreta en su ángulo real. Solo dibuja: lee window.HUD, que rellena app.js, y no manda nada
   al robot. Three.js va copiado en vendor/ porque en el laboratorio no hay internet. */
import * as THREE from "/web/vendor/three.module.min.js";

const HUD = window.HUD;
const ACENTO = new THREE.Color(0x5ce483);
const ROJO = new THREE.Color(0xff4d4d);
const AMARILLO = new THREE.Color(0xffc800);
const APAGADO = new THREE.Color(0x2a4631);
const COLORES_PS = { 0: "#a1badb", 1: "#e09a9a", 2: "#d9a3c8", 3: "#9bd8ab" };
const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const rad = THREE.MathUtils.degToRad;

// Coordenadas de plano: x a la derecha, y hacia el lado lejano del jugador, h hacia arriba.
const en = (x, y, h = 0) => new THREE.Vector3(x, h, -y);

function textura(ancho, alto, dibujar) {
  const lienzo = document.createElement("canvas");
  lienzo.width = ancho;
  lienzo.height = alto;
  const tex = new THREE.CanvasTexture(lienzo);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  tex.redibujar = (...datos) => {
    const ctx = lienzo.getContext("2d");
    ctx.clearRect(0, 0, ancho, alto);
    dibujar(ctx, ancho, alto, ...datos);
    tex.needsUpdate = true;
  };
  return tex;
}

function material(color, extra) {
  return new THREE.MeshStandardMaterial(Object.assign({ color, roughness: .6, metalness: .08 }, extra));
}

/* Pieza que se hunde y se ilumina según cuánto se pulsa (0 a 1). */
class Pulsable {
  constructor(grupo, recorrido, materiales, brillo = 1.5) {
    this.grupo = grupo;
    this.y0 = grupo.position.y;
    this.recorrido = recorrido;
    this.materiales = materiales;
    this.brillo = brillo;
    this.valor = 0;
  }
  poner(objetivo) {
    this.valor += (objetivo - this.valor) * (quieto ? 1 : .5);
    this.grupo.position.y = this.y0 - this.valor * this.recorrido;
    for (const m of this.materiales) {
      if (m.emissive) m.emissiveIntensity = this.valor * this.brillo;
      else m.color.lerpColors(m.userData.base, m.userData.pulsado, this.valor);
    }
  }
}

function luces(escena) {
  escena.add(new THREE.HemisphereLight(0xe8ece6, 0x0b0d0a, 1.2));
  const principal = new THREE.DirectionalLight(0xffffff, 2.2);
  principal.position.set(5, 12, 8);
  escena.add(principal);
  const contra = new THREE.DirectionalLight(0x5ce483, .7);
  contra.position.set(-6, 5, -10);
  escena.add(contra);
}

function placaRedondeada(ancho, fondo, radio, grosor, mat) {
  const f = new THREE.Shape();
  const x = ancho / 2, y = fondo / 2;
  f.moveTo(-x + radio, -y);
  f.lineTo(x - radio, -y);
  f.quadraticCurveTo(x, -y, x, -y + radio);
  f.lineTo(x, y - radio);
  f.quadraticCurveTo(x, y, x - radio, y);
  f.lineTo(-x + radio, y);
  f.quadraticCurveTo(-x, y, -x, y - radio);
  f.lineTo(-x, -y + radio);
  f.quadraticCurveTo(-x, -y, -x + radio, -y);
  const g = new THREE.ExtrudeGeometry(f, { depth: grosor, bevelEnabled: true, bevelSize: .12, bevelThickness: .12, bevelSegments: 3, curveSegments: 10 });
  g.rotateX(-Math.PI / 2);
  g.translate(0, -grosor - .12, 0);        // cara de arriba en h = 0
  return new THREE.Mesh(g, mat);
}

// --- mando --------------------------------------------------------------------------------
function crearMando() {
  const grupo = new THREE.Group();
  const cuerpo = material(0x1d221e, { roughness: .5 });
  const oscuro = material(0x0e110f, { roughness: .75 });
  const piezas = {};                       // índice de botón → Pulsable

  const f = new THREE.Shape();
  f.moveTo(0, 3.4);
  f.lineTo(4.4, 3.4);
  f.bezierCurveTo(6.6, 3.5, 8.2, 2.6, 8.4, .4);
  f.bezierCurveTo(8.6, -2.4, 8.3, -5, 7.3, -6.3);
  f.bezierCurveTo(6.5, -7.2, 5.1, -6.9, 4.6, -5.6);
  f.bezierCurveTo(4.2, -4.4, 3.9, -2.4, 2.6, -2.2);
  f.lineTo(-2.6, -2.2);
  f.bezierCurveTo(-3.9, -2.4, -4.2, -4.4, -4.6, -5.6);
  f.bezierCurveTo(-5.1, -6.9, -6.5, -7.2, -7.3, -6.3);
  f.bezierCurveTo(-8.3, -5, -8.6, -2.4, -8.4, .4);
  f.bezierCurveTo(-8.2, 2.6, -6.6, 3.5, -4.4, 3.4);
  f.closePath();
  const g = new THREE.ExtrudeGeometry(f, { depth: 1.2, bevelEnabled: true, bevelSize: .4, bevelThickness: .45, bevelSegments: 5, curveSegments: 18 });
  g.rotateX(-Math.PI / 2);
  g.translate(0, -1.65, 0);                // cara de arriba en h = 0
  grupo.add(new THREE.Mesh(g, cuerpo));

  // Panel táctil y barra de luz
  const panel = new THREE.Mesh(new THREE.BoxGeometry(4.4, .16, 2.3), oscuro);
  panel.position.copy(en(0, 1.95, .05));
  grupo.add(panel);
  const barra = new THREE.MeshBasicMaterial({ color: APAGADO.clone() });
  const luz = new THREE.Mesh(new THREE.BoxGeometry(3.4, .08, .16), barra);
  luz.position.copy(en(0, 3.28, .04));
  grupo.add(luz);

  function boton(indice, x, y, forma, mat, recorrido = .18, altura = .2) {
    const g2 = new THREE.Group();
    g2.position.copy(en(x, y, altura));
    g2.add(new THREE.Mesh(forma, mat));
    grupo.add(g2);
    piezas[indice] = new Pulsable(g2, recorrido, [mat]);
    return g2;
  }

  // Botones de símbolo, con su figura dibujada encima
  const figuras = {
    3: (c, t) => { c.beginPath(); c.moveTo(t / 2, t * .2); c.lineTo(t * .82, t * .76); c.lineTo(t * .18, t * .76); c.closePath(); c.stroke(); },
    1: (c, t) => { c.beginPath(); c.arc(t / 2, t / 2, t * .3, 0, 7); c.stroke(); },
    0: (c, t) => { c.beginPath(); c.moveTo(t * .24, t * .24); c.lineTo(t * .76, t * .76); c.moveTo(t * .76, t * .24); c.lineTo(t * .24, t * .76); c.stroke(); },
    2: (c, t) => { c.strokeRect(t * .24, t * .24, t * .52, t * .52); }
  };
  const sitios = { 3: [5.6, 2.3], 1: [6.9, 1], 0: [5.6, -.3], 2: [4.3, 1] };
  for (const [indice, [x, y]] of Object.entries(sitios)) {
    const color = new THREE.Color(COLORES_PS[indice]);
    const mat = material(0x262c27, { emissive: color, emissiveIntensity: 0 });
    const g2 = boton(indice, x, y, new THREE.CylinderGeometry(.56, .6, .4, 28), mat);
    const tex = textura(128, 128, (c, w) => {
      c.strokeStyle = COLORES_PS[indice];
      c.lineWidth = 13;
      c.lineJoin = c.lineCap = "round";
      figuras[indice](c, w);
    });
    tex.redibujar();
    const cara = new THREE.Mesh(new THREE.CircleGeometry(.5, 28), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
    cara.rotation.x = -Math.PI / 2;
    cara.position.y = .21;
    g2.add(cara);
  }

  // Cruceta (12 arriba, 13 abajo, 14 izquierda, 15 derecha)
  const cruz = { 12: [0, .78], 13: [0, -.78], 14: [-.78, 0], 15: [.78, 0] };
  for (const [indice, [dx, dy]] of Object.entries(cruz)) {
    const mat = material(0x262c27, { emissive: ACENTO, emissiveIntensity: 0 });
    boton(indice, -5.6 + dx, 1 + dy, new THREE.BoxGeometry(dx ? .8 : .62, .34, dy ? .8 : .62), mat, .14, .17);
  }
  // SHARE, OPTIONS y PS
  for (const [indice, x] of [[8, -3.25], [9, 3.25]]) {
    const mat = material(0x2b312c, { emissive: indice === 8 ? ROJO : ACENTO, emissiveIntensity: 0 });
    boton(indice, x, 2.75, new THREE.BoxGeometry(.42, .26, .95), mat, .1, .13);
  }
  boton(16, 0, -.75, new THREE.CylinderGeometry(.45, .45, .24, 24), material(0x2b312c, { emissive: ACENTO, emissiveIntensity: 0 }), .1, .12);

  // Gatillos: L1/R1 pegados al borde y L2/R2 detrás, que bajan según cuánto se aprietan
  for (const [l1, l2, lado] of [[4, 6, -1], [5, 7, 1]]) {
    const m1 = material(0x2b312c, { emissive: ACENTO, emissiveIntensity: 0 });
    boton(l1, lado * 5.6, 4.15, new THREE.BoxGeometry(3.1, .7, .8), m1, .22, -.5);
    const m2 = material(0x333a34, { emissive: lado > 0 ? ROJO : ACENTO, emissiveIntensity: 0 });
    boton(l2, lado * 5.6, 5.25, new THREE.BoxGeometry(2.5, 1.1, 1.1), m2, .55, -.55);
  }

  // Joysticks: pivotan por debajo de la carcasa
  const sticks = [];
  for (const [x, ejeX, ejeY, pulsar] of [[-2.9, 0, 1, 10], [2.9, 2, 3, 11]]) {
    const pozo = new THREE.Mesh(new THREE.TorusGeometry(1.2, .16, 12, 40), oscuro);
    pozo.rotation.x = Math.PI / 2;
    pozo.position.copy(en(x, -.75, .04));
    grupo.add(pozo);
    const fondo = new THREE.Mesh(new THREE.CircleGeometry(1.2, 32), oscuro);
    fondo.rotation.x = -Math.PI / 2;
    fondo.position.copy(en(x, -.75, .02));
    grupo.add(fondo);
    const pivote = new THREE.Group();
    pivote.position.copy(en(x, -.75, -.7));
    const cana = new THREE.Mesh(new THREE.CylinderGeometry(.34, .42, 1.5, 16), oscuro);
    cana.position.y = .85;
    const anillo = material(0x2b312c, { emissive: ACENTO, emissiveIntensity: 0, roughness: .8 });
    const seta = new THREE.Mesh(new THREE.CylinderGeometry(.92, .98, .3, 32), anillo);
    seta.position.y = 1.7;
    const borde = new THREE.Mesh(new THREE.TorusGeometry(.8, .11, 10, 32), cuerpo);
    borde.rotation.x = Math.PI / 2;
    borde.position.y = 1.86;
    pivote.add(cana, seta, borde);
    grupo.add(pivote);
    sticks.push({ pivote, ejeX, ejeY, pulsar, anillo, x: 0, y: 0, hundido: 0, y0: pivote.position.y });
  }

  function actualizar(leds) {
    const p = HUD.pad;
    for (const [indice, pieza] of Object.entries(piezas)) pieza.poner(Math.min(1, Number(p.botones[indice]) || 0));
    for (const s of sticks) {
      const k = quieto ? 1 : .55;
      s.x += ((p.ejes[s.ejeX] || 0) - s.x) * k;
      s.y += ((p.ejes[s.ejeY] || 0) - s.y) * k;
      s.hundido += ((p.botones[s.pulsar] > .5 ? 1 : 0) - s.hundido) * k;
      s.pivote.rotation.z = -s.x * .5;
      s.pivote.rotation.x = s.y * .5;
      s.pivote.position.y = s.y0 - s.hundido * .16;
      s.anillo.emissiveIntensity = Math.min(1, Math.hypot(s.x, s.y)) * .4 + s.hundido * .7;
    }
    barra.color.copy(p.conectado ? leds.arriba : APAGADO);
  }
  return { grupo, actualizar };
}

// --- teclado y ratón ------------------------------------------------------------------------
function crearTeclado() {
  const grupo = new THREE.Group();
  const base = placaRedondeada(17.8, 9.4, .7, .5, material(0x161a17, { roughness: .7 }));
  base.position.copy(en(0, .55, 0));
  grupo.add(base);
  const cuerpoTecla = material(0x0d100e, { roughness: .8 });
  const BLANCO = new THREE.Color(0xffffff), PULSADA = new THREE.Color(0x8dffad);
  const teclas = [];

  // Colocadas como en el mando: mover a la izquierda, mirar en el centro y emotes en rombo
  const plano = [
    ["girar_izquierda", -6.3, 3.6], ["girar_derecha", -4.5, 3.6],
    ["adelante", -5.4, 1.1], ["izquierda", -7.1, -.6], ["atras", -5.4, -.6], ["derecha", -3.7, -.6],
    ["ajustes", 0, 3.6, 2.4],
    ["mirar_arriba", 0, 1.1], ["mirar_izquierda", -1.7, -.6], ["mirar_abajo", 0, -.6], ["mirar_derecha", 1.7, -.6],
    ["parar", 0, -2.75, 7, 1.3, "#ff8585"],
    ["waka", 5.6, 1.3, 1.5, 1.5, COLORES_PS[3]], ["superestrella", 7.3, -.4, 1.5, 1.5, COLORES_PS[1]],
    ["risa", 5.6, -2.1, 1.5, 1.5, COLORES_PS[0]], ["moonwalk", 3.9, -.4, 1.5, 1.5, COLORES_PS[2]]
  ];
  function caraTecla(c, w, h, texto, color) {
    c.fillStyle = "#222823";
    c.fillRect(0, 0, w, h);
    c.strokeStyle = color || "#4a5446";
    c.lineWidth = color ? 10 : 6;
    c.strokeRect(5, 5, w - 10, h - 10);
    c.fillStyle = color || "#e7efdf";
    const tam = texto.length <= 1 ? h * .6 : texto.length <= 3 ? h * .4 : h * .34;
    c.font = "600 " + tam + "px JetBrains, ui-monospace, monospace";
    c.textAlign = "center";
    c.textBaseline = "middle";
    c.fillText(texto, w / 2, h / 2 + tam * .06);
  }
  for (const [accion, x, y, ancho = 1.5, fondo = 1.5, color] of plano) {
    const g = new THREE.Group();
    g.position.copy(en(x, y, .3));
    g.add(new THREE.Mesh(new THREE.BoxGeometry(ancho, .6, fondo), cuerpoTecla));
    const tex = textura(Math.round(128 * ancho / fondo), 128, caraTecla);
    const cara = new THREE.MeshBasicMaterial({ map: tex });
    cara.userData = { base: BLANCO, pulsado: PULSADA };
    const plano2 = new THREE.Mesh(new THREE.PlaneGeometry(ancho - .14, fondo - .14), cara);
    plano2.rotation.x = -Math.PI / 2;
    plano2.position.y = .305;
    g.add(plano2);
    grupo.add(g);
    teclas.push({ accion, tex, color, pieza: new Pulsable(g, .24, [cara]) });
  }

  // Ratón: el botón izquierdo dispara
  const matRaton = material(0x3a423b, { roughness: .45 });
  const raton = new THREE.Group();
  raton.position.copy(en(5.6, 4.05, .3));
  const lomo = new THREE.Mesh(new THREE.CapsuleGeometry(.72, .55, 6, 20), matRaton);
  lomo.rotation.x = Math.PI / 2;
  lomo.scale.set(1, 1, .5);                // aplastado: tras el giro, z local es la altura
  lomo.position.z = .35;
  raton.add(lomo);
  const derecho = new THREE.Mesh(new THREE.BoxGeometry(.64, .42, .95), matRaton);
  derecho.position.set(.36, 0, -.62);
  raton.add(derecho);
  const rueda = new THREE.Mesh(new THREE.BoxGeometry(.12, .5, .4), material(0x0d100e));
  rueda.position.set(0, .04, -.6);
  raton.add(rueda);
  grupo.add(raton);
  const matClic = material(0x4a544b, { emissive: ROJO, emissiveIntensity: 0 });
  const clic = new THREE.Group();
  clic.position.copy(en(5.24, 4.67, .3));
  clic.add(new THREE.Mesh(new THREE.BoxGeometry(.64, .42, .95), matClic));
  grupo.add(clic);
  const piezaClic = new Pulsable(clic, .1, [matClic], 2.2);

  let version = -1;
  function actualizar() {
    if (version !== HUD.version) {
      version = HUD.version;
      const nombres = (HUD.etiquetas && HUD.etiquetas.teclado) || {};
      for (const t of teclas) t.tex.redibujar(nombres[t.accion] || "", t.color);
    }
    for (const t of teclas) t.pieza.poner(HUD.teclas[t.accion] ? 1 : 0);
    piezaClic.poner(HUD.raton ? 1 : 0);
  }
  // Las fuentes web pueden llegar después del primer dibujo
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { version = -1; });
  return { grupo, actualizar };
}

// --- robot con la torreta ---------------------------------------------------------------------
function crearRobot() {
  const grupo = new THREE.Group();
  const chapa = material(0x2a302b, { roughness: .5 });
  const negro = material(0x0c0e0c, { roughness: .85 });
  const ledAbajo = new THREE.MeshBasicMaterial({ color: APAGADO.clone() });
  const ledArriba = new THREE.MeshBasicMaterial({ color: APAGADO.clone() });

  // Suelo con referencia de rumbo: el frente del chasis es hacia arriba en pantalla
  const linea = new THREE.MeshBasicMaterial({ color: 0x5ce483, transparent: true, opacity: .22, side: THREE.DoubleSide, depthWrite: false });
  for (const r of [2.6, 3.9]) {
    const aro = new THREE.Mesh(new THREE.RingGeometry(r - .03, r + .03, 64), linea);
    aro.rotation.x = -Math.PI / 2;
    grupo.add(aro);
  }
  const frente = new THREE.Mesh(new THREE.ConeGeometry(.22, .5, 3), new THREE.MeshBasicMaterial({ color: 0x5ce483, transparent: true, opacity: .7 }));
  frente.rotation.x = -Math.PI / 2;
  frente.position.set(0, .02, -4.25);
  grupo.add(frente);

  const chasis = new THREE.Group();
  chasis.position.y = .55;
  const caja = new THREE.Mesh(new THREE.BoxGeometry(1.9, .5, 3), chapa);
  chasis.add(caja);
  // Blindajes con LED en los cuatro lados
  for (const [x, z, ancho, largo] of [[0, -1.56, 1.5, .14], [0, 1.56, 1.5, .14], [-1.02, 0, .14, 1.3], [1.02, 0, .14, 1.3]]) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(ancho, .34, largo), ledAbajo);
    b.position.set(x, .02, z);
    chasis.add(b);
  }
  const ruedas = [];
  for (const [x, z, signoY, signoZ] of [[-1.25, -1.05, 1, 1], [1.25, -1.05, -1, -1], [-1.25, 1.05, -1, 1], [1.25, 1.05, 1, -1]]) {
    const rueda = new THREE.Group();
    rueda.position.set(x, -.05, z);
    const llanta = new THREE.Mesh(new THREE.CylinderGeometry(.5, .5, .42, 20), negro);
    llanta.rotation.z = Math.PI / 2;
    rueda.add(llanta);
    for (let i = 0; i < 8; i++) {            // rodillos de la rueda mecanum, para que se vea girar
      const rodillo = new THREE.Mesh(new THREE.BoxGeometry(.44, .1, .2), chapa);
      const a = i * Math.PI / 4;
      rodillo.position.set(0, Math.sin(a) * .5, Math.cos(a) * .5);
      rodillo.rotation.x = -a;
      rueda.add(rodillo);
    }
    chasis.add(rueda);
    ruedas.push({ rueda, signoY, signoZ });
  }
  grupo.add(chasis);

  // Flecha de movimiento del chasis
  const flecha = new THREE.Group();
  const matFlecha = new THREE.MeshBasicMaterial({ color: 0xeceee6, transparent: true, opacity: .85 });
  const asta = new THREE.Mesh(new THREE.BoxGeometry(.14, .02, 1), matFlecha);
  asta.position.z = -.5;
  const punta = new THREE.Mesh(new THREE.ConeGeometry(.26, .5, 3), matFlecha);
  punta.rotation.x = -Math.PI / 2;
  punta.position.z = -1.2;
  flecha.add(asta, punta);
  flecha.position.y = .04;
  grupo.add(flecha);

  // Torreta: gira en yaw sobre el chasis y el cañón sube o baja en pitch
  const yaw = new THREE.Group();
  yaw.position.y = .8;
  const basa = new THREE.Mesh(new THREE.CylinderGeometry(.62, .7, .3, 24), negro);
  basa.position.y = .15;
  yaw.add(basa);
  const campo = new THREE.MeshBasicMaterial({ color: ACENTO.clone(), transparent: true, opacity: .2, side: THREE.DoubleSide, depthWrite: false });
  const sector = new THREE.Mesh(new THREE.CircleGeometry(3.9, 24, rad(55), rad(70)), campo);
  sector.rotation.x = -Math.PI / 2;
  sector.position.y = -.77;
  yaw.add(sector);
  const pitch = new THREE.Group();
  pitch.position.y = .72;
  const cabeza = new THREE.Mesh(new THREE.BoxGeometry(1.05, .62, 1.2), chapa);
  pitch.add(cabeza);
  const canon = new THREE.Mesh(new THREE.CylinderGeometry(.13, .13, 1.5, 12), negro);
  canon.rotation.x = Math.PI / 2;
  canon.position.set(0, -.02, -1.25);
  pitch.add(canon);
  const boca = new THREE.Mesh(new THREE.CylinderGeometry(.19, .19, .28, 12), ledArriba);
  boca.rotation.x = Math.PI / 2;
  boca.position.set(0, -.02, -2.05);
  pitch.add(boca);
  for (const x of [-.56, .56]) {
    const l = new THREE.Mesh(new THREE.BoxGeometry(.1, .36, .8), ledArriba);
    l.position.set(x, 0, 0);
    pitch.add(l);
  }
  yaw.add(pitch);
  grupo.add(yaw);

  let anguloYaw = 0, anguloPitch = 0, largo = 0;
  function actualizar(leds, dt) {
    const r = HUD.robot;
    // Giro más corto hasta el ángulo que da el robot (positivo: a la derecha)
    let falta = -rad(r.yaw) - anguloYaw;
    falta = Math.atan2(Math.sin(falta), Math.cos(falta));
    anguloYaw += falta * (quieto ? 1 : .22);
    anguloPitch += (rad(r.pitch) - anguloPitch) * (quieto ? 1 : .22);
    yaw.rotation.y = anguloYaw;
    pitch.rotation.x = anguloPitch;
    const [vx, vy] = r.velocidad;
    const rapidez = Math.hypot(vx, vy);
    largo += (Math.min(1, rapidez / .5) - largo) * .25;
    flecha.visible = largo > .04;
    flecha.rotation.y = -Math.atan2(vy, vx);
    flecha.scale.set(1, 1, .8 + largo * 1.6);
    flecha.position.set(0, .04, 0).add(new THREE.Vector3(Math.sin(-flecha.rotation.y), 0, -Math.cos(-flecha.rotation.y)).multiplyScalar(1.7));
    for (const { rueda, signoY, signoZ } of ruedas) {
      rueda.rotation.x -= (vx + signoY * vy + signoZ * (r.girar || 0) * .35) * dt * 14;
    }
    ledAbajo.color.copy(leds.abajo);
    ledArriba.color.copy(leds.arriba);
    campo.color.copy(leds.disparando ? ROJO : ACENTO);
    campo.opacity = leds.disparando ? .42 : .2;
  }
  return { grupo, actualizar };
}

// --- color de los LED según lo que hace el robot -------------------------------------------
const leds = { arriba: new THREE.Color(), abajo: new THREE.Color(), disparando: false };
function calcularLeds(ahora) {
  leds.disparando = ahora - HUD.disparoEn < 160;
  const e = HUD.emote;
  if (e && e.nombre === "waka") {
    // Bandera de España, al ritmo de la canción (127 tiempos por minuto), como en el robot
    const par = Math.floor(Math.max(0, ahora - e.inicio) / 1000 * 127 / 60) % 2 === 0;
    leds.arriba.copy(par ? ROJO : AMARILLO);
    leds.abajo.copy(par ? AMARILLO : ROJO);
  } else if (e) {
    leds.arriba.setHSL((ahora / 900) % 1, .9, .58);
    leds.abajo.copy(leds.arriba);
  } else if (leds.disparando) {
    leds.arriba.copy(ROJO);
    leds.abajo.copy(ROJO);
  } else {
    leds.arriba.copy(HUD.activo ? ACENTO : APAGADO);
    leds.abajo.copy(leds.arriba);
  }
}

// --- montaje -------------------------------------------------------------------------------
function vista(lienzo, fov, posicion, mira) {
  const renderer = new THREE.WebGLRenderer({ canvas: lienzo, alpha: true, antialias: true });
  renderer.setClearColor(0x000000, 0);
  const escena = new THREE.Scene();
  luces(escena);
  const camara = new THREE.PerspectiveCamera(fov, 1, .1, 100);
  camara.position.copy(posicion);
  camara.lookAt(mira);
  function ajustar() {
    const escala = Math.min(2, window.devicePixelRatio || 1);
    const w = Math.round(lienzo.clientWidth * escala), h = Math.round(lienzo.clientHeight * escala);
    if (!w || !h) return false;
    if (lienzo.width !== w || lienzo.height !== h) {
      renderer.setSize(w, h, false);
      camara.aspect = w / h;
      camara.updateProjectionMatrix();
    }
    return true;
  }
  return { renderer, escena, camara, ajustar };
}

function iniciar() {
  const controles = vista(document.getElementById("lienzo-controles"), 30, new THREE.Vector3(0, 23, 16.5), new THREE.Vector3(0, 0, .7));
  const mando = crearMando(), teclado = crearTeclado();
  controles.escena.add(mando.grupo, teclado.grupo);
  const robot = vista(document.getElementById("lienzo-robot"), 36, new THREE.Vector3(0, 11.5, 9), new THREE.Vector3(0, .4, -.5));
  const modelo = crearRobot();
  robot.escena.add(modelo.grupo);

  let mezcla = HUD.vista === "mando" ? 1 : 0, anterior = performance.now();
  function colocar(grupo, visible, t, tam = 1) {
    grupo.visible = visible > .02;
    grupo.scale.setScalar(tam * (.72 + .28 * visible));
    grupo.position.y = (1 - visible) * -3.5;
    grupo.rotation.x = (1 - visible) * .7;
    grupo.rotation.y = quieto ? 0 : Math.sin(t / 2600) * .05;
  }
  function fotograma(ahora) {
    requestAnimationFrame(fotograma);
    if (document.hidden) return;
    const dt = Math.min(.1, (ahora - anterior) / 1000);
    anterior = ahora;
    calcularLeds(ahora);
    mezcla += ((HUD.vista === "mando" ? 1 : 0) - mezcla) * (quieto ? 1 : .28);
    if (Math.abs((HUD.vista === "mando" ? 1 : 0) - mezcla) < .004) mezcla = HUD.vista === "mando" ? 1 : 0;
    // Primero se va uno y después entra el otro, para que no se monten
    colocar(mando.grupo, Math.max(0, mezcla * 2 - 1), ahora);
    colocar(teclado.grupo, Math.max(0, 1 - mezcla * 2), ahora, 1.14);
    mando.actualizar(leds);
    teclado.actualizar();
    modelo.actualizar(leds, dt);
    if (controles.ajustar()) controles.renderer.render(controles.escena, controles.camara);
    if (robot.ajustar()) robot.renderer.render(robot.escena, robot.camara);
  }
  requestAnimationFrame(fotograma);
}

try {
  iniciar();
} catch (error) {
  // Sin WebGL la página sigue funcionando; solo faltan los dibujos
  HUD.sin3d = true;
  document.body.classList.add("sin-3d");
  console.warn("Escena 3D no disponible:", error);
}
