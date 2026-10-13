from django.db import IntegrityError, transaction
from rest_framework import filters, mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Ingrediente
from .permissions import EsAdminOAlmaceneroParaEscribir
from .serializers import IngredienteSerializer


class IngredienteViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/catalogo/insumos/        lista los insumos del restaurante del token (?search=, ?ordering=)
    GET  /api/catalogo/insumos/{id}/   un insumo de otro restaurante responde 404 (no se revela que existe)
    POST /api/catalogo/insumos/        HU-05: registra un insumo (CA-05). Solo ADMINISTRADOR o ALMACENERO.
    """

    serializer_class = IngredienteSerializer
    permission_classes = [IsAuthenticated, EsAdminOAlmaceneroParaEscribir]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'stock_actual', 'costo_unitario']

    def get_queryset(self):
        # Multi-tenant: SIEMPRE filtrado por el restaurante del empleado autenticado
        return Ingrediente.objects.filter(restaurante_id=self.request.user.restaurante_id)

    def perform_create(self, serializer):
        try:
            # El restaurante sale del token (de la BD), nunca del body
            with transaction.atomic():
                serializer.save(restaurante_id=self.request.user.restaurante_id)
        except IntegrityError:
            # Dos altas del mismo nombre a la vez: la segunda choca con el UNIQUE de la tabla
            raise ValidationError({'nombre': ['Ya existe un insumo con ese nombre en el restaurante.']})
