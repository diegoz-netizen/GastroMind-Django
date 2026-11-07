"""Base de los reportes del Sprint 4 (catalogo/reportes/comun.py). Cada HU de reportes trae su propio test_reportes_*.py."""
from datetime import date, datetime, time, timezone
from decimal import Decimal
from unittest import mock

from django.test import RequestFactory
from django.utils import timezone as dj_timezone
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from .models import Categoria, Mesa, MovimientoInventario, Pedido, PedidoDetalle, Producto
from .reportes.comun import periodo, rango, salidas_entre, ventas_entre
from .tests import BaseCatalogoTest


def a_las(dia, hora=12, minuto=0):
    """Esa hora de Perú, como la guarda Spring."""
    return dj_timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


def pedido_servido(mesa, empleado, producto, cantidad, cuando, estado='SERVIDO'):
    pedido = Pedido.objects.create(mesa=mesa, empleado=empleado, estado='CERRADO', fecha_registro=cuando)
    return PedidoDetalle.objects.create(pedido_id=pedido.id, producto=producto, cantidad=cantidad, estado=estado)


class BaseReportesTest(BaseCatalogoTest):
    """Datos para los reportes: platillos vendidos y movimientos del almacén en días conocidos."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mesa_central = Mesa.objects.create(restaurante=cls.central, numero=1, estado='LIBRE')
        cls.mesa_norte = Mesa.objects.create(restaurante=cls.norte, numero=1, estado='LIBRE')
        fondos = Categoria.objects.create(restaurante=cls.central, nombre='Fondos')
        cls.lomo = Producto.objects.create(categoria=fondos, nombre='Lomo saltado', precio=Decimal('32.00'))
        bebidas_norte = Categoria.objects.create(restaurante=cls.norte, nombre='Bebidas')
        cls.limonada = Producto.objects.create(categoria=bebidas_norte, nombre='Limonada', precio=Decimal('8.00'))

    def movimiento(self, insumo, tipo, cantidad, cuando):
        return MovimientoInventario.objects.create(ingrediente=insumo, tipo=tipo, cantidad=Decimal(cantidad),
                                                   saldo=Decimal('0'), fecha=cuando)


class PeriodoTest(BaseReportesTest):

    def periodo(self, **params):
        return periodo(Request(RequestFactory().get('/', params)))

    def test_sin_fechas_es_del_1_del_mes_a_hoy(self):
        with mock.patch('catalogo.reportes.comun.timezone.localdate', return_value=date(2026, 11, 7)):
            self.assertEqual(self.periodo(), (date(2026, 11, 1), date(2026, 11, 7)))

    def test_con_fechas_las_respeta(self):
        self.assertEqual(self.periodo(desde='2026-10-01', hasta='2026-10-31'), (date(2026, 10, 1), date(2026, 10, 31)))

    def test_fecha_inicial_mayor_que_la_final_responde_400(self):
        with self.assertRaises(ValidationError) as error:
            self.periodo(desde='2026-11-05', hasta='2026-11-01')
        self.assertIn('desde', error.exception.detail)

    def test_fecha_mal_escrita_responde_400(self):
        for mala in ('05/11/2026', '2026-13-01', 'ayer'):
            with self.subTest(mala=mala), self.assertRaises(ValidationError) as error:
                self.periodo(hasta=mala)
            self.assertIn('hasta', error.exception.detail)

    def test_el_rango_va_de_medianoche_a_medianoche_de_peru(self):
        inicio, fin = rango(date(2026, 11, 1), date(2026, 11, 2))
        # Perú es UTC-5: el 1/11 empieza a las 05:00 UTC y el rango termina al empezar el 3/11
        self.assertEqual(inicio.astimezone(timezone.utc), datetime(2026, 11, 1, 5, tzinfo=timezone.utc))
        self.assertEqual(dj_timezone.localtime(fin).date(), date(2026, 11, 3))
        self.assertEqual(fin - inicio, datetime(2026, 11, 3) - datetime(2026, 11, 1))


class VentasEntreTest(BaseReportesTest):
    DIA = date(2026, 10, 15)

    def test_suma_solo_lo_servido_del_restaurante_y_del_periodo(self):
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 2, a_las(self.DIA))              # 64
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 1, a_las(self.DIA, 23, 59))      # 32
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 5, a_las(self.DIA), 'ANULADO')
        pedido_servido(self.mesa_central, self.admin_central, self.lomo, 3, a_las(date(2026, 10, 16)))
        pedido_servido(self.mesa_norte, self.admin_norte, self.limonada, 4, a_las(self.DIA))
        self.assertEqual(ventas_entre(self.central.id, self.DIA, self.DIA), Decimal('96.00'))
        self.assertEqual(ventas_entre(self.norte.id, self.DIA, self.DIA), Decimal('32.00'))

    def test_sin_ventas_da_cero(self):
        self.assertEqual(ventas_entre(self.central.id, self.DIA, self.DIA), Decimal('0'))


class SalidasEntreTest(BaseReportesTest):
    DIA = date(2026, 10, 15)

    def test_valora_consumo_y_merma_al_costo_del_insumo_y_deja_fuera_los_ingresos(self):
        # Tomate y Arroz cuestan S/ 10.00 en la base de los tests
        self.movimiento(self.tomate, 'CONSUMO', '-0.500', a_las(self.DIA))
        self.movimiento(self.arroz, 'CONSUMO', '-1.250', a_las(self.DIA))
        self.movimiento(self.tomate, 'MERMA', '-0.100', a_las(self.DIA))
        self.movimiento(self.tomate, 'INGRESO', '5.000', a_las(self.DIA))
        self.movimiento(self.tomate, 'CONSUMO', '-9.000', a_las(date(2026, 10, 16)))
        self.movimiento(self.pollo_norte, 'CONSUMO', '-2.000', a_las(self.DIA))
        salidas = salidas_entre(self.central.id, self.DIA, self.DIA)
        self.assertEqual(salidas['CONSUMO'], Decimal('17.50'))
        self.assertEqual(salidas['MERMA'], Decimal('1.00'))

    def test_sin_movimientos_da_cero_en_los_dos(self):
        self.assertEqual(salidas_entre(self.central.id, self.DIA, self.DIA), {'CONSUMO': 0, 'MERMA': 0})
