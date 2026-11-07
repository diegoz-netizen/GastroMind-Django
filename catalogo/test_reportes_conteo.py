"""HU-30 en el reporte de la HU-20: lo que faltó en el último conteo físico suma al consumo real."""
from datetime import date
from decimal import Decimal

from .models import ConteoCiclico, RecetaDetalle
from .test_reportes_base import BaseReportesTest, a_las, pedido_servido
from .tests import token_como_spring

URL = '/api/catalogo/reportes/consumo/'
DIA = date(2026, 10, 15)


class ConteoEnConsumoRealTest(BaseReportesTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.tomate, cantidad_requerida=Decimal('0.100'))

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))
        # 4 lomos: el teórico de tomate es 0.400 kg y salió justo eso
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 4, a_las(DIA))
        self.movimiento(self.tomate, 'CONSUMO', '-0.400', a_las(DIA))

    def contar(self, contado, sistema, cuando, insumo=None):
        ConteoCiclico.objects.create(empleado=self.almacenero_central, ingrediente=insumo or self.tomate,
                                     cantidad_fisica_contada=Decimal(contado),
                                     stock_sistema=Decimal(sistema) if sistema is not None else None,
                                     fecha_registro=cuando)

    def fila_tomate(self):
        filas = self.client.get(URL, {'desde': DIA.isoformat(), 'hasta': DIA.isoformat()}).json()['filas']
        return next(f for f in filas if f['insumo'] == 'Tomate')

    def test_lo_que_falto_en_el_conteo_suma_al_real(self):
        self.contar('1.900', '2.000', a_las(DIA, 20))
        fila = self.fila_tomate()
        self.assertEqual((fila['real'], fila['diferencia'], fila['porcentaje']), ('0.500', '0.100', '25.0'))
        self.assertTrue(fila['resaltar'])

    def test_si_en_el_conteo_sobro_el_real_baja(self):
        self.contar('2.020', '2.000', a_las(DIA, 20))
        self.assertEqual(self.fila_tomate()['real'], '0.380')

    def test_vale_solo_el_ultimo_conteo_del_periodo(self):
        self.contar('1.500', '2.000', a_las(DIA, 9))
        self.contar('1.950', '2.000', a_las(DIA, 21))
        self.assertEqual(self.fila_tomate()['real'], '0.450')

    def test_no_cuentan_los_conteos_de_otro_periodo_ni_los_sin_stock_del_sistema(self):
        self.contar('0.000', '2.000', a_las(date(2026, 10, 16)))
        self.contar('0.000', None, a_las(DIA, 21))
        self.assertEqual(self.fila_tomate()['real'], '0.400')

    def test_un_insumo_solo_con_faltante_en_el_conteo_aparece_resaltado(self):
        self.contar('15.000', '20.000', a_las(DIA), insumo=self.arroz)
        filas = self.client.get(URL, {'desde': DIA.isoformat(), 'hasta': DIA.isoformat()}).json()['filas']
        arroz = next(f for f in filas if f['insumo'] == 'Arroz')
        self.assertEqual((arroz['teorico'], arroz['real'], arroz['porcentaje']), ('0.000', '5.000', None))
        self.assertTrue(arroz['resaltar'])
