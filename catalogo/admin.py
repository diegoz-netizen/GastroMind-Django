"""
Admin de Django para el staff interno (S05 del curso).

Ojo: el admin NO filtra por restaurante; un superusuario ve los datos de todos.
La gestión de cada restaurante va por la API, filtrada por el JWT.
Los empleados son de solo lectura aquí: se gestionan en Spring Boot (HU-01, HU-03).
"""

from django.contrib import admin

from .models import Empleado, Ingrediente, Restaurante, Rol


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'unidad_medida', 'stock_actual', 'stock_minimo', 'costo_unitario',
                    'tipo_control')
    list_filter = ('restaurante', 'tipo_control')
    search_fields = ('nombre',)
    list_select_related = ('restaurante',)
    # El stock solo lo cambia InventarioService de Spring, que deja el movimiento del kardex (revisión del #15)
    readonly_fields = ('stock_actual',)


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'correo', 'rol', 'restaurante', 'estado')
    list_filter = ('estado', 'rol', 'restaurante')
    search_fields = ('nombre_completo', 'correo')
    list_select_related = ('rol', 'restaurante')
    exclude = ('password_hash', 'pin_acceso')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    # Roles fijos del sistema (script_database.sql): solo lectura
    list_display = ('id', 'nombre')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
