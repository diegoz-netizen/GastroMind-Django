from rest_framework import filters, viewsets

from .models import Ingrediente
from .serializers import IngredienteSerializer


class IngredienteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/catalogo/insumos/        lista los insumos del restaurante del token (?search=, ?ordering=)
    GET /api/catalogo/insumos/{id}/   un insumo de otro restaurante responde 404 (no se revela que existe)

    Solo lectura por ahora: el alta (POST, CA-05) se agrega cuando el equipo confirme que el
    catálogo va en Django (agenda de la Planning 2).
    """

    serializer_class = IngredienteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'stock_actual', 'costo_unitario']

    def get_queryset(self):
        # Multi-tenant: SIEMPRE filtrado por el restaurante del empleado autenticado
        return Ingrediente.objects.filter(restaurante_id=self.request.user.restaurante_id)
