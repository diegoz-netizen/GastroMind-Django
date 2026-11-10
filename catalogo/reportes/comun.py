"""Lo que usan todos los reportes: el periodo pedido, su rango en el tiempo, las ventas y el costo de lo que salió."""
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from catalogo.models import MovimientoInventario, Pedido, PedidoDetalle

CERO = Decimal('0')
DINERO = DecimalField(max_digits=14, decimal_places=2)


def _fecha(request, nombre, defecto):
    texto = request.query_params.get(nombre)
    if not texto:
        return defecto
    try:
        fecha = parse_date(texto)
    except ValueError:
        fecha = None
    if fecha is None:
        raise ValidationError({nombre: ['Fecha no válida. Use AAAA-MM-DD.']})
    return fecha


def periodo(request):
    """?desde= y ?hasta= (AAAA-MM-DD, días de Perú, los dos incluidos). Sin ellos, del 1 del mes en curso a hoy."""
    hoy = timezone.localdate()
    desde = _fecha(request, 'desde', hoy.replace(day=1))
    hasta = _fecha(request, 'hasta', hoy)
    if desde > hasta:
        raise ValidationError({'desde': ['La fecha inicial no puede ser mayor que la final.']})
    return desde, hasta


def rango(desde, hasta):
    """Del inicio de `desde` al inicio del día siguiente a `hasta`, en hora de Perú (TIME_ZONE)."""
    return (timezone.make_aware(datetime.combine(desde, time.min)),
            timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min)))


def pedidos_entre(restaurante_id, desde, hasta):
    inicio, fin = rango(desde, hasta)
    return Pedido.objects.filter(mesa__restaurante_id=restaurante_id,
                                 fecha_registro__gte=inicio, fecha_registro__lt=fin)


def ventas_entre(restaurante_id, desde, hasta):
    """Soles vendidos: platillos SERVIDOS × precio de la carta, de los pedidos del periodo."""
    pedidos = pedidos_entre(restaurante_id, desde, hasta).values('id')
    return soles(PedidoDetalle.objects.filter(pedido_id__in=pedidos, estado='SERVIDO')
                 .aggregate(total=Coalesce(Sum(F('cantidad') * F('producto__precio'), output_field=DINERO), CERO,
                                           output_field=DINERO))['total'])


def salidas_entre(restaurante_id, desde, hasta):
    """
    Costo en soles de lo que salió del almacén en el periodo: {'CONSUMO': ..., 'MERMA': ...}, en positivo.
    Se valora al costo_unitario actual del insumo, que solo cambia al registrarlo (las compras no lo tocan).
    """
    inicio, fin = rango(desde, hasta)
    costos = {'CONSUMO': soles(CERO), 'MERMA': soles(CERO)}
    filas = (MovimientoInventario.objects
             .filter(ingrediente__restaurante_id=restaurante_id, tipo__in=costos, fecha__gte=inicio, fecha__lt=fin)
             .values('tipo')
             .annotate(costo=Sum(-F('cantidad') * F('ingrediente__costo_unitario'), output_field=DINERO)))
    for fila in filas:
        costos[fila['tipo']] = soles(fila['costo'])
    return costos


def soles(valor):
    """A céntimos, redondeando una sola vez al final (como el costo del platillo de la HU-08)."""
    return (valor or CERO).quantize(Decimal('0.01'), ROUND_HALF_UP)
