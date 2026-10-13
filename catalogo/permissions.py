from rest_framework.permissions import SAFE_METHODS, BasePermission


class EsAdminOAlmaceneroParaEscribir(BasePermission):
    """
    Leer: cualquier empleado autenticado de su restaurante.
    Escribir (HU-05, "encargado de almacén"): solo ADMINISTRADOR o ALMACENERO; el resto recibe 403.
    """

    ROLES_ESCRITURA = {'ADMINISTRADOR', 'ALMACENERO'}
    message = 'Se requiere rol ADMINISTRADOR o ALMACENERO.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.rol.upper() in self.ROLES_ESCRITURA
