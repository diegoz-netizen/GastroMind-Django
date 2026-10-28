from django.db import IntegrityError, transaction
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Categoria, Ingrediente, Producto
from .permissions import EsAdminOAlmaceneroParaEscribir, EsAdminParaEscribir
from .serializers import (CategoriaSerializer, EstadoProductoSerializer, GuardarRecetaSerializer, IngredienteSerializer,
                          ProductoRecetaSerializer)


class Conflicto(APIException):
    """409 CONFLICTO (HL-014): la acción choca con datos que dependen del recurso."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'El recurso tiene datos que dependen de él.'
    default_code = 'conflicto'


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
    """
    DELETE /api/catalogo/categorias/{id}/   solo si no tiene platillos (409): borrarla se llevaría
    sus platillos y recetas (CA-07: un platillo se desactiva, nunca se borra).
    """

    permission_classes = [IsAuthenticated, EsAdminParaEscribir]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        return Categoria.objects.filter(restaurante_id=restaurante_id)

    def perform_create(self, serializer):
        # El restaurante sale del token (de la BD), nunca del body
        serializer.save(restaurante_id=self.request.user.restaurante_id)

    def perform_destroy(self, instance):
        if instance.productos.exists():
            raise Conflicto('La categoría tiene platillos: muévelos a otra categoría o desactívalos antes de borrarla.')
        instance.delete()


class ProductoViewSet(viewsets.ModelViewSet):
    """
    HU-07 Gestionar la carta (escribe solo el ADMINISTRADOR):
    GET   /api/catalogo/productos/               platillos del restaurante del token (?estado=ACTIVO para la toma de pedidos)
    POST  /api/catalogo/productos/               crea un platillo (nace ACTIVO)
    PUT/PATCH /api/catalogo/productos/{id}/      edita nombre, precio, categoría o requiere_receta
    PATCH /api/catalogo/productos/{id}/estado/   activa o desactiva (CA-07)
    DELETE no existe (405): un platillo desactivado se conserva en el historial de ventas.
    HU-08: cada platillo trae costo, margen y porcentaje_costo, calculados con su receta (CA-08).
    Solo los ve el ADMINISTRADOR, y salen en null si el platillo no lleva receta o aún no la tiene (Review 2).
    """

    permission_classes = [IsAuthenticated, EsAdminParaEscribir]
    serializer_class = ProductoRecetaSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        # La receta con sus insumos se trae en una sola consulta: el costo (HU-08) se calcula con ella
        productos = (Producto.objects.filter(categoria__restaurante_id=restaurante_id)
                     .select_related('categoria').prefetch_related('detalles_receta__ingrediente')
                     .order_by('categoria__nombre', 'nombre'))
        estado = self.request.query_params.get('estado')
        if estado is not None and self.action == 'list':
            if estado not in Producto.ESTADOS:
                raise ValidationError({'estado': [f'Debe ser {" o ".join(Producto.ESTADOS)}.']})
            productos = productos.filter(estado=estado)
        return productos

    @action(detail=True, methods=['patch'], url_path='estado')
    def estado(self, request, pk=None):
        producto = self.get_object()
        serializer = EstadoProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto.estado = serializer.validated_data['estado']
        producto.save(update_fields=['estado'])
        return Response(self.get_serializer(producto).data)

    @action(detail=True, methods=['post', 'get'], url_path='receta')
    def receta(self, request, pk=None):
        producto = self.get_object()

        if request.method == 'GET':
            serializer = self.get_serializer(producto)
            return Response(serializer.data)

        if request.method == 'POST':
            serializer = GuardarRecetaSerializer(
                data=request.data, 
                context={'producto': producto, 'request': request}
            )
            # HL-014: los errores pasan por config/errores.py como el resto de la API
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # Se vuelve a leer: el producto trae la receta anterior ya cargada (prefetch) y el costo saldría viejo
            producto = self.get_queryset().get(pk=producto.pk)
            res_serializer = self.get_serializer(producto)
            return Response(res_serializer.data, status=status.HTTP_200_OK)
