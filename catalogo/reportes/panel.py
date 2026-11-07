"""
HU-23 (CA-23): panel del gerente. Ventas, costo de insumos, merma y margen bruto del periodo, en soles y en %,
frente al periodo anterior del mismo largo. Trae también las ventas y el costo por semana y los platillos más vendidos.
El detalle de la merma por motivo es del reporte de la HU-19.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Prefetch, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import PedidoDetalle, Producto, RecetaDetalle
from ..permissions import EsAdmin
from ..serializers import costo_de
from .comun import pedidos_entre, periodo, salidas_entre, soles, ventas_entre

PLATILLOS_EN_EL_PANEL = 5


def porcentaje(parte, total):
    """A un decimal; None si no hay total (no se inventa un 0 %)."""
    return str((Decimal(parte) * 100 / total).quantize(Decimal('0.1'))) if total else None


def resumen(restaurante_id, desde, hasta):
    ventas = ventas_entre(restaurante_id, desde, hasta)
    salidas = salidas_entre(restaurante_id, desde, hasta)
    costo, merma = salidas['CONSUMO'], salidas['MERMA']
    return ventas, costo, merma, soles(ventas - costo - merma)


def semanas_entre(restaurante_id, desde, hasta):
    semanas = []
    inicio = desde
    while inicio <= hasta:
        fin = min(inicio + timedelta(days=6), hasta)
        semanas.append({'desde': inicio, 'hasta': fin, 'ventas': str(ventas_entre(restaurante_id, inicio, fin)),
                        'costo': str(salidas_entre(restaurante_id, inicio, fin)['CONSUMO'])})
        inicio = fin + timedelta(days=1)
    return semanas


def mas_vendidos(restaurante_id, desde, hasta):
    vendidos = (PedidoDetalle.objects
                .filter(pedido_id__in=pedidos_entre(restaurante_id, desde, hasta).values('id'), estado='SERVIDO')
                .values('producto_id').annotate(porciones=Sum('cantidad')).order_by('-porciones', 'producto_id')
                [:PLATILLOS_EN_EL_PANEL])
    porciones = {v['producto_id']: v['porciones'] for v in vendidos}
    productos = Producto.objects.filter(id__in=porciones).prefetch_related(
        Prefetch('detalles_receta', queryset=RecetaDetalle.objects.select_related('ingrediente')))
    filas = []
    for producto in productos:
        costo = costo_de(producto) if producto.requiere_receta else None
        filas.append({'id': producto.id, 'nombre': producto.nombre, 'vendidos': porciones[producto.id],
                      'precio': str(producto.precio), 'costo': str(costo) if costo is not None else None,
                      'porcentaje_costo': porcentaje(costo, producto.precio) if costo is not None else None})
    filas.sort(key=lambda f: (-f['vendidos'], f['nombre']))
    return filas


class PanelView(APIView):
    """GET /api/catalogo/reportes/panel/?desde=&hasta=   Solo ADMINISTRADOR."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        r = request.user.restaurante_id
        desde, hasta = periodo(request)
        ventas, costo, merma, margen = resumen(r, desde, hasta)

        dias = (hasta - desde).days + 1
        anterior_desde, anterior_hasta = desde - timedelta(days=dias), desde - timedelta(days=1)
        ventas_antes, _, _, margen_antes = resumen(r, anterior_desde, anterior_hasta)

        return Response({
            'desde': desde, 'hasta': hasta,
            'ventas': str(ventas),
            'costo_insumos': str(costo), 'costo_porcentaje': porcentaje(costo, ventas),
            'merma': str(merma), 'merma_porcentaje': porcentaje(merma, ventas),
            # CA-23: margen bruto en soles y en %
            'margen': str(margen), 'margen_porcentaje': porcentaje(margen, ventas),
            'anterior': {'desde': anterior_desde, 'hasta': anterior_hasta, 'ventas': str(ventas_antes),
                         'margen': str(margen_antes),
                         'variacion_ventas': porcentaje(ventas - ventas_antes, ventas_antes)},
            'semanas': semanas_entre(r, desde, hasta),
            'platillos': mas_vendidos(r, desde, hasta),
        })
