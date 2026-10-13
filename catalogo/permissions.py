from rest_framework import permissions


class EsAlmaceneroOAdministrador(permissions.BasePermission):
    """
    Permite lectura (GET) a cualquier usuario autenticado del restaurante.
    Solo permite crear (POST) a usuarios con rol ALMACENERO o ADMINISTRADOR.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        rol = getattr(request.user, 'rol_nombre', None) or getattr(request.user, 'rol', None)
        if hasattr(rol, 'nombre'):
            rol_str = rol.nombre.upper()
        else:
            rol_str = str(rol).upper() if rol else ''

        return 'ALMACENERO' in rol_str or 'ADMIN' in rol_str