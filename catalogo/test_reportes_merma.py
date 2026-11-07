"""HU-19: GET /api/catalogo/reportes/merma/ (% de merma por periodo, insumo y motivo)."""
from datetime import date
from decimal import Decimal

from .models import Ingrediente, MotivoMerma, MovimientoInventario, RegistroMerma
from .test_reportes_base import BaseReportesTest, a_las
from .tests import token_como_spring

URL = '/api/catalogo/reportes/merma/'
DIA = date(2026, 10, 15)


class MermaReporteTest(BaseReportesTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Tomate y Arroz cuestan S/ 10.00 el kg en la base de los tests
        cls.servilletas = Ingrediente.objects.create(
            restaurante=cls.central, nombre='Servilletas', unidad_medida='unidades', stock_actual=Decimal('500'),
            stock_minimo=Decimal('10'), costo_unitario=Decimal('0.10'))
        cls.vencido = MotivoMerma.objects.create(nombre='VENCIDO', es_global=True)
        cls.quemado = MotivoMerma.objects.create(nombre='QUEMADO', es_global=True)
        cls.propio_central = MotivoMerma.objects.create(restaurante=cls.central, nombre='CAIDA')
        cls.propio_norte = MotivoMerma.objects.create(restaurante=cls.norte, nombre='ROBO')

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def merma(self, insumo, cantidad, motivo, cuando=None):
        """Como la registra Spring (HU-17): el registro_merma y su movimiento MERMA."""
        cuando = cuando or a_las(DIA)
        registro = RegistroMerma.objects.create(empleado=self.almacenero_central, ingrediente=insumo,
                                                cantidad=Decimal(cantidad), motivo=motivo, fecha_registro=cuando)
        MovimientoInventario.objects.create(ingrediente=insumo, tipo='MERMA', cantidad=-Decimal(cantidad),
                                            saldo=Decimal('0'), fecha=cuando, registro_merma_id=registro.id)

    def reporte(self, **params):
        respuesta = self.client.get(URL, {'desde': DIA.isoformat(), 'hasta': DIA.isoformat(), **params})
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return respuesta.json()

    def test_porcentaje_de_merma_sobre_el_consumo_total_de_cada_insumo(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))
        self.merma(self.tomate, '0.100', self.vencido)
        self.movimiento(self.arroz, 'CONSUMO', '-2.000', a_las(DIA))
        filas = self.reporte()['filas']
        self.assertEqual(filas[0], {'id': self.tomate.id, 'insumo': 'Tomate', 'unidad': 'kg', 'consumo': '1.000',
                                    'merma': '0.100', 'porcentaje': '10.0', 'costo_merma': '1.00'})
        self.assertEqual((filas[1]['insumo'], filas[1]['porcentaje']), ('Arroz', '0.0'))

    def test_el_total_va_en_soles_para_no_sumar_kilos_con_unidades(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))      # S/ 9.00
        self.merma(self.tomate, '0.100', self.vencido)                     # S/ 1.00
        self.movimiento(self.servilletas, 'CONSUMO', '-70', a_las(DIA))    # S/ 7.00
        self.merma(self.servilletas, '30', self.quemado)                   # S/ 3.00: 30 % de las servilletas
        datos = self.reporte()
        self.assertEqual(datos['total'], {'costo_consumo': '20.00', 'costo_merma': '4.00', 'porcentaje': '20.0'})
        self.assertEqual([(f['insumo'], f['porcentaje']) for f in datos['filas']],
                         [('Servilletas', '30.0'), ('Tomate', '10.0')])

    def test_filtrar_por_motivo_cuenta_solo_esa_merma_sobre_todo_el_consumo(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.700', a_las(DIA))
        self.merma(self.tomate, '0.100', self.vencido)
        self.merma(self.tomate, '0.200', self.quemado)
        self.assertEqual(self.reporte()['filas'][0]['porcentaje'], '30.0')
        tomate = self.reporte(motivo=self.quemado.id)['filas'][0]
        self.assertEqual((tomate['consumo'], tomate['merma'], tomate['porcentaje']), ('1.000', '0.200', '20.0'))

    def test_filtrar_por_insumo_deja_solo_ese(self):
        self.merma(self.tomate, '0.100', self.vencido)
        self.movimiento(self.arroz, 'CONSUMO', '-1.000', a_las(DIA))
        self.merma(self.arroz, '0.250', self.quemado)
        datos = self.reporte(insumo=self.arroz.id)
        self.assertEqual([f['insumo'] for f in datos['filas']], ['Arroz'])
        self.assertEqual(datos['motivos'], [{'motivo': 'QUEMADO', 'costo': '2.50', 'porcentaje': '100.0'}])

    def test_merma_por_motivo_de_mayor_a_menor_costo(self):
        self.merma(self.tomate, '0.100', self.vencido)                     # S/ 1.00
        self.merma(self.arroz, '0.200', self.quemado)                      # S/ 2.00
        # Una merma vieja, sin registro_merma (carga inicial)
        self.movimiento(self.tomate, 'MERMA', '-0.100', a_las(DIA))        # S/ 1.00
        self.assertEqual(self.reporte()['motivos'], [
            {'motivo': 'QUEMADO', 'costo': '2.00', 'porcentaje': '50.0'},
            {'motivo': 'Sin motivo', 'costo': '1.00', 'porcentaje': '25.0'},
            {'motivo': 'VENCIDO', 'costo': '1.00', 'porcentaje': '25.0'},
        ])

    def test_no_cuenta_ingresos_otro_periodo_ni_otro_restaurante(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))
        self.merma(self.tomate, '0.100', self.vencido)
        self.movimiento(self.tomate, 'INGRESO', '5.000', a_las(DIA))
        self.merma(self.tomate, '1.000', self.vencido, a_las(date(2026, 10, 16)))
        self.merma(self.pollo_norte, '2.000', self.vencido)
        datos = self.reporte()
        self.assertEqual([(f['insumo'], f['porcentaje']) for f in datos['filas']], [('Tomate', '10.0')])
        self.assertEqual(datos['total']['costo_merma'], '1.00')

    def test_sin_movimientos_todo_en_cero(self):
        datos = self.reporte()
        self.assertEqual((datos['filas'], datos['motivos']), ([], []))
        self.assertEqual(datos['total'], {'costo_consumo': '0.00', 'costo_merma': '0.00', 'porcentaje': '0.0'})

    def test_motivos_para_el_filtro_son_los_globales_y_los_del_restaurante(self):
        nombres = [m['nombre'] for m in self.reporte()['motivos_disponibles']]
        self.assertEqual(nombres, ['CAIDA', 'QUEMADO', 'VENCIDO'])

    def test_insumo_o_motivo_de_otro_restaurante_o_inexistente_responden_400(self):
        for campo, valor in (('insumo', self.pollo_norte.id), ('insumo', 'abc'), ('motivo', self.propio_norte.id),
                             ('motivo', 9999)):
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.client.get(URL, {campo: valor})
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.json()['campos'])

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
