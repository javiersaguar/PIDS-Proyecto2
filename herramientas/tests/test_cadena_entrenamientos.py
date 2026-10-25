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


class Opciones(unittest.TestCase):
    def test_modelos_validos_en_su_orden(self):
        self.assertEqual(c.validar_modelos('retinanet_v2, faster_rcnn_v2'), ['retinanet_v2', 'faster_rcnn_v2'])

    def test_rechaza_modelos_desconocidos_o_repetidos_o_vacios(self):
        for malo in ('inventado', 'ssd_v1,ssd_v1', '', 'ssd_v1,otro'):
            with self.assertRaises(ValueError):
                c.validar_modelos(malo)

    def test_simular_no_ejecuta_nada(self):
        import contextlib
        import io
        llamadas = []
        original = c.ejecutar
        c.ejecutar = lambda *a, **k: llamadas.append(a) or 0
        try:
            with contextlib.redirect_stdout(io.StringIO()) as salida:
                c.main(['cadena', '--simular', '--modelos', 'ssd_v2', '--sin-fase2'])
        finally:
            c.ejecutar = original
        self.assertEqual(llamadas, [])
        self.assertIn('ssd_v2_aug_robusto_v1_lr001', salida.getvalue())
        self.assertIn('--sin-fase2', salida.getvalue())


class EvaluacionEnTest(unittest.TestCase):
    """La acción `test` evalúa una sola vez, con el umbral de validación, y deja registro."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.guardado = (c.RAIZ, c.WEEK2, c.CADENA, c.ejecutar, c.comprobar_gpu, c.evitar_suspension)
        c.RAIZ, c.WEEK2, c.CADENA = base, base / 'WEEK2', base / 'WEEK2' / 'cadena'
        c.CADENA.mkdir(parents=True)
        self.exp = c.nombre('ssd_v1', c.LR_BASE)
        estado = {'experimentos': {self.exp: {'modelo': 'ssd_v1', 'lr': c.LR_BASE, 'fase': 1, 'batch_size': 8, 'acumulacion_gradiente': 1}}}
        c.escribir_json(c.CADENA / 'estado.json', estado)
        val = c.WEEK2 / 'resultados_test' / f'{self.exp}_val'
        val.mkdir(parents=True)
        c.escribir_json(val / 'resumen.json', resumen(0.90, 0.52))
        filas = ['umbral,precision,recall,recall_normales,recall_difficult,f1,tp,fp,fn',
                 '0.1,0.5,0.95,1,0.9,0.65,95,95,5', '0.25,0.9,0.9,1,0.7,0.89,90,10,10', '0.9,0.99,0.3,0.5,0.1,0.46,30,1,70']
        (val / 'umbral_confianza.csv').write_text('\n'.join(filas) + '\n', encoding='utf-8')
        self.llamadas = []

        def falso_ejecutar(notebook, salida, cfg, log):
            self.llamadas.append(cfg)
            carpeta = c.WEEK2 / 'resultados_test' / f'{self.exp}_test'
            carpeta.mkdir(parents=True, exist_ok=True)
            c.escribir_json(carpeta / 'resumen.json', resumen(0.91, 0.55))
            return 0

        c.ejecutar, c.comprobar_gpu, c.evitar_suspension = falso_ejecutar, lambda: None, lambda: None

    def tearDown(self):
        c.RAIZ, c.WEEK2, c.CADENA, c.ejecutar, c.comprobar_gpu, c.evitar_suspension = self.guardado
        self.tmp.cleanup()

    def lanzar(self, **kw):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            c.evaluar_test(self.exp, **kw)
        return salida.getvalue()

    def test_sin_confirmar_solo_muestra_el_plan(self):
        salida = self.lanzar()
        self.assertEqual(self.llamadas, [])
        self.assertIn('Solo es el plan', salida)
        self.assertIn('umbral 0.25', salida)

    def test_confirmado_usa_el_umbral_de_validacion_y_el_conjunto_test(self):
        self.lanzar(confirmar=True)
        self.assertEqual(len(self.llamadas), 1)
        cfg = self.llamadas[0]
        self.assertEqual((cfg['conjunto'], cfg['score_threshold'], cfg['model_name'], cfg['perfil_aumento']),
                         ('test', 0.25, 'ssd_v1', c.PERFIL))
        registro = c.leer_json(c.CADENA / 'test_registro.json')
        self.assertEqual(registro[self.exp]['veces'], 1)
        self.assertEqual(registro[self.exp]['umbral'], 0.25)
        self.assertTrue((c.CADENA / 'resumen_test.csv').is_file())

    def test_no_repite_una_evaluacion_ya_hecha(self):
        self.lanzar(confirmar=True)
        salida = self.lanzar(confirmar=True)
        self.assertEqual(len(self.llamadas), 1)
        self.assertIn('YA evaluado', salida)

    def test_forzar_repite_y_lo_anota(self):
        self.lanzar(confirmar=True)
        self.lanzar(confirmar=True, forzar=True)
        self.assertEqual(len(self.llamadas), 2)
        self.assertEqual(c.leer_json(c.CADENA / 'test_registro.json')[self.exp]['veces'], 2)

    def test_sin_validacion_no_se_evalua_en_test(self):
        import shutil
        shutil.rmtree(c.WEEK2 / 'resultados_test' / f'{self.exp}_val')
        with self.assertRaises(RuntimeError):
            self.lanzar(confirmar=True)
        self.assertEqual(self.llamadas, [])

    def test_experimento_desconocido(self):
        with self.assertRaises(ValueError):
            c.evaluar_test('no_existe', confirmar=True)

    def test_fase1_son_los_siete_de_lr_001(self):
        estado = {'experimentos': {c.nombre(m, c.LR_BASE): {} for m in c.MODELOS}}
        self.assertEqual(c.seleccionar_experimentos('fase1', estado), [c.nombre(m, c.LR_BASE) for m in c.MODELOS])


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
