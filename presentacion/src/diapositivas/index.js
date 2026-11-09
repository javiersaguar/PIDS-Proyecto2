// Orden de la presentación. Cada diapositiva: fase (índice de FASES), título para el índice,
// componente, pasos (fragmentos que se descubren con →) y notas para quien presenta (tecla N).
import { Portada, Reto } from './inicio.jsx';
import { Anotacion, Aumento, Eda, Recogida, Seccion1 } from './fase1.jsx';
import { Ajuste, Arquitecturas, Cualitativo, Etapas, Hiperparametros, Seccion2, Sistema, Test } from './fase2.jsx';
import { Circuito, Integracion, Mando, Marcha, Seccion3 } from './fase3.jsx';
import { Gracias } from './cierre.jsx';

export const FASES = [
  { nombre: 'Introducción' },
  { nombre: 'Fase 1 · Datos' },
  { nombre: 'Fase 2 · Modelo' },
  { nombre: 'Fase 3 · Robot' },
  { nombre: 'Cierre' },
];

export const DIAPOSITIVAS = [
  { id: 'portada', fase: 0, tipo: 'portada', titulo: 'Portada', Componente: Portada,
    notas: 'Presentación del grupo. La imagen es un fotograma de nuestro vídeo V03 con sus robots anotados.' },
  { id: 'reto', fase: 0, titulo: 'El caso y cómo lo resolvimos', Componente: Reto,
    notas: 'Objetivo del proyecto y las tres fases: datos propios, modelo y robot. Cada fase alimenta a la siguiente. La cifra del robot es la latencia: el SDK obliga a Python 3.8 y el detector va en CPU, a 2,2–2,4 s por imagen; eso condiciona todo el Bloque 3.' },
  { id: 'seccion-1', fase: 1, tipo: 'seccion', titulo: 'Fase 1 · Datos', Componente: Seccion1,
    notas: 'Fase 1: todo lo que hicimos antes de entrenar.' },
  { id: 'recogida', fase: 1, titulo: 'Las imágenes con las que entrenamos', Componente: Recogida,
    notas: 'Diez vídeos propios en cuatro escenarios. El intervalo de 24 se eligió midiendo la redundancia (Tabla 3): con 12 duplicaríamos el trabajo para añadir poca información.' },
  { id: 'anotacion', fase: 1, titulo: 'Qué consideramos un robot', Componente: Anotacion,
    notas: 'Qué es un robot y qué es difficult. Calibración con 20 imágenes difíciles anotadas por los cinco: IoU medio 0,81, con más discrepancia en el borde superior (torreta y antenas).' },
  { id: 'eda', fase: 1, titulo: 'Nuestros vídeos y los de la asignatura no se parecen', Componente: Eda,
    notas: 'Cada vídeo es distinto en número de robots y difficult. Validación y test tienen más robots por imagen y más pequeños que nuestros vídeos.' },
  { id: 'aumento', fase: 1, titulo: 'Más imágenes sin grabar escenas nuevas', Componente: Aumento,
    notas: 'Transformaciones geométricas, de color y de calidad, cada una justificada por el EDA. Depuración: 69 imágenes revisadas a ojo, 12 fuera. 796 originales × 4 = 3184 imágenes.' },

  { id: 'seccion-2', fase: 2, tipo: 'seccion', titulo: 'Fase 2 · Modelo', Componente: Seccion2,
    notas: 'Fase 2: entrenamiento, comparación de arquitecturas y evaluación final.' },
  { id: 'sistema', fase: 2, titulo: 'Cómo entrenamos cada detector y cómo lo medimos', Componente: Sistema,
    notas: 'Esquema de bloques (comentario C2.1 de la revisión). Azul: cada lote; verde: cada época; naranja: una sola vez. El test solo mide, no decide.' },
  { id: 'etapas', fase: 2, titulo: 'Dos formas de buscar el robot en la imagen', Componente: Etapas,
    notas: 'Dos etapas: propuestas y después clasificación de cada región. Una etapa: anclas por toda la imagen y predicción directa, con pérdida focal en RetinaNet.' },
  { id: 'hiperparametros', fase: 2, titulo: 'Cómo elegimos el lote, la tasa y el optimizador', Componente: Hiperparametros,
    notas: 'Pruebas de tres épocas con Faster R-CNN v1. Lote: con 1, 2 y 8 el AP@0,5 acaba a menos de 0,4 puntos porcentuales (pp); 16 y 32 no caben en los 12 GB. Elegimos 8, el mayor que cabe: gradientes estables y unos 400 pasos por época. Tasa: con 10⁻⁵ el AP no llega a 0,03 en tres épocas y con 10⁻¹ la pérdida acaba en NaN; entre 10⁻⁴ y 10⁻² cambia la velocidad, no el resultado. SGD: el momentum 0,9 sigue la media de unos 10 lotes; el weight decay 5·10⁻⁴ penaliza los pesos grandes; la tasa se multiplica por 0,1 tras 5 épocas sin mejorar la validación. Son los valores del artículo de Faster R-CNN y del tutorial de torchvision. Una estrategia mejor: prueba de rango de la tasa, búsqueda logarítmica y paciencia ajustada a cuándo se estanca la validación.' },
  { id: 'ajuste', fase: 2, titulo: 'Qué mejoró al primer modelo, y cuándo dejó de mejorar', Componente: Ajuste,
    notas: 'El aumento sube 1,9 pp (puntos porcentuales). La imagen grande no compensa: más falsos positivos, peores cajas y un 62 % más lenta. La validación toca su mínimo en la época 4 y luego sube mientras el entrenamiento baja: guardamos el mejor checkpoint de validación.' },
  { id: 'arquitecturas', fase: 2, titulo: 'Los siete detectores, en precisión y en tiempo', Componente: Arquitecturas,
    notas: 'Precisión frente a tiempo. La línea discontinua une los modelos que ningún otro supera en las dos cosas. Faster R-CNN v2 es el final; MobileNet, la alternativa rápida.' },
  { id: 'test', fase: 2, titulo: 'El resultado en imágenes que el modelo no había visto', Componente: Test,
    notas: 'Test una sola vez, con el umbral fijado en validación. 0,952 de AP@0,5. La curva PR responde al comentario C2.7. Los difficult son el punto débil.' },
  { id: 'cualitativo', fase: 2, titulo: 'Dónde acierta el detector y dónde se equivoca', Componente: Cualitativo,
    notas: 'Algunos falsos positivos son robots sin etiquetar en validación. Los fallos reales: difficult, lejanos y secuencias concretas.' },

  { id: 'seccion-3', fase: 3, tipo: 'seccion', titulo: 'Fase 3 · Robot', Componente: Seccion3,
    notas: 'Fase 3: el detector en el RoboMaster EP.' },
  { id: 'integracion', fase: 3, titulo: 'Cómo conectamos el detector al robot', Componente: Integracion,
    notas: 'Portátil y robot por wifi: el vídeo de 1280 × 720 llega al portátil y las órdenes van al robot. Python 3.8 obliga a usar la CPU: 2,2–2,4 s por imagen, frente a los 0,1 s que harían falta para ver y moverse a la vez. Por eso el robot se para a mirar y cada tramo reparte el tiempo entre girar, ver y disparar. Umbral de confianza 0,95 y configuración separada del código. Seguridad: toda orden se recorta a 0,5 m/s y 30 °/s; si el programa se bloquea, el chasis se para a los 0,5 s; ante un error, una interrupción o el final, para, centra la torreta, apaga los LED y guarda las evidencias.' },
  { id: 'circuito', fase: 3, titulo: 'El recorrido que tiene que hacer el robot', Componente: Circuito,
    notas: 'Recorrido por tramos. Solo P1 está medido en el laboratorio. Primer problema: la orden por distancia del SDK no respetaba la velocidad.' },
  { id: 'marcha', fase: 3, titulo: 'Disparar sin detener el robot', Componente: Marcha,
    notas: 'Presupuesto de tiempo del retroceso de 1,25 m a 0,1 m/s: girar la torreta, ver al rival, avisar y la ráfaga. El chasis no espera a la inferencia. Imagen nítida: con el robot en marcha algunas salen movidas; de las de los últimos 0,2 s se analiza la más nítida (varianza del laplaciano). Velocidad prevista: con el plano y las velocidades, el rival 2 se queda atrás unos 2,4 °/s; la torreta gira a esa velocidad y corrige con cada imagen. Rival en alto: a 1 m queda a unos 17° y a 2 m a 9°; la torreta lo busca inclinada 10° y corrige con la caja. Ráfaga: 20 disparos, uno cada 0,3 s, sincronizados con el sonido; el enunciado pide 12 impactos y los 8 de más cubren los que no registre.' },
  { id: 'mando', fase: 3, titulo: 'Mover el robot a mano desde el navegador', Componente: Mando,
    notas: 'Interfaz del mando en el navegador. El detector va en un proceso aparte con la GPU: unas 10 imágenes por segundo con Faster R-CNN v2 y unas 31 con MobileNet. El joystick mueve el robot hacia donde mira la cámara. Si dejan de llegar órdenes durante 0,3 s, el robot se para; mismos topes que la demo. Disparo automático opcional: el centro de la imagen dentro de una caja de confianza ≥ 0,95, de menos de 0,5 s y con la torreta quieta. 31 pruebas automáticas y probado con el robot simulado.' },

  { id: 'gracias', fase: 4, tipo: 'portada', titulo: 'Gracias', Componente: Gracias, notas: 'Turno de preguntas.' },
];
