"""
HL-014: formato común de errores, igual que GlobalExceptionHandler de Spring Boot.

    {"error": "VALIDACION", "mensaje": "Hay campos con errores.", "campos": {"nombre": "Ya existe..."}}

- error:   código estable que sale del status HTTP (mismos códigos que CodigoError.java de Spring).
- mensaje: texto para mostrar al usuario.
- campos:  solo en errores de validación, un mensaje por campo.

Se activa en settings.REST_FRAMEWORK['EXCEPTION_HANDLER'].
"""

import logging

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

log = logging.getLogger(__name__)

CODIGOS = {
    400: 'SOLICITUD_INVALIDA',
    401: 'NO_AUTENTICADO',
    403: 'SIN_PERMISO',
    404: 'NO_ENCONTRADO',
    405: 'METODO_NO_PERMITIDO',
    409: 'CONFLICTO',
}

MENSAJES = {
    401: 'Tu sesión no es válida o expiró. Vuelve a iniciar sesión.',
    403: 'No tienes permiso para esta acción.',
    404: 'No se encontró el recurso.',
}


def _texto(valor):
    """DRF da listas, dicts o ErrorDetail; se aplana a un solo texto."""
    if isinstance(valor, (list, tuple)):
        return ' '.join(_texto(v) for v in valor)
    if isinstance(valor, dict):
        return ' '.join(_texto(v) for v in valor.values())
    return str(valor)


def manejador_errores(exc, context):
    respuesta = exception_handler(exc, context)

    if respuesta is None:
        # Error no controlado: se registra en el log y el cliente solo ve un mensaje genérico
        log.exception('Error no controlado', exc_info=exc)
        return Response({'error': 'ERROR_INTERNO', 'mensaje': 'Ocurrió un error inesperado. Intenta de nuevo.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    datos = respuesta.data
    if isinstance(exc, ValidationError):
        cuerpo = {'error': 'VALIDACION', 'mensaje': 'Hay campos con errores.'}
        if isinstance(datos, dict):
            generales = datos.pop('non_field_errors', None)
            if generales:
                cuerpo['mensaje'] = _texto(generales)
            if datos:
                cuerpo['campos'] = {campo: _texto(msg) for campo, msg in datos.items()}
        else:
            cuerpo['mensaje'] = _texto(datos)
    else:
        codigo = respuesta.status_code
        detalle = datos.get('detail') if isinstance(datos, dict) else datos
        if isinstance(exc, NotAuthenticated):
            detalle = None  # sin token: mismo mensaje que Spring; token vencido o inactivo conservan el suyo
        cuerpo = {
            'error': CODIGOS.get(codigo, 'ERROR_INTERNO' if codigo >= 500 else 'SOLICITUD_INVALIDA'),
            # El 404 de DRF es genérico ("No encontrado."): se usa un texto propio
            'mensaje': MENSAJES.get(codigo, 'Error') if codigo == 404 or not detalle else _texto(detalle),
        }

    respuesta.data = cuerpo
    return respuesta  # conserva el status y cabeceras como WWW-Authenticate
