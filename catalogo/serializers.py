from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Categoria, Ingrediente, Producto, RecetaDetalle

# Las de la tabla ingrediente (comentario de unidad_medida en script_database.sql)
UNIDADES = ['g', 'kg', 'ml', 'l', 'unidades']
MAYOR_QUE_CERO = 'Debe ser mayor que 0.'


class IngredienteSerializer(serializers.ModelSerializer):
    """
    HU-05. El restaurante no se expone ni se acepta del cliente: sale del token.

    CA-05: nombre, unidad y costo obligatorios; costo y stock mínimo > 0. La BD acepta 0
    (CHECK >= 0 y DEFAULT 0), pero manda el CA del Excel oficial: se valida aquí, antes de guardar.
    """

    nombre = serializers.CharField(max_length=150, trim_whitespace=True)
    unidad_medida = serializers.ChoiceField(choices=UNIDADES)
    costo_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                                              error_messages={'min_value': MAYOR_QUE_CERO})
    stock_minimo = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                                            error_messages={'min_value': MAYOR_QUE_CERO})
    stock_actual = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'),
                                            required=False, default=Decimal('0'),
                                            error_messages={'min_value': 'No puede ser negativo.'})
    dotacion_cantidad = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                                                 required=False, allow_null=True,
                                                 error_messages={'min_value': MAYOR_QUE_CERO})
    bajo_stock_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ingrediente
        fields = ['id', 'nombre', 'unidad_medida', 'stock_actual', 'stock_minimo', 'costo_unitario',
                  'tipo_control', 'dotacion_cantidad', 'dotacion_periodo', 'bajo_stock_minimo']
        # El UNIQUE (restaurante, nombre) se valida a mano en validate_nombre: el restaurante no viene en el body
        validators = []

    def validate_nombre(self, nombre):
        restaurante_id = self.context['request'].user.restaurante_id
        if Ingrediente.objects.filter(restaurante_id=restaurante_id, nombre__iexact=nombre).exists():
            raise serializers.ValidationError('Ya existe un insumo con ese nombre en el restaurante.')
        return nombre

    def validate(self, datos):
        # Igual que el CHECK chk_dotacion_libre: un insumo LIBRE necesita su dotación; uno de RECETA no la usa
        if datos.get('tipo_control', 'RECETA') == 'LIBRE':
            faltan = {campo: 'Obligatorio si tipo_control es LIBRE.'
                      for campo in ('dotacion_cantidad', 'dotacion_periodo') if not datos.get(campo)}
            if faltan:
                raise serializers.ValidationError(faltan)
        else:
            datos['dotacion_cantidad'] = None
            datos['dotacion_periodo'] = None
        return datos


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

    def get_fields(self):
        # Solo los insumos del restaurante del token: uno de otra sede responde igual que uno inexistente
        fields = super().get_fields()
        request = self.context.get('request')
        if request is not None:
            fields['ingrediente'].queryset = Ingrediente.objects.filter(restaurante_id=request.user.restaurante_id)
        return fields

    def validate_cantidad_requerida(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("La cantidad requerida debe ser mayor a cero.")
        return value


class ProductoRecetaSerializer(serializers.ModelSerializer):
    """
    HU-07: el gerente crea y edita platillos con su precio. El estado no se cambia aquí:
    va por PATCH /productos/{id}/estado/ (CA-07: desactivar, nunca borrar).
    """

    nombre = serializers.CharField(max_length=150, trim_whitespace=True)
    # La BD acepta 0 (CHECK precio >= 0), pero un platillo de la carta se vende: precio > 0
    precio = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                                      error_messages={'min_value': MAYOR_QUE_CERO})
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    detalles_receta = RecetaDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio', 'categoria', 'categoria_nombre', 'requiere_receta', 'estado', 'detalles_receta']
        read_only_fields = ['estado']

    def validate_categoria(self, value):
        # Valida que la categoría seleccionada pertenezca al restaurante del usuario autenticado
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'restaurante_id'):
            if value.restaurante_id != request.user.restaurante_id:
                raise serializers.ValidationError("La categoría seleccionada no pertenece a tu restaurante.")
        return value


class EstadoProductoSerializer(serializers.Serializer):
    """HU-07 / CA-07: un platillo se activa o se desactiva; nunca se borra (queda en el historial de ventas)."""

    estado = serializers.ChoiceField(choices=Producto.ESTADOS)


class GuardarRecetaSerializer(serializers.Serializer):
    detalles = RecetaDetalleWriteSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("La receta debe tener al menos un insumo.")

        ingredientes_ids = [item['ingrediente'].id for item in value]
        if len(ingredientes_ids) != len(set(ingredientes_ids)):
            raise serializers.ValidationError("No se pueden repetir insumos en la misma receta.")

        return value

    def validate(self, attrs):
        if not self.context['producto'].requiere_receta:
            raise serializers.ValidationError("Este platillo no requiere receta.")
        return attrs

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
