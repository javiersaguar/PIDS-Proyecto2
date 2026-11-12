"use strict";
const assert = require("node:assert/strict");
globalThis.window = {};
require("../web/audio.js");
(async () => {
  const sonido = new window.AudioRM(() => {});
  sonido.local = () => true;
  sonido.tocar = () => { throw new Error("Un emote no debe sonar en el ordenador"); };
  await sonido.baile("risa", 0, 3.15);
  assert.equal(sonido.emote, null);
  console.log("Emotes enviados al robot, sin reproducción local.");
})().catch(error => { console.error(error); process.exitCode = 1; });
