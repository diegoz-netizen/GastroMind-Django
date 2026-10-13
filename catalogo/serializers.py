from decimal import Decimal

from rest_framework import serializers

from .models import Ingrediente

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
