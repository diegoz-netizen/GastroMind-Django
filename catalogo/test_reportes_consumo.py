"""HU-20: GET /api/catalogo/reportes/consumo/ (consumo teórico contra real)."""
from datetime import date
from decimal import Decimal

from .models import Ingrediente, RecetaDetalle
from .test_reportes_base import BaseReportesTest, a_las, pedido_servido
from .tests import token_como_spring

URL = '/api/catalogo/reportes/consumo/'
DIA = date(2026, 10, 15)


class ConsumoTeoricoRealTest(BaseReportesTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.servilletas = Ingrediente.objects.create(
            restaurante=cls.central, nombre='Servilletas', unidad_medida='unidades', stock_actual=Decimal('100'),
            stock_minimo=Decimal('10'), costo_unitario=Decimal('0.10'), tipo_control='LIBRE',
            dotacion_cantidad=Decimal('50'), dotacion_periodo='SEMANAL')
        # Lomo saltado: 0.100 kg de tomate y 0.150 kg de arroz (y servilletas, que es LIBRE)
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.tomate, cantidad_requerida=Decimal('0.100'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.arroz, cantidad_requerida=Decimal('0.150'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.servilletas, cantidad_requerida=Decimal('2'))

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def reporte(self, **params):
        respuesta = self.client.get(URL, {'desde': DIA.isoformat(), 'hasta': DIA.isoformat(), **params})
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return {f['insumo']: f for f in respuesta.json()['filas']}

    def vender_lomos(self, cantidad, cuando=None, estado='SERVIDO'):
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, cantidad, cuando or a_las(DIA), estado)

    def test_si_salio_lo_que_dice_la_receta_no_hay_diferencia(self):
        self.vender_lomos(4)
        self.movimiento(self.tomate, 'CONSUMO', '-0.400', a_las(DIA))
        self.movimiento(self.arroz, 'CONSUMO', '-0.600', a_las(DIA))
        filas = self.reporte()
        self.assertEqual(filas['Tomate'], {'id': self.tomate.id, 'insumo': 'Tomate', 'unidad': 'kg',
                                           'teorico': '0.400', 'real': '0.400', 'diferencia': '0.000',
                                           'porcentaje': '0.0', 'resaltar': False})
        self.assertEqual(filas['Arroz']['teorico'], '0.600')

    def test_la_merma_suma_al_real_y_mas_de_5_por_ciento_se_resalta(self):
        self.vender_lomos(4)
        self.movimiento(self.tomate, 'CONSUMO', '-0.400', a_las(DIA))
        self.movimiento(self.tomate, 'MERMA', '-0.050', a_las(DIA))   # +12.5 %
        self.movimiento(self.arroz, 'CONSUMO', '-0.600', a_las(DIA))
        self.movimiento(self.arroz, 'MERMA', '-0.030', a_las(DIA))    # +5.0 %: justo en el límite, no se resalta
        filas = self.reporte()
        self.assertEqual((filas['Tomate']['real'], filas['Tomate']['diferencia'], filas['Tomate']['porcentaje']),
                         ('0.450', '0.050', '12.5'))
        self.assertTrue(filas['Tomate']['resaltar'])
        self.assertEqual(filas['Arroz']['porcentaje'], '5.0')
        self.assertFalse(filas['Arroz']['resaltar'])

    def test_lo_mas_desviado_sale_primero(self):
        self.vender_lomos(4)
        self.movimiento(self.tomate, 'CONSUMO', '-0.400', a_las(DIA))
        self.movimiento(self.arroz, 'CONSUMO', '-0.900', a_las(DIA))  # +50 %
        datos = self.client.get(URL, {'desde': DIA.isoformat(), 'hasta': DIA.isoformat()}).json()
        self.assertEqual([f['insumo'] for f in datos['filas']], ['Arroz', 'Tomate'])
        self.assertEqual(datos['umbral'], '5')

    def test_insumo_que_solo_se_mermo_sale_sin_porcentaje_y_resaltado(self):
        self.movimiento(self.tomate, 'MERMA', '-0.200', a_las(DIA))
        filas = self.reporte()
        self.assertEqual((filas['Tomate']['teorico'], filas['Tomate']['real'], filas['Tomate']['porcentaje']),
                         ('0.000', '0.200', None))
        self.assertTrue(filas['Tomate']['resaltar'])

    def test_no_cuenta_libres_anulados_otro_periodo_ni_otro_restaurante(self):
        self.vender_lomos(4)
        self.vender_lomos(9, estado='ANULADO')
        self.vender_lomos(9, cuando=a_las(date(2026, 10, 16)))
        self.movimiento(self.tomate, 'CONSUMO', '-5.000', a_las(date(2026, 10, 16)))
        self.movimiento(self.servilletas, 'CONSUMO', '-8', a_las(DIA))
        self.movimiento(self.pollo_norte, 'CONSUMO', '-1.000', a_las(DIA))
        filas = self.reporte()
        self.assertEqual(set(filas), {'Tomate', 'Arroz'})
        self.assertEqual((filas['Tomate']['teorico'], filas['Tomate']['real']), ('0.400', '0.000'))

    def test_sin_ventas_ni_salidas_la_lista_viene_vacia(self):
        self.assertEqual(self.reporte(), {})

    def test_sin_fechas_usa_el_mes_en_curso(self):
        datos = self.client.get(URL).json()
        self.assertEqual(datos['hasta'][:7], datos['desde'][:7])
        self.assertTrue(datos['desde'].endswith('-01'))

    def test_fechas_invertidas_responden_400(self):
        respuesta = self.client.get(URL, {'desde': '2026-10-20', 'hasta': '2026-10-01'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('desde', respuesta.json()['campos'])

    def test_solo_el_administrador(self):
        for empleado in (self.almacenero_central, self.cocinero_central):
            self.con_token(token_como_spring(empleado))
            self.assertEqual(self.client.get(URL).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(URL).status_code, 401)
