from django.db import IntegrityError, transaction
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Categoria, Ingrediente, Producto
from .permissions import EsAdminOAlmaceneroParaEscribir, EsAdminParaEscribir
from .serializers import CategoriaSerializer, GuardarRecetaSerializer, IngredienteSerializer, ProductoRecetaSerializer


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


class CategoriaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EsAdminParaEscribir]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        return Categoria.objects.filter(restaurante_id=restaurante_id)

    def perform_create(self, serializer):
        # El restaurante sale del token (de la BD), nunca del body
        serializer.save(restaurante_id=self.request.user.restaurante_id)


class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EsAdminParaEscribir]
    serializer_class = ProductoRecetaSerializer

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        return Producto.objects.filter(categoria__restaurante_id=restaurante_id)

    @action(detail=True, methods=['post', 'get'], url_path='receta')
    def receta(self, request, pk=None):
        producto = self.get_object()

        if request.method == 'GET':
            serializer = ProductoRecetaSerializer(producto)
            return Response(serializer.data)

        if request.method == 'POST':
            serializer = GuardarRecetaSerializer(
                data=request.data, 
                context={'producto': producto, 'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                res_serializer = ProductoRecetaSerializer(producto)
                return Response(res_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
