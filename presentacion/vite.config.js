import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(aqui, '..');

// Las imágenes y las fuentes se importan desde el propio repositorio (@repo/...), sin copias:
// fotogramas anotados, figuras de la memoria y las fuentes de la interfaz del mando.
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: { alias: { '@repo': repo } },
  server: { port: 5190, fs: { allow: [repo] } },
  preview: { port: 5191 },
});
