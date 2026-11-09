// Cifras de la memoria de la entrega 3 (tablas citadas en cada bloque). Si cambia la memoria, cambian aquí.

// Bloque 1 · Tablas 2, 3, 5 y 11
export const RECOGIDA = { videos: 10, segundos: 643.8, fotogramas: 19508, intervalo: 24, imagenes: 808 };
export const INTERVALOS = [
  { intervalo: 6, imagenes: 3248, duplicadas: 11.1 },
  { intervalo: 12, imagenes: 1622, duplicadas: 4.6 },
  { intervalo: 24, imagenes: 808, duplicadas: 1.4 },
  { intervalo: 48, imagenes: 400, duplicadas: 0.3 },
  { intervalo: 96, imagenes: 196, duplicadas: 0.0 },
];
export const ANOTACION = { robots: 1420, difficult: 375, negativas: 41, porImagen: 1.76, iouAnotadores: 0.81,
  imagenesCalibracion: 20, aspecto: 1.11 };
export const CRITERIOS = [
  ['Robot', 'chasis, ruedas, torreta y cañón; sin antenas'],
  ['Oclusión', 'se anota si se ve al menos un 30 %'],
  ['Difficult', '< 30 px de ancho, medio tapado o movido'],
  ['Ajenos', 'ni el cañón propio, ni reflejos, ni pantallas'],
  ['Negativas', 'imagen y XML vacío: también enseñan'],
];
export const DATASET = { originales: 808, depuradas: 796, cajasDepuradas: 1399, copias: 2388, total: 3184, cajasTotal: 5566 };
export const AUMENTO = [
  { grupo: 'Geometría', porque: 'robots lejanos y cámara inclinada', items: ['volteo horizontal', 'escala ×0,6–1,25', 'desplazamiento', 'giro ±6°'] },
  { grupo: 'Color', porque: 'otras luces', items: ['brillo y contraste ±20 %', 'gamma', 'tono suave', 'balance RGB'] },
  { grupo: 'Calidad', porque: 'vídeo movido o comprimido', items: ['desenfoque de movimiento', 'JPEG 35–75', 'ruido de sensor', 'menos resolución'] },
];

// Bloque 2 · Tablas 14, 16, 18, 22 y 23
export const LOTES = [
  { lote: '1', ap: 0.9332 }, { lote: '2', ap: 0.9358 }, { lote: '8', ap: 0.9326 },
  { lote: '16', ap: null }, { lote: '32', ap: null },
];
export const TASAS = [
  { tasa: '10⁻⁵', ap: 0.0261 }, { tasa: '10⁻³', ap: 0.9326 }, { tasa: '10⁻²', ap: 0.9353 }, { tasa: '10⁻¹', ap: null },
];
export const AJUSTE_V1 = [
  { nombre: 'Sin aumento · tasa 10⁻⁴', ap: 0.9228, epoca: 20 },
  { nombre: 'Con aumento · tasa 10⁻⁴', ap: 0.9416, epoca: 29 },
  { nombre: 'Con aumento · tasa 10⁻³', ap: 0.9433, epoca: 5 },
  { nombre: 'Con aumento · tasa 10⁻³ · imagen grande', ap: 0.9465, epoca: 2 },
];
export const ARQUITECTURAS = [
  { modelo: 'Faster R-CNN v2', corto: 'FRCNN v2', etapas: 2, ap: 0.9513, apDiff: 0.6422, ms: 99.5 },
  { modelo: 'RetinaNet v2', corto: 'RetinaNet v2', etapas: 1, ap: 0.9447, apDiff: 0.6213, ms: 67.3 },
  { modelo: 'Faster R-CNN v1', corto: 'FRCNN v1', etapas: 2, ap: 0.9426, apDiff: 0.6471, ms: 75.1 },
  { modelo: 'RetinaNet v1', corto: 'RetinaNet v1', etapas: 1, ap: 0.9396, apDiff: 0.5994, ms: 72.2 },
  { modelo: 'Faster R-CNN MobileNet', corto: 'MobileNet', etapas: 2, ap: 0.9281, apDiff: 0.6027, ms: 16.0 },
  { modelo: 'SSD300 VGG16', corto: 'SSD300', etapas: 1, ap: 0.9008, apDiff: 0.5199, ms: 12.5 },
  { modelo: 'SSDlite320', corto: 'SSDlite320', etapas: 1, ap: 0.6823, apDiff: 0.3233, ms: 4.2 },
];
export const TEST_FINAL = { modelo: 'Faster R-CNN v2', umbral: 0.95, ap50: 0.9523, ap75: 0.6005, ap5095: 0.5724,
  precision: 0.9447, exhaustividad: 0.9332, f1: 0.9389, tp: 1606, fp: 94, fn: 115, apNormales: 0.9658, apDifficult: 0.6921,
  fnDifficult: 74,
  imagenes: 718, robots: 1721, difficult: 270 };
export const TEST_MODELOS = [
  { modelo: 'Faster R-CNN v2', val: 0.9513, test: 0.9523 },
  { modelo: 'RetinaNet v2', val: 0.9447, test: 0.9457 },
  { modelo: 'Faster R-CNN v1', val: 0.9426, test: 0.9355 },
  { modelo: 'RetinaNet v1', val: 0.9396, test: 0.9362 },
  { modelo: 'Faster R-CNN MobileNet', val: 0.9281, test: 0.9240 },
  { modelo: 'SSD300 VGG16', val: 0.9008, test: 0.8797 },
  { modelo: 'SSDlite320', val: 0.6823, test: 0.6412 },
];

// Bloque 3 · Tablas B3.1 a B3.3 y mando
export const LATENCIA = { cpuLab: [2.2, 2.4], cpu32: 1.1, gpuV2: 0.094, gpuMobile: 0.032 };
// Recorrido en metros: origen en la salida, x hacia delante, y hacia la izquierda negativa (como la Figura B3.1)
export const CIRCUITO = {
  puntos: [[0, 0], [2.85, 0], [4.75, 0], [4.75, -1], [3.5, -1], [3.5, 0], [6, 0], [6, -0.7], [8, -0.7]],
  ataques: [3, 7],               // índice del tramo (desde el punto i al i+1) en el que se ataca en marcha
  tramos: [
    { tramo: 'P1', texto: '2,85 m · 0,5 m/s' }, { tramo: 'R1', texto: '1,9 m · 0,4 m/s' },
    { tramo: 'R1', texto: '1 m · 0,5 m/s' }, { tramo: 'R1', texto: '1,25 m · 0,1 m/s' },
    { tramo: 'R1', texto: '1 m · 0,5 m/s' }, { tramo: 'R2', texto: '2,5 m · 0,5 m/s' },
    { tramo: 'R2', texto: '0,7 m · 0,5 m/s' }, { tramo: 'R2', texto: '2 m · 0,1 m/s' },
  ],
  rivales: [
    { nombre: 'Rival 1', x: 2.85, y: 1.2 },
    { nombre: 'Camuflado', x: 2.85, y: -1.2, camuflado: true },
    { nombre: 'Rival 2', x: 4.6, y: -2.2, hastaX: 3.85 },
    { nombre: 'Rival 3 · en alto', x: 5.35, y: -0.7 },
  ],
};
export const PRESUPUESTO = [
  { que: 'Girar la torreta 90°', s: 3.0 },
  { que: 'Ver al rival (una imagen)', s: 2.0 },
  { que: '«Enemy spotted»', s: 1.4 },
  { que: 'Ráfaga de 20 disparos', s: 6.2 },
];
export const CAMUFLAJE = [
  { imagen: 'Detective', confianza: [98.8, 99.9], verde: 0.0 },
  { imagen: 'S1 con bandera', confianza: [99.8, 99.9], verde: 5.7 },
  { imagen: 'Orugas', confianza: [99.8, 99.9], verde: 11.0 },
  { imagen: 'Dibujo', confianza: [92.7, 97.9], verde: 7.6 },
  { imagen: 'Blanco', confianza: [95.4, 98.9], verde: 12.5 },
];
export const SOPORTES = [
  { soporte: 'Papel', tam: '⅓–½ del alto', conf: '0,96–0,99', dispara: true },
  { soporte: 'Papel', tam: '¼ del alto', conf: '0,87–0,92', dispara: false },
  { soporte: 'Tableta', tam: '⅓–½ del alto', conf: '0,29–0,63', dispara: false },
  { soporte: 'Tableta', tam: 'toda la imagen', conf: '0,55–0,95', dispara: null },
];
