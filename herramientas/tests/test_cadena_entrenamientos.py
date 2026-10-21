"""Pruebas de las funciones puras de herramientas/cadena_entrenamientos.py (no usan la GPU)."""
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'herramientas'))

import cadena_entrenamientos as c  # noqa: E402


def resumen(todos, difficult):
    return {'map': [{'grupo': 'todos', 'map_50': todos}, {'grupo': 'normales', 'map_50': 0.9},
                    {'grupo': 'difficult', 'map_50': difficult}]}


class NombresYEpocas(unittest.TestCase):
    def test_texto_del_lr(self):
        self.assertEqual(c.lr_txt(0.001), 'lr001')
        self.assertEqual(c.lr_txt(0.0005), 'lr0005')
        self.assertEqual(c.lr_txt(0.002), 'lr002')

    def test_nombre_distinto_por_modelo_y_lr(self):
        nombres = {c.nombre(m, lr) for m in c.MODELOS for lr in (c.LR_BASE, *c.LR_FASE2)}
        self.assertEqual(len(nombres), len(c.MODELOS) * 3)
        self.assertEqual(c.nombre('ssd_v2', 0.001), f'ssd_v2_aug_{c.PERFIL}_lr001')

    def test_sufijo_valido_para_el_notebook(self):
        for lr in (c.LR_BASE, *c.LR_FASE2):
            self.assertTrue(all(ch.isalnum() or ch in '-_' for ch in c.sufijo(lr)))

    def test_los_siete_modelos_del_script_original(self):
        self.assertEqual(sorted(c.MODELOS), sorted(['faster_rcnn_v1', 'faster_rcnn_v2', 'faster_rcnn_v3',
                                                    'retinanet_v1', 'retinanet_v2', 'ssd_v1', 'ssd_v2']))

    def test_epocas(self):
        self.assertEqual(c.epocas(0.001), c.EPOCAS)
        self.assertEqual(c.epocas(0.002), c.EPOCAS)
        self.assertEqual(c.epocas(0.0005), c.EPOCAS_LR_BAJO)

    def test_el_lote_efectivo_es_ocho(self):
        self.assertTrue(all(lote * acum == 8 for lote, acum in c.CANDIDATOS_LOTE))


class Eleccion(unittest.TestCase):
    def test_mayor_ap50(self):
        cand = {'a': resumen(0.90, 0.5), 'b': resumen(0.95, 0.4), 'c': resumen(0.93, 0.9)}
        self.assertEqual(c.elegir_mejores(cand, 2), ['b', 'c'])

    def test_empate_decide_difficult(self):
        cand = {'a': resumen(0.94, 0.55), 'b': resumen(0.94, 0.65)}
        self.assertEqual(c.elegir_mejores(cand, 1), ['b'])

    def test_menos_candidatos_que_pedidos(self):
        self.assertEqual(c.elegir_mejores({'a': resumen(0.9, 0.5)}, 3), ['a'])


class MejorUmbral(unittest.TestCase):
    def test_elige_la_fila_de_mayor_f1(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            exp = 'x_aug_robusto_v1_lr001'
            carpeta = Path(d) / 'resultados_test' / f'{exp}_val'
            carpeta.mkdir(parents=True)
            filas = ['umbral,precision,recall,recall_normales,recall_difficult,f1,tp,fp,fn',
                     '0.1,0.5,0.95,1,0.9,0.65,95,95,5',
                     '0.3,0.8,0.9,1,0.7,0.85,90,22,10',
                     '0.9,0.99,0.3,0.5,0.1,0.46,30,1,70']
            (carpeta / 'umbral_confianza.csv').write_text('\n'.join(filas) + '\n', encoding='utf-8')
            anterior, c.WEEK2 = c.WEEK2, Path(d)
            try:
                mejor = c.mejor_umbral(exp)
                self.assertEqual(mejor['umbral'], 0.3)
                self.assertEqual(mejor['fp'], 22.0)
                self.assertEqual(c.mejor_umbral('no_existe'), {})
            finally:
                c.WEEK2 = anterior


class ParcheDeData(unittest.TestCase):
    def nb(self, fuente):
        return {'cells': [{'cell_type': 'markdown', 'source': ["PERFIL_AUMENTO = 'base'"]},
                          {'cell_type': 'code', 'source': fuente}]}

    def test_cambia_solo_el_perfil(self):
        original = self.nb(["a = 1\n", "PERFIL_AUMENTO = 'base'     # comentario\n", "b = 2"])
        copia = c.parchear_perfil(copy.deepcopy(original), 'robusto_v1')
        self.assertEqual(copia['cells'][1]['source'][1], "PERFIL_AUMENTO = 'robusto_v1'     # comentario\n")
        self.assertEqual(copia['cells'][1]['source'][0], 'a = 1\n')
        self.assertEqual(copia['cells'][1]['source'][2], 'b = 2')
        self.assertEqual(copia['cells'][0], original['cells'][0])

    def test_falla_si_no_encuentra_el_perfil(self):
        with self.assertRaises(ValueError):
            c.parchear_perfil(self.nb(['x = 1']), 'robusto_v1')

    def test_falla_si_aparece_dos_veces(self):
        with self.assertRaises(ValueError):
            c.parchear_perfil(self.nb(["PERFIL_AUMENTO = 'base'\n", "PERFIL_AUMENTO = 'base'"]), 'robusto_v1')

    def test_con_el_notebook_real(self):
        nb = json.load(open(RAIZ / 'ENTREGA 1' / 'WEEK1' / 'data_aug.ipynb', encoding='utf-8'))
        copia = c.parchear_perfil(copy.deepcopy(nb), c.PERFIL)
        antes = ''.join(''.join(x['source']) for x in nb['cells'] if x['cell_type'] == 'code')
        despues = ''.join(''.join(x['source']) for x in copia['cells'] if x['cell_type'] == 'code')
        self.assertEqual(antes.replace("PERFIL_AUMENTO = 'base'", f"PERFIL_AUMENTO = '{c.PERFIL}'"), despues)


class NotebooksParametrizados(unittest.TestCase):
    """Los valores por defecto de train.ipynb y test.ipynb siguen siendo los de siempre."""

    def fuente(self, nombre):
        nb = json.load(open(RAIZ / 'ENTREGA 1' / 'WEEK2' / nombre, encoding='utf-8'))
        return '\n'.join(''.join(x['source']) for x in nb['cells'] if x['cell_type'] == 'code')

    def test_train_lee_pids_config_con_los_mismos_valores_por_defecto(self):
        s = self.fuente('train.ipynb')
        for esperado in ("_cfg.get('model_name', 'faster_rcnn_v1')", "_cfg.get('lr', 0.001)", "_cfg.get('num_epochs', 30)",
                         "_cfg.get('batch_size', 8)", "_cfg.get('perfil_aumento', 'base')",
                         "_cfg.get('acumulacion_gradiente', 1)", "_cfg.get('reanudar', False)"):
            self.assertIn(esperado, s)

    def test_test_lee_la_misma_configuracion(self):
        s = self.fuente('test.ipynb')
        for esperado in ("_cfg.get('conjunto', 'val')", "_cfg.get('perfil_aumento', 'base')",
                         "_cfg.get('sufijo_experimento', 'lr001')", "_cfg.get('max_imagenes')"):
            self.assertIn(esperado, s)

    def test_test_sigue_usando_val_por_defecto(self):
        self.assertIn("conjunto = _cfg.get('conjunto', 'val')", self.fuente('test.ipynb'))


if __name__ == '__main__':
    unittest.main()
