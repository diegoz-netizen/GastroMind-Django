"""
HU-20 (CA-20): consumo teórico contra real de cada insumo en un periodo.
- Teórico: platillos SERVIDOS en el periodo × su receta. Solo insumos RECETA: los LIBRE no se descuentan al servir
  (HU-13) y van por dotación y conteo.
- Real: lo que salió según el inventario (CONSUMO + MERMA), más lo que faltó en el último conteo físico del
  periodo (HU-30: stock del sistema − lo contado). Si en el conteo sobró, el real baja.
Se resaltan las diferencias mayores a 5 %.
"""
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import ConteoCiclico, Ingrediente, MovimientoInventario, PedidoDetalle, RecetaDetalle
from ..permissions import EsAdmin
from .comun import pedidos_entre, periodo, rango

UMBRAL_DESVIACION = Decimal('5')
TRES = Decimal('0.001')


def faltantes_del_conteo(restaurante_id, inicio, fin):
    """HU-30: por insumo RECETA, lo que faltó en su último conteo del periodo (negativo si sobró)."""
    conteos = (ConteoCiclico.objects
               .filter(ingrediente__restaurante_id=restaurante_id, ingrediente__tipo_control='RECETA',
                       stock_sistema__isnull=False, fecha_registro__gte=inicio, fecha_registro__lt=fin)
               .order_by('ingrediente_id', '-fecha_registro', '-id')
               .values('ingrediente_id', 'stock_sistema', 'cantidad_fisica_contada'))
    faltantes = {}
    for conteo in conteos:
        # El primero de cada insumo es el más reciente
        faltantes.setdefault(conteo['ingrediente_id'], conteo['stock_sistema'] - conteo['cantidad_fisica_contada'])
    return faltantes


def teorico_vs_real(restaurante_id, desde, hasta):
    vendidos = (PedidoDetalle.objects
                .filter(pedido_id__in=pedidos_entre(restaurante_id, desde, hasta).values('id'), estado='SERVIDO')
                .values('producto_id').annotate(porciones=Sum('cantidad')))
    porciones = {v['producto_id']: v['porciones'] for v in vendidos}

    teorico = defaultdict(Decimal)
    recetas = RecetaDetalle.objects.filter(producto_id__in=porciones, ingrediente__tipo_control='RECETA')
    for linea in recetas.values('producto_id', 'ingrediente_id', 'cantidad_requerida'):
        teorico[linea['ingrediente_id']] += linea['cantidad_requerida'] * porciones[linea['producto_id']]

    inicio, fin = rango(desde, hasta)
    salidas = (MovimientoInventario.objects
               .filter(ingrediente__restaurante_id=restaurante_id, ingrediente__tipo_control='RECETA',
                       tipo__in=('CONSUMO', 'MERMA'), fecha__gte=inicio, fecha__lt=fin)
               .values('ingrediente_id').annotate(total=Sum('cantidad')))
    real = defaultdict(Decimal, {s['ingrediente_id']: -s['total'] for s in salidas})
    for insumo_id, faltante in faltantes_del_conteo(restaurante_id, inicio, fin).items():
        real[insumo_id] += faltante

    insumos = Ingrediente.objects.filter(id__in=set(teorico) | set(real), restaurante_id=restaurante_id)
    filas = []
    for insumo in insumos:
        t = teorico.get(insumo.id, Decimal('0'))
        r = real.get(insumo.id, Decimal('0'))
        diferencia = r - t
        # Sin teórico no hay base para el %: si igual se movió algo (una merma, o lo que faltó o sobró en el
        # conteo), se resalta
        porcentaje = (diferencia * 100 / t).quantize(Decimal('0.1')) if t else None
        resaltar = abs(porcentaje) > UMBRAL_DESVIACION if porcentaje is not None else r != 0
        filas.append({'id': insumo.id, 'insumo': insumo.nombre, 'unidad': insumo.unidad_medida,
                      'teorico': str(t.quantize(TRES)), 'real': str(r.quantize(TRES)),
                      'diferencia': str(diferencia.quantize(TRES)),
                      'porcentaje': str(porcentaje) if porcentaje is not None else None, 'resaltar': resaltar})
    # Primero lo que más se desvía; lo que no tiene teórico va arriba de todo
    filas.sort(key=lambda f: (f['porcentaje'] is not None, -abs(Decimal(f['porcentaje'] or 0)), f['insumo']))
    return filas


class ConsumoTeoricoRealView(APIView):
    """GET /api/catalogo/reportes/consumo/?desde=&hasta=   Solo ADMINISTRADOR."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        desde, hasta = periodo(request)
        return Response({'desde': desde, 'hasta': hasta, 'umbral': str(UMBRAL_DESVIACION),
                         'filas': teorico_vs_real(request.user.restaurante_id, desde, hasta)})
