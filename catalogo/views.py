from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Ingrediente, Categoria, Producto, RecetaDetalle
from .permissions import EsAlmaceneroOAdministrador
from .serializers import (
    IngredienteSerializer, 
    CategoriaSerializer, 
    ProductoRecetaSerializer, 
    GuardarRecetaSerializer
)


class IngredienteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EsAlmaceneroOAdministrador]
    serializer_class = IngredienteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        return Ingrediente.objects.filter(restaurante_id=restaurante_id)

    def perform_create(self, serializer):
        serializer.save(restaurante_id=self.request.user.restaurante_id)


class CategoriaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        restaurante_id = self.request.user.restaurante_id
        return Categoria.objects.filter(restaurante_id=restaurante_id)


class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
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