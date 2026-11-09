// Orden de la presentación. Cada diapositiva: fase (índice de FASES), título para el índice,
// componente, pasos (fragmentos que se descubren con →) y notas para quien presenta (tecla N).
import { Equipo, Portada, Reto } from './inicio.jsx';
import { Anotacion, Aumento, Decisiones, Eda, Recogida, Seccion1 } from './fase1.jsx';
import { Ajuste, Arquitecturas, Cualitativo, Etapas, Hiperparametros, Seccion2, Sistema, Test } from './fase2.jsx';
import { Camuflaje, Circuito, Estado, Integracion, Mando, Marcha, Punteria, Seccion3 } from './fase3.jsx';
import { Conclusiones, Gracias } from './cierre.jsx';

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
  { id: 'reto', fase: 0, titulo: 'El reto y las tres fases', Componente: Reto,
    notas: 'Objetivo del proyecto y las tres fases: datos propios, modelo y robot. Cada fase alimenta a la siguiente.' },
  { id: 'equipo', fase: 0, titulo: 'Cómo nos organizamos', Componente: Equipo,
    notas: 'Un lote de dos vídeos por persona, revisión cruzada y calibración común. Ramas personales y pull requests revisadas por otro integrante.' },

  { id: 'seccion-1', fase: 1, tipo: 'seccion', titulo: 'Fase 1 · Datos', Componente: Seccion1,
    notas: 'Fase 1: todo lo que hicimos antes de entrenar.' },
  { id: 'recogida', fase: 1, titulo: 'De 19 508 fotogramas a 808 imágenes', Componente: Recogida,
    notas: 'Diez vídeos propios en cuatro escenarios. El intervalo de 24 se eligió midiendo la redundancia (Tabla 3): con 12 duplicaríamos el trabajo para añadir poca información.' },
  { id: 'anotacion', fase: 1, titulo: 'Criterios de anotación', Componente: Anotacion,
    notas: 'Qué es un robot y qué es difficult. Calibración con 20 imágenes difíciles anotadas por los cinco: IoU medio 0,81, con más discrepancia en el borde superior (torreta y antenas).' },
  { id: 'eda', fase: 1, titulo: 'Análisis exploratorio', Componente: Eda,
    notas: 'Cada vídeo es distinto en número de robots y difficult. Validación y test tienen más robots por imagen y más pequeños que nuestros vídeos.' },
  { id: 'decisiones', fase: 1, titulo: 'Del EDA a las decisiones', Componente: Decisiones, pasos: 3,
    notas: 'Pulsar → para descubrir cada fila. Lo importante: cada decisión del entrenamiento sale del EDA y se comprobó después en el Bloque 2.' },
  { id: 'aumento', fase: 1, titulo: 'Aumento y depuración', Componente: Aumento,
    notas: 'Transformaciones geométricas, de color y de calidad, cada una justificada por el EDA. Depuración: 69 imágenes revisadas a ojo, 12 fuera. 796 originales × 4 = 3184 imágenes.' },

  { id: 'seccion-2', fase: 2, tipo: 'seccion', titulo: 'Fase 2 · Modelo', Componente: Seccion2,
    notas: 'Fase 2: entrenamiento, comparación de arquitecturas y evaluación final.' },
  { id: 'sistema', fase: 2, titulo: 'El sistema de entrenamiento', Componente: Sistema,
    notas: 'Esquema de bloques (comentario C2.1 de la revisión). Azul: cada lote; verde: cada época; naranja: una sola vez. El test solo mide, no decide.' },
  { id: 'etapas', fase: 2, titulo: 'Una y dos etapas', Componente: Etapas,
    notas: 'Dos etapas: propuestas y después clasificación de cada región. Una etapa: anclas por toda la imagen y predicción directa, con pérdida focal en RetinaNet.' },
  { id: 'hiperparametros', fase: 2, titulo: 'Hiperparámetros', Componente: Hiperparametros,
    notas: 'Lote 8: el mayor que cabe y estable. Tasa 10⁻³: 10⁻⁵ apenas aprende y 10⁻¹ diverge. SGD con momentum 0,9 y weight decay 5·10⁻⁴, del artículo de Faster R-CNN y del tutorial de torchvision.' },
  { id: 'ajuste', fase: 2, titulo: 'Primeros experimentos y sobreajuste', Componente: Ajuste,
    notas: 'El aumento sube 1,9 pp (puntos porcentuales). La imagen grande no compensa: más falsos positivos, peores cajas y un 62 % más lenta. La validación toca su mínimo en la época 4 y luego sube mientras el entrenamiento baja: guardamos el mejor checkpoint de validación.' },
  { id: 'arquitecturas', fase: 2, titulo: 'Siete arquitecturas', Componente: Arquitecturas,
    notas: 'Precisión frente a tiempo. La línea discontinua une los modelos que ningún otro supera en las dos cosas. Faster R-CNN v2 es el final; MobileNet, la alternativa rápida.' },
  { id: 'test', fase: 2, titulo: 'Evaluación final en test', Componente: Test,
    notas: 'Test una sola vez, con el umbral fijado en validación. 0,952 de AP@0,5. La curva PR responde al comentario C2.7. Los difficult son el punto débil.' },
  { id: 'cualitativo', fase: 2, titulo: 'Análisis cualitativo', Componente: Cualitativo,
    notas: 'Algunos falsos positivos son robots sin etiquetar en validación. Los fallos reales: difficult, lejanos y secuencias concretas.' },

  { id: 'seccion-3', fase: 3, tipo: 'seccion', titulo: 'Fase 3 · Robot', Componente: Seccion3,
    notas: 'Fase 3: el detector en el RoboMaster EP.' },
  { id: 'integracion', fase: 3, titulo: 'Integración en el robot', Componente: Integracion,
    notas: 'Portátil y robot por wifi. Python 3.8 obliga a usar la CPU: 2,2–2,4 s por imagen. Por eso el robot para a mirar. Seguridad: topes, órdenes que caducan y final seguro.' },
  { id: 'circuito', fase: 3, titulo: 'El circuito', Componente: Circuito,
    notas: 'Recorrido por tramos. Solo P1 está medido en el laboratorio. Primer problema: la orden por distancia del SDK no respetaba la velocidad.' },
  { id: 'punteria', fase: 3, titulo: 'Puntería y la cola de vídeo', Componente: Punteria, pasos: 1,
    notas: 'Primero la causa: la cola de 64 imágenes del SDK. Pulsar → para el arreglo: solo la última imagen, tomada después del último giro.' },
  { id: 'marcha', fase: 3, titulo: 'Ataque en marcha', Componente: Marcha,
    notas: 'Presupuesto de tiempo del retroceso de 1,25 m. El chasis va por su cuenta y la torreta sigue al rival con la velocidad prevista.' },
  { id: 'camuflaje', fase: 3, titulo: 'Robot camuflado y aliados', Componente: Camuflaje,
    notas: 'El detector ve robots en todo lo que parece un robot. Para no disparar a un aliado hace falta una marca: más de un 2 % de verde. Prueba con papel y tableta delante de una webcam.' },
  { id: 'mando', fase: 3, titulo: 'Control manual', Componente: Mando,
    notas: 'Interfaz del mando en el navegador. El detector va en un proceso aparte con la GPU: unas 10 imágenes por segundo con Faster R-CNN v2.' },
  { id: 'estado', fase: 3, titulo: 'Estado del Bloque 3', Componente: Estado,
    notas: 'Actualizar con los resultados del laboratorio antes de presentar.' },

  { id: 'conclusiones', fase: 4, titulo: 'Conclusiones', Componente: Conclusiones,
    notas: 'Una lección por fase y el trabajo futuro.' },
  { id: 'gracias', fase: 4, tipo: 'portada', titulo: 'Gracias', Componente: Gracias, notas: 'Turno de preguntas.' },
];
