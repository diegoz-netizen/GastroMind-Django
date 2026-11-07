"""
HU-21 (CA-21): sugerencia de compra por insumo, con el historial de consumo y la temporada.
Es un pronóstico estadístico que se puede explicar en la Review; no llama a ningún servicio externo.

- Historial: lo que salió por CONSUMO (platillos servidos, HU-13) en las últimas ?semanas= (8), hasta ayer.
- Tendencia: las 2 semanas más recientes pesan 60 % y el historial completo 40 %, para que una semana rara no
  dispare la compra.
- Temporada: si hay datos del año pasado, se compara lo que se consumió en los mismos días que se van a cubrir con
  las semanas anteriores a esa fecha. Si en esos días el consumo subió un 30 %, se pide un 30 % más. El factor va
  de 0.5 a 2; sin datos del año pasado es 1.
- Comprar = consumo previsto para los próximos ?dias= (7) + stock mínimo − stock actual, redondeado hacia arriba.
- A quién: el proveedor de menor costo total para esa cantidad (HU-22, opciones_de).
Solo insumos RECETA: los LIBRE van por dotación y conteo (HU-25). La cantidad se puede ajustar en la web, que
vuelve a preguntar el mejor proveedor con /reportes/proveedores/?insumo=&cantidad=.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import ROUND_CEILING, Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Ingrediente, MovimientoInventario
from ..permissions import EsAdmin
from .comun import rango
from .proveedores import opciones_de

DIAS_POR_DEFECTO = 7
SEMANAS_POR_DEFECTO = 8
SEMANAS_RECIENTES = 2
PESO_RECIENTE = Decimal('0.6')
FACTOR_MINIMO, FACTOR_MAXIMO = Decimal('0.5'), Decimal('2')
UNO = Decimal('1')
TRES = Decimal('0.001')


def _entero(request, nombre, defecto, minimo, maximo):
    texto = request.query_params.get(nombre)
    if not texto:
        return defecto
    if not texto.isdigit() or not minimo <= int(texto) <= maximo:
        raise ValidationError({nombre: [f'Debe ser un número entero de {minimo} a {maximo}.']})
    return int(texto)


def consumo_por_insumo(restaurante_id, desde, hasta):
    """Lo que salió por CONSUMO de cada insumo RECETA entre esas fechas (incluidas), en positivo."""
    inicio, fin = rango(desde, hasta)
    filas = (MovimientoInventario.objects
             .filter(ingrediente__restaurante_id=restaurante_id, ingrediente__tipo_control='RECETA',
                     tipo='CONSUMO', fecha__gte=inicio, fecha__lt=fin)
             .values('ingrediente_id').annotate(total=Sum('cantidad')))
    return defaultdict(Decimal, {f['ingrediente_id']: -f['total'] for f in filas})


def un_anio_antes(fecha):
    """La misma fecha del año pasado (el 29/2 pasa al 28/2)."""
    try:
        return fecha.replace(year=fecha.year - 1)
    except ValueError:
        return fecha.replace(year=fecha.year - 1, day=28)


def factor_de_temporada(base_anterior, mismos_dias_anterior, dias_base, dias):
    """Cuánto cambió el consumo diario en los mismos días del año pasado frente a las semanas previas."""
    if not base_anterior or not mismos_dias_anterior:
        return UNO
    factor = (mismos_dias_anterior / dias) / (base_anterior / dias_base)
    return min(max(factor, FACTOR_MINIMO), FACTOR_MAXIMO).quantize(Decimal('0.01'))


def sugerencia(restaurante_id, hoy, dias, semanas):
    hasta = hoy - timedelta(days=1)
    desde = hasta - timedelta(weeks=semanas) + timedelta(days=1)
    reciente_desde = hasta - timedelta(weeks=SEMANAS_RECIENTES) + timedelta(days=1)
    historial = consumo_por_insumo(restaurante_id, desde, hasta)
    reciente = consumo_por_insumo(restaurante_id, max(reciente_desde, desde), hasta)

    # Temporada: el mismo tramo hace un año
    hace_un_anio = un_anio_antes(hoy)
    base_anterior = consumo_por_insumo(restaurante_id, un_anio_antes(desde), hace_un_anio - timedelta(days=1))
    mismos_dias_anterior = consumo_por_insumo(restaurante_id, hace_un_anio, hace_un_anio + timedelta(days=dias - 1))

    dias_historial = Decimal(semanas * 7)
    dias_recientes = Decimal(min(SEMANAS_RECIENTES, semanas) * 7)
    filas = []
    for insumo in Ingrediente.objects.filter(restaurante_id=restaurante_id, tipo_control='RECETA'):
        diario = historial[insumo.id] / dias_historial
        tendencia = reciente[insumo.id] / dias_recientes
        temporada = factor_de_temporada(base_anterior[insumo.id], mismos_dias_anterior[insumo.id], dias_historial,
                                        Decimal(dias))
        previsto = ((PESO_RECIENTE * tendencia + (UNO - PESO_RECIENTE) * diario) * dias * temporada).quantize(TRES)
        faltan = previsto + insumo.stock_minimo - insumo.stock_actual
        comprar = max(faltan, Decimal('0')).quantize(UNO, ROUND_CEILING)

        opciones = opciones_de(restaurante_id, insumo.id, comprar) if comprar else []
        mejor = opciones[0] if opciones else None
        filas.append({
            'id': insumo.id, 'insumo': insumo.nombre, 'unidad': insumo.unidad_medida,
            'stock': str(insumo.stock_actual.quantize(TRES)), 'minimo': str(insumo.stock_minimo.quantize(TRES)),
            'consumo_diario': str(diario.quantize(TRES)), 'tendencia_diaria': str(tendencia.quantize(TRES)),
            'factor_temporada': str(temporada), 'previsto': str(previsto), 'comprar': str(comprar),
            'proveedor': {**mejor, 'precio_unitario': str(mejor['precio_unitario']), 'flete': str(mejor['flete']),
                          'costo_total': str(mejor['costo_total'])} if mejor else None,
        })
    # Primero lo que hay que comprar, de más a menos; luego el resto por nombre
    filas.sort(key=lambda f: (-Decimal(f['comprar']), f['insumo']))
    return {'desde': desde, 'hasta': hasta, 'dias': dias, 'semanas': semanas, 'filas': filas}


class SugerenciaCompraView(APIView):
    """GET /api/catalogo/reportes/sugerencia/?dias=7&semanas=8   Solo ADMINISTRADOR."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        dias = _entero(request, 'dias', DIAS_POR_DEFECTO, 1, 60)
        semanas = _entero(request, 'semanas', SEMANAS_POR_DEFECTO, 1, 52)
        return Response(sugerencia(request.user.restaurante_id, timezone.localdate(), dias, semanas))
