"""Regresiones para evitar validaciones y acuerdos vacíos o engañosos."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from revisar_anotaciones import acuerdo, validar


def escribir_xml(ruta, cajas=((10, 10, 60, 60),), ancho=1280):
    objetos = ''.join(
        '<object><name>robot</name><difficult>0</difficult><bndbox>'
        f'<xmin>{x1}</xmin><ymin>{y1}</ymin><xmax>{x2}</xmax><ymax>{y2}</ymax>'
        '</bndbox></object>' for x1, y1, x2, y2 in cajas
    )
    ruta.write_text(f'<annotation><filename>{ruta.stem}.jpg</filename>'
                    f'<size><width>{ancho}</width><height>720</height></size>'
                    f'{objetos}</annotation>', encoding='utf-8')


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)

    def ejecutar(self, funcion, *args):
        salida = StringIO()
        with redirect_stdout(salida):
            codigo = funcion(*args)
        return codigo, salida.getvalue()

    def ronda(self, cajas=((10, 10, 60, 60),)):
        carpetas = [self.raiz / 'uno', self.raiz / 'dos']
        for carpeta in carpetas:
            carpeta.mkdir()
            for n in range(20):
                escribir_xml(carpeta / f'imagen_{n:02d}.xml', cajas)
        return [str(c) for c in carpetas]

    def lote(self, caja, ancho=1280):
        seq = self.raiz / 'VIDEO_01'
        (seq / 'images').mkdir(parents=True)
        (seq / 'labels').mkdir()
        (seq / 'images/frame.jpg').touch()
        escribir_xml(seq / 'labels/frame.xml', (caja,), ancho)
        return str(self.raiz)

    def test_no_aprueba_carpetas_vacias(self):
        a, b = self.raiz / 'a', self.raiz / 'b'
        a.mkdir(); b.mkdir()
        codigo, salida = self.ejecutar(acuerdo, [str(a), str(b)])
        self.assertEqual(codigo, 1)
        self.assertIn('calibración está pendiente', salida)

    def test_no_aprueba_distintas_imagenes(self):
        carpetas = self.ronda()
        ruta = Path(carpetas[1]) / 'imagen_00.xml'
        ruta.rename(ruta.with_name('otra_imagen.xml'))
        self.assertEqual(self.ejecutar(acuerdo, carpetas)[0], 1)

    def test_rechaza_misma_carpeta_dos_veces(self):
        carpetas = self.ronda()
        self.assertEqual(self.ejecutar(acuerdo, [carpetas[0], carpetas[0]])[0], 1)

    def test_acuerdo_de_veinte_imagenes_correcto(self):
        codigo, salida = self.ejecutar(acuerdo, self.ronda())
        self.assertEqual(codigo, 0)
        self.assertIn('IoU medio global: 1.000', salida)

    def test_no_aprueba_si_falta_un_robot(self):
        carpetas = self.ronda()
        escribir_xml(Path(carpetas[1]) / 'imagen_00.xml', ())
        self.assertEqual(self.ejecutar(acuerdo, carpetas)[0], 1)

    def test_no_aprueba_una_ronda_solo_de_negativos(self):
        self.assertEqual(self.ejecutar(acuerdo, self.ronda(()))[0], 1)

    def test_no_aprueba_iou_inferior_a_objetivo(self):
        carpetas = self.ronda()
        for ruta in Path(carpetas[1]).glob('*.xml'):
            escribir_xml(ruta, ((20, 10, 70, 60),))
        self.assertEqual(self.ejecutar(acuerdo, carpetas)[0], 1)

    def test_no_aprueba_acuerdo_sobre_cajas_fuera_de_imagen(self):
        self.assertEqual(self.ejecutar(acuerdo, self.ronda(((-10, 10, 40, 60),)))[0], 1)

    def test_no_aprueba_dataset_vacio(self):
        self.assertEqual(self.ejecutar(validar, str(self.raiz))[0], 1)

    def test_rechaza_cajas_menores_de_diez_pixels(self):
        self.assertEqual(self.ejecutar(validar, self.lote((10, 10, 15, 60)))[0], 1)

    def test_rechaza_xml_sin_dimensiones_validas(self):
        self.assertEqual(self.ejecutar(validar, self.lote((10, 10, 60, 60), 0))[0], 1)

    def test_valida_lote_con_caja_correcta(self):
        self.assertEqual(self.ejecutar(validar, self.lote((10, 10, 60, 60)))[0], 0)


if __name__ == '__main__':
    unittest.main()
