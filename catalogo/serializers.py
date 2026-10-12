from rest_framework import serializers

from .models import Ingrediente


class IngredienteSerializer(serializers.ModelSerializer):
    """HU-05 (lectura). El restaurante no se expone ni se acepta del cliente: sale del token."""

    bajo_stock_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ingrediente
        fields = ['id', 'nombre', 'unidad_medida', 'stock_actual', 'stock_minimo', 'costo_unitario',
                  'tipo_control', 'bajo_stock_minimo']
