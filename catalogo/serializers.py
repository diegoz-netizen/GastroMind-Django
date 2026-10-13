from rest_framework import serializers
from .models import Categoria, Producto, RecetaDetalle, Ingrediente


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class RecetaDetalleReadSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.ReadOnlyField(source='ingrediente.nombre')
    costo_unitario = serializers.ReadOnlyField(source='ingrediente.costo_unitario')

    class Meta:
        model = RecetaDetalle
        fields = ['id', 'ingrediente', 'ingrediente_nombre', 'cantidad', 'unidad_medida', 'costo_unitario']


class RecetaDetalleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecetaDetalle
        fields = ['ingrediente', 'cantidad', 'unidad_medida']


class ProductoRecetaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    detalles_receta = RecetaDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio', 'categoria', 'categoria_nombre', 'activo', 'detalles_receta']


class GuardarRecetaSerializer(serializers.Serializer):
    detalles = RecetaDetalleWriteSerializer(many=True)

    def create(self, validated_data):
        producto = self.context['producto']
        # Limpiar detalles anteriores para reescribir la receta
        RecetaDetalle.objects.filter(producto=producto).delete()
        
        detalles_creados = []
        for item in validated_data['detalles']:
            detalle = RecetaDetalle.objects.create(producto=producto, **item)
            detalles_creados.append(detalle)
        return detalles_creados