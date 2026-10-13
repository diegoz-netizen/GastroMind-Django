from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from .models import Categoria, Producto, RecetaDetalle, Ingrediente

UNIDADES_VALIDAS = {'kg', 'g', 'l', 'ml', 'unidades', 'unidad', 'paquete', 'lata', 'botella', 'caja', 'bolsa'}


# --- HU-05: Insumos / Ingredientes ---
class IngredienteSerializer(serializers.ModelSerializer):
    bajo_stock_minimo = serializers.BooleanField(read_only=True)
    stock_minimo = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True, 
        allow_null=False
    )
    costo_unitario = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True, 
        allow_null=False
    )

    class Meta:
        model = Ingrediente
        fields = [
            'id', 'nombre', 'unidad_medida', 'stock_actual', 
            'stock_minimo', 'costo_unitario', 'tipo_control', 
            'dotacion_cantidad', 'dotacion_periodo', 'bajo_stock_minimo'
        ]

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del insumo es obligatorio.")
        return value.strip()

    def validate_unidad_medida(self, value):
        if not value:
            raise serializers.ValidationError("La unidad de medida es obligatoria.")
        val_clean = value.strip().lower()
        if val_clean not in UNIDADES_VALIDAS:
            raise serializers.ValidationError(f"Unidad de medida '{value}' no válida.")
        return val_clean

    def validate_costo_unitario(self, value):
        if value is None:
            raise serializers.ValidationError("El costo unitario es obligatorio.")
        if value <= Decimal('0'):
            raise serializers.ValidationError("El costo unitario debe ser mayor a cero.")
        return value

    def validate_stock_minimo(self, value):
        if value is None:
            raise serializers.ValidationError("El stock mínimo es obligatorio.")
        if value <= Decimal('0'):
            raise serializers.ValidationError("El stock mínimo debe ser mayor a cero.")
        return value

    def validate_stock_actual(self, value):
        if value is not None and value < Decimal('0'):
            raise serializers.ValidationError("El stock actual no puede ser negativo.")
        return value

    def validate(self, attrs):
        tipo_control = attrs.get('tipo_control', 'RECETA')
        dotacion_cantidad = attrs.get('dotacion_cantidad')
        dotacion_periodo = attrs.get('dotacion_periodo')

        if tipo_control == 'LIBRE':
            errors = {}
            if dotacion_cantidad is None or dotacion_cantidad <= Decimal('0'):
                errors['dotacion_cantidad'] = 'Para control libre, la dotación es obligatoria y debe ser mayor a cero.'
            if not dotacion_periodo:
                errors['dotacion_periodo'] = 'Para control libre, el periodo de dotación es obligatorio.'
            if errors:
                raise serializers.ValidationError(errors)
        elif tipo_control == 'RECETA':
            attrs['dotacion_cantidad'] = None
            attrs['dotacion_periodo'] = None

        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'restaurante_id'):
            restaurante_id = request.user.restaurante_id
            nombre = attrs.get('nombre')
            if nombre:
                qs = Ingrediente.objects.filter(
                    restaurante_id=restaurante_id, 
                    nombre__iexact=nombre
                )
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError({
                        'nombre': 'Ya existe un insumo con este nombre en tu restaurante.'
                    })

        return attrs


# --- HU-06: Categorías y Productos con Receta ---
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']


class RecetaDetalleReadSerializer(serializers.ModelSerializer):
    ingrediente_id = serializers.ReadOnlyField(source='ingrediente.id')
    ingrediente_nombre = serializers.ReadOnlyField(source='ingrediente.nombre')
    unidad_medida = serializers.ReadOnlyField(source='ingrediente.unidad_medida')
    costo_unitario = serializers.ReadOnlyField(source='ingrediente.costo_unitario')

    class Meta:
        model = RecetaDetalle
        fields = ['id', 'ingrediente_id', 'ingrediente_nombre', 'cantidad_requerida', 'unidad_medida', 'costo_unitario']


class RecetaDetalleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecetaDetalle
        fields = ['ingrediente', 'cantidad_requerida']

    def validate_cantidad_requerida(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("La cantidad requerida debe ser mayor a cero.")
        return value


class ProductoRecetaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    detalles_receta = RecetaDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio', 'categoria', 'categoria_nombre', 'requiere_receta', 'estado', 'detalles_receta']


class GuardarRecetaSerializer(serializers.Serializer):
    detalles = RecetaDetalleWriteSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("La receta debe tener al menos un insumo.")

        ingredientes_ids = [item['ingrediente'].id for item in value]
        if len(ingredientes_ids) != len(set(ingredientes_ids)):
            raise serializers.ValidationError("No se pueden repetir insumos en la misma receta.")

        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'restaurante_id'):
            restaurante_id = request.user.restaurante_id
            for item in value:
                ingrediente = item['ingrediente']
                if ingrediente.restaurante_id != restaurante_id:
                    raise serializers.ValidationError(
                        f"El insumo '{ingrediente.nombre}' no pertenece a tu restaurante."
                    )

        return value

    def create(self, validated_data):
        producto = self.context['producto']
        
        with transaction.atomic():
            RecetaDetalle.objects.filter(producto=producto).delete()
            
            detalles_creados = []
            for item in validated_data['detalles']:
                detalle = RecetaDetalle.objects.create(
                    producto=producto,
                    ingrediente=item['ingrediente'],
                    cantidad_requerida=item['cantidad_requerida']
                )
                detalles_creados.append(detalle)
            
            return detalles_creados