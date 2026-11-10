"""
HU-22 (CA-22): ante dos proveedores del mismo insumo, se sugiere el de menor costo total.
Costo total = precio unitario × cantidad + flete. Si empatan, gana el que entrega antes.
La HU-21 (sugerencia de compra) usa opciones_de() para proponer a quién comprarle.
"""
from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogo.models import Ingrediente, ProveedorInsumo
from catalogo.permissions import EsAdmin
from .comun import soles


def opciones_de(restaurante_id, ingrediente_id, cantidad):
    """Lo que cuesta comprar esa cantidad a cada proveedor del insumo, de menor a mayor costo total."""
    precios = (ProveedorInsumo.objects
               .filter(ingrediente_id=ingrediente_id, ingrediente__restaurante_id=restaurante_id,
                       proveedor__restaurante_id=restaurante_id)
               .select_related('proveedor'))
    opciones = [{'proveedor_id': p.proveedor_id, 'proveedor': p.proveedor.nombre,
                 'precio_unitario': p.precio_unitario, 'flete': p.flete, 'tiempo_entrega_dias': p.tiempo_entrega_dias,
                 'costo_total': soles(p.precio_unitario * cantidad + p.flete)} for p in precios]
    opciones.sort(key=lambda o: (o['costo_total'], o['tiempo_entrega_dias'], o['proveedor']))
    return opciones


def _cantidad(texto):
    if not texto:
        return Decimal('1')
    try:
        cantidad = Decimal(texto)
    except InvalidOperation:
        raise ValidationError({'cantidad': ['Debe ser un número.']})
    if not cantidad.is_finite() or cantidad <= 0:
        raise ValidationError({'cantidad': ['Debe ser mayor que 0.']})
    if cantidad.as_tuple().exponent < -3:
        raise ValidationError({'cantidad': ['Admite hasta 3 decimales.']})
    return cantidad


class CompararProveedoresView(APIView):
    """GET /api/catalogo/reportes/proveedores/?insumo=&cantidad=   Solo ADMINISTRADOR. Cantidad por defecto: 1."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        restaurante_id = request.user.restaurante_id
        insumo_id = request.query_params.get('insumo') or ''
        # Un insumo de otro restaurante se trata como inexistente
        insumo = (Ingrediente.objects.filter(id=insumo_id, restaurante_id=restaurante_id).first()
                  if insumo_id.isdigit() else None)
        if insumo is None:
            raise ValidationError({'insumo': ['Insumo no encontrado.']})
        cantidad = _cantidad(request.query_params.get('cantidad'))
        opciones = opciones_de(restaurante_id, insumo.id, cantidad)
        filas = [{**o, 'precio_unitario': str(o['precio_unitario']), 'flete': str(o['flete']),
                  'costo_total': str(o['costo_total']), 'sugerido': i == 0} for i, o in enumerate(opciones)]
        return Response({'insumo_id': insumo.id, 'insumo': insumo.nombre, 'unidad': insumo.unidad_medida,
                         'cantidad': str(cantidad), 'opciones': filas})
