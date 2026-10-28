"""
Modelos sobre las tablas que YA existen en la BD compartida (docs/script_database.sql).

managed = False: Django lee y escribe DATOS (CRUD), pero nunca crea ni altera estas tablas.
La estructura la controla el script SQL.
"""

from django.db import models


class Restaurante(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'restaurante'

    def __str__(self):
        return self.nombre


class Rol(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    """Solo lectura desde Django: los empleados los gestiona Spring Boot (HU-01, HU-03)."""

    ACTIVO = 'ACTIVO'

    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(
        Restaurante, 
        on_delete=models.PROTECT, 
        db_column='restaurante_id',
        related_name='empleados'
    )
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.PROTECT, 
        db_column='rol_id', 
        related_name='empleados'
    )
    nombre_completo = models.CharField(max_length=150)
    correo = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    pin_acceso = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()
    # HL-035: va en el JWT; Spring la sube al cambiar la contraseña y los tokens anteriores dejan de valer
    version_token = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'empleado'

    def __str__(self):
        return f'{self.nombre_completo} ({self.correo})'

    @property
    def esta_activo(self):
        return self.estado == self.ACTIVO


class Ingrediente(models.Model):
    """HU-05: insumo del almacén. Cada insumo pertenece a UN restaurante (multi-tenant)."""

    TIPO_CONTROL = [('RECETA', 'Receta'), ('LIBRE', 'Libre')]
    DOTACION_PERIODO = [('SEMANAL', 'Semanal'), ('MENSUAL', 'Mensual')]

    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(
        Restaurante, 
        on_delete=models.PROTECT, 
        db_column='restaurante_id',
        related_name='ingredientes'
    )
    nombre = models.CharField(max_length=150)
    unidad_medida = models.CharField(max_length=20)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_control = models.CharField(max_length=20, choices=TIPO_CONTROL, default='RECETA')
    dotacion_cantidad = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dotacion_periodo = models.CharField(max_length=20, choices=DOTACION_PERIODO, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ingrediente'
        unique_together = [('restaurante', 'nombre')]
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.unidad_medida})'

    @property
    def bajo_stock_minimo(self):
        # CA-16: la alerta salta cuando el stock "llega" al mínimo, así que el mínimo exacto ya cuenta
        return self.stock_actual <= self.stock_minimo


class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(
        Restaurante,
        on_delete=models.PROTECT,
        db_column='restaurante_id',
        related_name='categorias'
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'categoria'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """HU-07: platillo de la carta. Se desactiva en vez de borrarse (CA-07)."""

    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    ESTADOS = [ACTIVO, INACTIVO]  # CHECK de la tabla producto

    id = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE, 
        db_column='categoria_id',
        related_name='productos'
    )
    nombre = models.CharField(max_length=150)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    requiere_receta = models.BooleanField(default=True)
    estado = models.CharField(max_length=20, default=ACTIVO)

    class Meta:
        managed = False
        db_table = 'producto'

    def __str__(self):
        return self.nombre


class RecetaDetalle(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='detalles_receta', 
        db_column='producto_id'
    )
    ingrediente = models.ForeignKey(
        Ingrediente, 
        on_delete=models.CASCADE, 
        db_column='ingrediente_id',
        related_name='recetas'
    )
    cantidad_requerida = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        managed = False
        db_table = 'receta_detalle'
        unique_together = [('producto', 'ingrediente')]

    def __str__(self):
        return f"{self.producto.nombre} - {self.ingrediente.nombre} ({self.cantidad_requerida})"


class Proveedor(models.Model):
    """HU-22: proveedor del restaurante. Por ahora solo se lee (HU-16 muestra de quién es cada lote)."""

    id = models.AutoField(primary_key=True)
    restaurante = models.ForeignKey(
        Restaurante,
        on_delete=models.PROTECT,
        db_column='restaurante_id',
        related_name='proveedores'
    )
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'proveedor'

    def __str__(self):
        return self.nombre


class RegistroIngresoProveedor(models.Model):
    """HU-14 registra los ingresos de compras (Spring). HU-16 solo lee el vencimiento de cada lote."""

    id = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, db_column='empleado_id', related_name='+')
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column='proveedor_id',
        related_name='ingresos'
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        db_column='ingrediente_id',
        related_name='ingresos'
    )
    lote = models.CharField(max_length=50, null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)  # NULL = no perecible
    cantidad_recibida = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'registro_ingreso_proveedor'

    def __str__(self):
        return f'{self.ingrediente.nombre} - lote {self.lote or "s/n"}'
