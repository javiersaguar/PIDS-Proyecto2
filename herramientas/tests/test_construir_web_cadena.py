"""Pruebas de las figuras de la cadena de entrenamientos (no necesitan GPU ni red)."""
import json
import sys
import unittest
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import construir_web_cadena as web  # noqa: E402


class FigurasCadena(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.figuras = web.construir()

    def test_hay_las_diez_figuras(self):
        self.assertEqual(set(self.figuras), {'arquitecturas', 'tasa', 'aprendizaje', 'coste', 'latencia', 'validacion_test',
                                             'errores', 'umbral', 'secuencias', 'mapa'})

    def test_cada_combinacion_de_selectores_tiene_su_variante(self):
        for nombre, fig in self.figuras.items():
            opciones = [range(len(c['opciones'])) for c in fig['controles']] or [range(1)]
            claves = {'|'.join(map(str, c)) for c in product(*opciones)}
            self.assertEqual(claves, set(fig['variantes']), nombre)

    def test_es_json_valido_y_sin_nan(self):
        json.dumps(self.figuras, allow_nan=False)

    def test_cada_variante_tiene_datos(self):
        for nombre, fig in self.figuras.items():
            for clave, variante in fig['variantes'].items():
                self.assertTrue(variante['data'], f'{nombre} {clave}')
                for traza in variante['data']:
                    for eje in ('x', 'y', 'z'):
                        if eje in traza:
                            self.assertTrue(len(traza[eje]) > 0, f'{nombre} {clave}')

    def test_el_entrenamiento_largo_aparece_en_la_figura_de_aprendizaje(self):
        opciones = self.figuras['aprendizaje']['controles'][0]['opciones']
        self.assertEqual(len(opciones), 13 + len(web.cargar_largo()))
        if web.cargar_largo():
            self.assertIn('SSD300 VGG16 · lr 0,001 · 40 épocas', opciones)

    def test_valor_de_test_del_modelo_final(self):
        variante = self.figuras['validacion_test']['variantes']['0']
        test = next(t for t in variante['data'] if t['name'] == 'Test')
        val = next(t for t in variante['data'] if t['name'] == 'Validación')
        self.assertEqual(test['x'][0], 'Faster R-CNN v2')
        self.assertAlmostEqual(test['y'][0], 0.9523, places=4)
        self.assertAlmostEqual(val['y'][0], 0.9513, places=4)

    def test_minutos_totales_de_la_cadena(self):
        val, _ = web.cargar()
        self.assertEqual(len(val), 13)
        self.assertAlmostEqual(sum(f['minutos_train'] for f in val), 1306.0, places=0)

    def test_f1_de_test_con_el_umbral_fijado(self):
        _, test = web.cargar()
        final = next(f for f in test if f['modelo'] == 'faster_rcnn_v2' and f['lr'] == 0.001)
        self.assertAlmostEqual(final['f1_umbral'], 0.9389, places=4)
        self.assertEqual(final['umbral_fijado'], 0.95)

    def test_los_valores_fuera_de_escala_solo_ocultan_lo_muy_bajo(self):
        rango, fuera = web._rango_ajustado([0.95, 0.94, 0.93, 0.68])
        self.assertEqual(fuera, [0.68])
        self.assertGreater(rango[0], 0.9)

    def test_formato_con_coma(self):
        self.assertEqual(web.coma(0.9513), '0,9513')
        self.assertEqual(web.lr_txt(0.0005), '0,0005')
        self.assertEqual(web.lr_txt(0.001), '0,001')
        self.assertEqual(web.id_exp('faster_rcnn_v2', 0.0005), 'faster_rcnn_v2_aug_robusto_v1_lr0005')


if __name__ == '__main__':
    unittest.main()
