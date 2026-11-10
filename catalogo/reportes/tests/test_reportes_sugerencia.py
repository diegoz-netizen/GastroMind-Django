"""HU-21: sugerencia de compra con el historial de consumo, la tendencia y la temporada (reportes/sugerencia.py)."""
from datetime import date
from decimal import Decimal
from unittest import mock

from catalogo.models import Ingrediente, Proveedor, ProveedorInsumo
from catalogo.reportes.sugerencia import factor_de_temporada, un_anio_antes
from .test_reportes_base import BaseReportesTest, a_las
from catalogo.tests.test_catalogo import token_como_spring

URL = '/api/catalogo/reportes/sugerencia/'
# Con hoy = 7/11, el historial de 8 semanas va del 12/09 al 6/11 y lo reciente (2 semanas) del 24/10 al 6/11
HOY = date(2026, 11, 7)


class SugerenciaCompraTest(BaseReportesTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        avicola = Proveedor.objects.create(restaurante=cls.central, nombre='Avícola Santa Rosa')
        mercado = Proveedor.objects.create(restaurante=cls.central, nombre='Mercado Mayorista')
        ProveedorInsumo.objects.create(proveedor=avicola, ingrediente=cls.tomate, precio_unitario=Decimal('4.00'),
                                       tiempo_entrega_dias=1, flete=Decimal('15'))
        ProveedorInsumo.objects.create(proveedor=mercado, ingrediente=cls.tomate, precio_unitario=Decimal('4.30'),
                                       tiempo_entrega_dias=2, flete=Decimal('5'))

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))
        hoy = mock.patch('catalogo.reportes.sugerencia.timezone.localdate', return_value=HOY)
        hoy.start()
        self.addCleanup(hoy.stop)

    def consumo_de_tomate(self):
        # 56 kg en 8 semanas = 1 kg al día; 28 kg en las 2 últimas = 2 kg al día (tendencia)
        self.movimiento(self.tomate, 'CONSUMO', '-28.000', a_las(date(2026, 9, 20)))
        self.movimiento(self.tomate, 'CONSUMO', '-28.000', a_las(date(2026, 11, 1)))

    def fila(self, datos, insumo):
        return next(f for f in datos['filas'] if f['id'] == insumo.id)

    def test_pide_lo_previsto_mas_el_minimo_menos_el_stock_con_el_proveedor_mas_barato(self):
        self.consumo_de_tomate()
        datos = self.client.get(URL).json()

        # Periodo analizado (CA-21)
        self.assertEqual((datos['desde'], datos['hasta']), ('2026-09-12', '2026-11-06'))
        self.assertEqual((datos['dias'], datos['semanas']), (7, 8))
        tomate = self.fila(datos, self.tomate)
        self.assertEqual(tomate['consumo_diario'], '1.000')
        self.assertEqual(tomate['tendencia_diaria'], '2.000')
        self.assertEqual(tomate['factor_temporada'], '1')
        # (0.6 × 2 + 0.4 × 1) × 7 días = 11.2; + mínimo 5 − stock 2 = 14.2 → 15 kg
        self.assertEqual(tomate['previsto'], '11.200')
        self.assertEqual(tomate['comprar'], '15')
        # 15 kg: Mercado 4.30 × 15 + 5 = 69.50; Avícola 4.00 × 15 + 15 = 75.00
        self.assertEqual(tomate['proveedor']['proveedor'], 'Mercado Mayorista')
        self.assertEqual(tomate['proveedor']['costo_total'], '69.50')
        # Lo que hay que comprar va primero
        self.assertEqual(datos['filas'][0]['id'], self.tomate.id)

    def test_con_stock_de_sobra_no_pide_nada_ni_proveedor(self):
        arroz = self.fila(self.client.get(URL).json(), self.arroz)
        self.assertEqual((arroz['previsto'], arroz['comprar']), ('0.000', '0'))
        self.assertIsNone(arroz['proveedor'])

    def test_la_temporada_del_anio_pasado_sube_lo_previsto(self):
        self.consumo_de_tomate()
        # Hace un año: 1 kg al día en las 8 semanas previas y 1.5 kg al día en la semana que se va a cubrir
        self.movimiento(self.tomate, 'CONSUMO', '-56.000', a_las(date(2025, 10, 1)))
        self.movimiento(self.tomate, 'CONSUMO', '-10.500', a_las(date(2025, 11, 10)))
        tomate = self.fila(self.client.get(URL).json(), self.tomate)
        self.assertEqual(tomate['factor_temporada'], '1.50')
        # 11.2 × 1.5 = 16.8; + 5 − 2 = 19.8 → 20 kg
        self.assertEqual((tomate['previsto'], tomate['comprar']), ('16.800', '20'))

    def test_se_puede_ajustar_los_dias_a_cubrir_y_las_semanas_de_historial(self):
        self.consumo_de_tomate()
        datos = self.client.get(URL, {'dias': 14, 'semanas': 2}).json()
        self.assertEqual((datos['desde'], datos['hasta']), ('2026-10-24', '2026-11-06'))
        tomate = self.fila(datos, self.tomate)
        # Solo las 2 semanas recientes: 2 kg al día × 14 días = 28; + 5 − 2 = 31
        self.assertEqual((tomate['previsto'], tomate['comprar']), ('28.000', '31'))

    def test_solo_cuenta_el_consumo_y_solo_insumos_receta_del_restaurante(self):
        sal = Ingrediente.objects.create(restaurante=self.central, nombre='Sal', unidad_medida='kg',
                                         stock_actual=Decimal('1'), stock_minimo=Decimal('1'),
                                         costo_unitario=Decimal('2.00'), tipo_control='LIBRE',
                                         dotacion_cantidad=Decimal('2'), dotacion_periodo='SEMANAL')
        self.movimiento(sal, 'CONSUMO', '-5.000', a_las(date(2026, 11, 1)))
        self.movimiento(self.arroz, 'MERMA', '-50.000', a_las(date(2026, 11, 1)))
        self.movimiento(self.pollo_norte, 'CONSUMO', '-50.000', a_las(date(2026, 11, 1)))
        datos = self.client.get(URL).json()
        self.assertEqual({f['insumo'] for f in datos['filas']}, {'Tomate', 'Arroz'})
        self.assertEqual(self.fila(datos, self.arroz)['previsto'], '0.000')

    def test_parametros_fuera_de_rango_responden_400(self):
        for params, campo in (({'dias': 0}, 'dias'), ({'dias': 'siete'}, 'dias'), ({'semanas': 60}, 'semanas')):
            with self.subTest(params=params):
                respuesta = self.client.get(URL, params)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.json()['campos'])

    def test_solo_el_administrador(self):
        for empleado in (self.almacenero_central, self.cocinero_central):
            self.con_token(token_como_spring(empleado))
            self.assertEqual(self.client.get(URL).status_code, 403)


class TemporadaTest(BaseReportesTest):

    def test_sin_datos_del_anio_pasado_el_factor_es_1(self):
        self.assertEqual(factor_de_temporada(Decimal('0'), Decimal('5'), Decimal('56'), Decimal('7')), Decimal('1'))
        self.assertEqual(factor_de_temporada(Decimal('56'), Decimal('0'), Decimal('56'), Decimal('7')), Decimal('1'))

    def test_el_factor_va_de_0_5_a_2(self):
        self.assertEqual(factor_de_temporada(Decimal('56'), Decimal('70'), Decimal('56'), Decimal('7')), Decimal('2'))
        self.assertEqual(factor_de_temporada(Decimal('56'), Decimal('1'), Decimal('56'), Decimal('7')), Decimal('0.5'))

    def test_el_29_de_febrero_pasa_al_28(self):
        self.assertEqual(un_anio_antes(date(2028, 2, 29)), date(2027, 2, 28))
        self.assertEqual(un_anio_antes(date(2026, 11, 7)), date(2025, 11, 7))
