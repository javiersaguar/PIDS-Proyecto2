// Genera la presentación en un solo fichero .html, sin carpetas ni servidor: se abre con doble clic.
// Uso: npm run html [-- ruta/de/salida.html]. Por defecto escribe docs/entregas/PIDS_grupo2_presentacion.html.
// Compila con todas las imágenes y fuentes incrustadas en base64 y después mete el JS y el CSS dentro del HTML.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const temporal = path.join(raiz, 'dist-unico');
const salida = path.resolve(process.argv[2] || path.join(raiz, '..', 'docs', 'entregas', 'PIDS_grupo2_presentacion.html'));

await build({
  root: raiz,
  logLevel: 'warn',
  build: { outDir: temporal, emptyOutDir: true, assetsInlineLimit: () => true, cssCodeSplit: false, chunkSizeWarningLimit: 1e6 },
});

const leer = (ruta) => fs.readFileSync(path.join(temporal, ruta), 'utf8');
let html = leer('index.html');
const usados = new Set();
// Se sustituye con una función para que los «$» del código no se tomen por referencias del patrón
html = html.replace(/<script type="module"[^>]*\ssrc="\.\/([^"]+)"[^>]*><\/script>/g, (_, ruta) => {
  usados.add(ruta);
  return `<script type="module">\n${leer(ruta).replace(/<\/script/gi, '<\\/script')}\n</script>`;
});
html = html.replace(/<link rel="stylesheet"[^>]*\shref="\.\/([^"]+)"[^>]*>/g, (_, ruta) => {
  usados.add(ruta);
  return `<style>\n${leer(ruta)}\n</style>`;
});

// Si algún fichero no se ha podido incrustar, el HTML no funcionaría solo: mejor fallar que entregarlo roto
const sueltos = fs.readdirSync(path.join(temporal, 'assets')).map((f) => `assets/${f}`).filter((f) => !usados.has(f));
if (sueltos.length || /(src|href)="\.\//.test(html)) {
  throw new Error(`Quedan ficheros sin incrustar: ${sueltos.join(', ') || 'referencias en el HTML'}`);
}

fs.mkdirSync(path.dirname(salida), { recursive: true });
fs.writeFileSync(salida, html);
fs.rmSync(temporal, { recursive: true, force: true });
console.log(`${salida} · ${(fs.statSync(salida).size / 1e6).toFixed(1)} MB`);
