"""HU-23: GET /api/catalogo/reportes/panel/ (ventas, costo, merma y margen bruto)."""
from datetime import date
from decimal import Decimal

from catalogo.models import Categoria, Producto, RecetaDetalle
from .test_reportes_base import BaseReportesTest, a_las, pedido_servido
from catalogo.tests.test_catalogo import token_como_spring

URL = '/api/catalogo/reportes/panel/'


class PanelTest(BaseReportesTest):
    DESDE, HASTA = date(2026, 10, 1), date(2026, 10, 14)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Lomo saltado S/ 32.00: 0.300 kg de tomate y 0.200 kg de arroz a S/ 10.00 = S/ 5.00 de receta
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.tomate, cantidad_requerida=Decimal('0.300'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.arroz, cantidad_requerida=Decimal('0.200'))
        bebidas = Categoria.objects.create(restaurante=cls.central, nombre='Bebidas')
        cls.chicha = Producto.objects.create(categoria=bebidas, nombre='Chicha', precio=Decimal('12.00'),
                                             requiere_receta=False)

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def panel(self, desde=None, hasta=None):
        respuesta = self.client.get(URL, {'desde': (desde or self.DESDE).isoformat(),
                                          'hasta': (hasta or self.HASTA).isoformat()})
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return respuesta.json()

    def test_ventas_costo_merma_y_margen_en_soles_y_en_porcentaje(self):
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 3, a_las(date(2026, 10, 2)))   # 96
        pedido_servido(self.mesa_central, self.admin_central, self.chicha, 2, a_las(date(2026, 10, 9)))  # 24
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(date(2026, 10, 2)))   # S/ 9.00
        self.movimiento(self.arroz, 'CONSUMO', '-0.600', a_las(date(2026, 10, 2)))    # S/ 6.00
        self.movimiento(self.tomate, 'MERMA', '-0.300', a_las(date(2026, 10, 9)))     # S/ 3.00
        datos = self.panel()
        self.assertEqual((datos['ventas'], datos['costo_insumos'], datos['merma'], datos['margen']),
                         ('120.00', '15.00', '3.00', '102.00'))
        self.assertEqual((datos['costo_porcentaje'], datos['merma_porcentaje'], datos['margen_porcentaje']),
                         ('12.5', '2.5', '85.0'))

    def test_compara_con_el_periodo_anterior_del_mismo_largo(self):
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 2, a_las(date(2026, 9, 25)))   # 64 antes
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 3, a_las(date(2026, 10, 5)))   # 96 ahora
        anterior = self.panel()['anterior']
        self.assertEqual((anterior['desde'], anterior['hasta']), ('2026-09-17', '2026-09-30'))
        self.assertEqual((anterior['ventas'], anterior['variacion_ventas']), ('64.00', '50.0'))

    def test_sin_ventas_los_porcentajes_vienen_vacios(self):
        datos = self.panel()
        self.assertEqual((datos['ventas'], datos['margen']), ('0.00', '0.00'))
        self.assertIsNone(datos['margen_porcentaje'])
        self.assertIsNone(datos['anterior']['variacion_ventas'])

    def test_semanas_del_periodo(self):
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 1, a_las(date(2026, 10, 3)))
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 2, a_las(date(2026, 10, 10)))
        self.movimiento(self.tomate, 'CONSUMO', '-0.500', a_las(date(2026, 10, 10)))
        semanas = self.panel()['semanas']
        self.assertEqual([(s['desde'], s['hasta'], s['ventas'], s['costo']) for s in semanas],
                         [('2026-10-01', '2026-10-07', '32.00', '0.00'), ('2026-10-08', '2026-10-14', '64.00', '5.00')])

    def test_platillos_mas_vendidos_con_su_costo_de_receta(self):
        pedido_servido(self.mesa_central, self.admin_central, self.chicha, 4, a_las(date(2026, 10, 2)))
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 2, a_las(date(2026, 10, 2)))
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 9, a_las(date(2026, 10, 2)), 'ANULADO')
        platillos = self.panel()['platillos']
        self.assertEqual([(p['nombre'], p['vendidos']) for p in platillos], [('Chicha', 4), ('Lomo saltado', 2)])
        lomo = platillos[1]
        self.assertEqual((lomo['precio'], lomo['costo'], lomo['porcentaje_costo']), ('32.00', '5.00', '15.6'))
        self.assertIsNone(platillos[0]['costo'])

    def test_solo_su_restaurante(self):
        pedido_servido(self.mesa_norte, self.admin_norte, self.limonada, 5, a_las(date(2026, 10, 2)))
        self.assertEqual(self.panel()['ventas'], '0.00')

    def test_solo_el_administrador(self):
        for empleado in (self.almacenero_central, self.cocinero_central):
            self.con_token(token_como_spring(empleado))
            self.assertEqual(self.client.get(URL).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(URL).status_code, 401)
