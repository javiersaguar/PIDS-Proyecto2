"use strict";
const assert = require("node:assert/strict");
require("../web/mando.js");
const { curva, combinar } = globalThis.ControlRM;
assert.equal(curva(.14, .15), 0);
assert.equal(curva(-.14, .15), -0);
assert.equal(curva(1, .15), 1);
assert.equal(curva(-1, .15), -1);
assert.ok(curva(.5, .15) < .5);
assert.deepEqual(combinar(
  { mover: [1, 0], mirar: [0, -.3], disparo: false },
  { mover: [.2, -.8], mirar: [.8, .1], disparo: true }
), { mover: [1, -.8], mirar: [.8, -.3], disparo: true, girar: 0 });
assert.deepEqual(combinar(
  { mover: [1, -1], mirar: [0, 0], disparo: false },
  { mover: [-.9, .9], mirar: [0, 0], disparo: false }
).mover, [1, -1]);
console.log("Controles: zona muerta, curva cuadrática y combinación por magnitud correctas.");
