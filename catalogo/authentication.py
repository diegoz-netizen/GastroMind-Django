"""
Login único con Spring Boot.

El JWT lo emite Spring (POST /api/auth/login en el repo GastroMind) con HS256 y los claims
usuario_id, rol_id y restaurante_id. Aquí se valida con la MISMA clave y, igual que el
JwtAuthenticationFilter de Spring, se exige que el empleado siga ACTIVO en la BD en cada petición.
"""

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import Empleado


class EmpleadoAutenticado:
    """Lo que queda en request.user: el empleado y su restaurante (se toma de la BD, no del cliente)."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, empleado):
        self.empleado = empleado
        self.id = empleado.id
        self.restaurante_id = empleado.restaurante_id
        self.rol = empleado.rol.nombre

    def __str__(self):
        return self.empleado.correo


class JWTSpringAuthentication(BaseAuthentication):
    keyword = b'bearer'

    def authenticate(self, request):
        partes = get_authorization_header(request).split()
        if not partes or partes[0].lower() != self.keyword:
            return None  # sin token: DRF responde 401 por IsAuthenticated
        if len(partes) != 2:
            raise AuthenticationFailed('Cabecera Authorization inválida.')

        try:
            claims = jwt.decode(partes[1], settings.JWT_SECRET, algorithms=['HS256'],
                                options={'require': ['exp', 'usuario_id', 'restaurante_id']})
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('El token expiró.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido.')

        empleado = (Empleado.objects.select_related('rol')
                    .filter(id=claims['usuario_id']).first())
        if empleado is None or not empleado.esta_activo:
            raise AuthenticationFailed('Su cuenta se encuentra inactiva o no existe.')

        return EmpleadoAutenticado(empleado), claims

    def authenticate_header(self, request):
        # Hace que DRF responda 401 (y no 403) cuando falta o falla el token, igual que Spring
        return 'Bearer'
