from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny  # Importar AllowAny
from rest_framework.response import Response
from .models import Categoria, Producto, RecetaDetalle
from .serializers import (
    CategoriaSerializer,
    ProductoRecetaSerializer,
    GuardarRecetaSerializer,
    RecetaDetalleReadSerializer
)


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]  # Permite acceso sin token en desarrollo


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoRecetaSerializer
    permission_classes = [AllowAny]  # Permite acceso sin token en desarrollo

    def get_queryset(self):
        queryset = super().get_queryset()
        restaurante_id = self.request.query_params.get('restaurante_id')
        if restaurante_id:
            queryset = queryset.filter(restaurante_id=restaurante_id)
        return queryset

    @action(detail=True, methods=['get', 'post'], url_path='receta')
    def gestionar_receta(self, request, pk=None):
        producto = self.get_object()

        if request.method == 'GET':
            detalles = RecetaDetalle.objects.filter(producto=producto)
            serializer = RecetaDetalleReadSerializer(detalles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'POST':
            serializer = GuardarRecetaSerializer(
                data=request.data,
                context={'producto': producto}
            )
            if serializer.is_valid():
                serializer.save()
                detalles_actualizados = RecetaDetalle.objects.filter(producto=producto)
                res_serializer = RecetaDetalleReadSerializer(detalles_actualizados, many=True)
                return Response(res_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)