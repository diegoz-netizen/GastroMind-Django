"""HU-24: GET /api/catalogo/reportes/exportar/ (Excel de merma, teórico contra real e inventario)."""
from datetime import date
from decimal import Decimal
from io import BytesIO

from openpyxl import load_workbook

from catalogo.models import MotivoMerma, MovimientoInventario, RegistroMerma
from .test_reportes_base import BaseReportesTest, a_las
from catalogo.tests.test_catalogo import token_como_spring

URL = '/api/catalogo/reportes/exportar/'
DIA = date(2026, 10, 15)
XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class ExportarReporteTest(BaseReportesTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.vencido = MotivoMerma.objects.create(nombre='VENCIDO', es_global=True)
        cls.quemado = MotivoMerma.objects.create(nombre='QUEMADO', es_global=True)

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def merma(self, insumo, cantidad, motivo):
        registro = RegistroMerma.objects.create(empleado=self.almacenero_central, ingrediente=insumo,
                                                cantidad=Decimal(cantidad), motivo=motivo, fecha_registro=a_las(DIA))
        MovimientoInventario.objects.create(ingrediente=insumo, tipo='MERMA', cantidad=-Decimal(cantidad),
                                            saldo=Decimal('0'), fecha=a_las(DIA), registro_merma_id=registro.id)

    def excel(self, **params):
        respuesta = self.client.get(URL, params)
        self.assertEqual(respuesta.status_code, 200, respuesta.content[:300])
        self.assertEqual(respuesta['Content-Type'], XLSX)
        hoja = load_workbook(BytesIO(respuesta.content)).active
        return respuesta, [[c for c in fila] for fila in hoja.iter_rows(values_only=True)]

    @staticmethod
    def fila(filas, primero):
        return next(f for f in filas if f[0] == primero)

    def test_merma_trae_los_mismos_numeros_que_la_pantalla_y_los_filtros(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))
        self.merma(self.tomate, '0.100', self.vencido)
        self.movimiento(self.arroz, 'CONSUMO', '-2.000', a_las(DIA))
        pantalla = self.client.get('/api/catalogo/reportes/merma/',
                                   {'desde': DIA.isoformat(), 'hasta': DIA.isoformat()}).json()

        respuesta, filas = self.excel(tipo='merma', desde=DIA.isoformat(), hasta=DIA.isoformat())
        self.assertIn('gastromind_merma_2026-10-15_2026-10-15.xlsx', respuesta['Content-Disposition'])
        self.assertEqual(filas[0][0], 'GastroMind · Merma')
        self.assertEqual(filas[1][0], 'Sede Central')
        self.assertIn('Periodo: 15/10/2026 al 15/10/2026', [f[0] for f in filas])
        self.assertIn('Filtros: insumo todos · motivo todos', [f[0] for f in filas])
        tomate = self.fila(filas, 'Tomate')
        esperado = pantalla['filas'][0]
        # En el Excel van como número (openpyxl los lee como float), no como texto
        self.assertEqual(tomate[:6], ['Tomate', 'kg', float(esperado['consumo']), float(esperado['merma']),
                                      float(esperado['porcentaje']), float(esperado['costo_merma'])])
        self.assertEqual(self.fila(filas, 'VENCIDO')[:3], ['VENCIDO', 1.0, 100.0])

    def test_merma_respeta_el_filtro_de_insumo_y_motivo(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))
        self.merma(self.tomate, '0.100', self.vencido)
        self.movimiento(self.arroz, 'CONSUMO', '-2.000', a_las(DIA))
        _, filas = self.excel(tipo='merma', desde=DIA.isoformat(), hasta=DIA.isoformat(),
                              insumo=self.tomate.id, motivo=self.quemado.id)
        self.assertIn('Filtros: insumo Tomate · motivo QUEMADO', [f[0] for f in filas])
        self.assertEqual([f[0] for f in filas].count('Arroz'), 0)
        # Con el motivo QUEMADO no hay merma del tomate: 0 %
        self.assertEqual(self.fila(filas, 'Tomate')[4], 0)

    def test_consumo_marca_lo_que_hay_que_revisar(self):
        self.movimiento(self.tomate, 'CONSUMO', '-0.900', a_las(DIA))
        _, filas = self.excel(tipo='consumo', desde=DIA.isoformat(), hasta=DIA.isoformat())
        self.assertEqual(filas[0][0], 'GastroMind · Teórico vs. real')
        tomate = self.fila(filas, 'Tomate')
        # Sin platillos servidos no hay teórico: lo que salió se resalta
        self.assertEqual(tomate[2:4], [0, 0.9])
        self.assertEqual(tomate[6], 'Sí')

    def test_inventario_trae_el_stock_de_hoy_solo_del_restaurante(self):
        _, filas = self.excel(tipo='inventario')
        nombres = [f[0] for f in filas]
        self.assertIn('Tomate', nombres)
        self.assertNotIn('Pollo', nombres)  # es de la Sede Norte
        tomate = self.fila(filas, 'Tomate')
        self.assertEqual(tomate[3:5], [2, 5])
        self.assertEqual(tomate[7], 'Sí')   # 2 kg con mínimo 5

    def test_tipo_desconocido_o_filtro_ajeno_responde_400(self):
        self.assertEqual(self.client.get(URL, {'tipo': 'ventas'}).status_code, 400)
        self.assertEqual(self.client.get(URL).status_code, 400)
        respuesta = self.client.get(URL, {'tipo': 'merma', 'insumo': self.pollo_norte.id})
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.get(URL, {'tipo': 'consumo', 'desde': '2026-11-07', 'hasta': '2026-11-01'})
        self.assertEqual(respuesta.status_code, 400)

    def test_solo_el_administrador(self):
        self.con_token(token_como_spring(self.almacenero_central))
        self.assertEqual(self.client.get(URL, {'tipo': 'inventario'}).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(URL, {'tipo': 'inventario'}).status_code, 401)
