from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Empleado, Ingrediente, Restaurante, Rol

URL = '/api/catalogo/insumos/'


def token_como_spring(empleado, clave=None, expira_en=timedelta(hours=24), **extra):
    """Mismo formato que JwtTokenProvider.generarToken() del repo GastroMind (HS256)."""
    ahora = datetime.now(timezone.utc)
    claims = {
        'sub': empleado.correo,
        'usuario_id': empleado.id,
        'rol_id': empleado.rol_id,
        'restaurante_id': empleado.restaurante_id,
        'iat': ahora,
        'exp': ahora + expira_en,
        **extra,
    }
    return jwt.encode(claims, clave or settings.JWT_SECRET, algorithm='HS256')


class BaseCatalogoTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.central = Restaurante.objects.create(nombre='Sede Central')
        cls.norte = Restaurante.objects.create(nombre='Sede Norte')
        admin = Rol.objects.create(nombre='ADMINISTRADOR')
        mozo = Rol.objects.create(nombre='MOZO')

        def empleado(restaurante, rol, correo, estado='ACTIVO'):
            return Empleado.objects.create(restaurante=restaurante, rol=rol, nombre_completo=correo,
                                           correo=correo, password_hash='hash', estado=estado,
                                           fecha_registro=datetime.now(timezone.utc))

        cls.admin_central = empleado(cls.central, admin, 'admin.central@test.com')
        cls.admin_norte = empleado(cls.norte, admin, 'admin.norte@test.com')
        cls.mozo_inactivo = empleado(cls.central, mozo, 'mozo@test.com', estado='INACTIVO')

        def insumo(restaurante, nombre, stock, minimo):
            return Ingrediente.objects.create(restaurante=restaurante, nombre=nombre, unidad_medida='kg',
                                              stock_actual=Decimal(stock), stock_minimo=Decimal(minimo),
                                              costo_unitario=Decimal('10.00'))

        cls.tomate = insumo(cls.central, 'Tomate', '2', '5')
        cls.arroz = insumo(cls.central, 'Arroz', '20', '5')
        cls.pollo_norte = insumo(cls.norte, 'Pollo', '10', '3')

    def setUp(self):
        self.client = APIClient()

    def con_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


class AutenticacionJWTTest(BaseCatalogoTest):
    """El mismo JWT que emite Spring sirve en Django; los mismos casos dan 401."""

    def test_sin_token_responde_401(self):
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta['WWW-Authenticate'], 'Bearer')

    def test_token_valido_de_empleado_activo_responde_200(self):
        self.con_token(token_como_spring(self.admin_central))
        self.assertEqual(self.client.get(URL).status_code, 200)

    def test_token_firmado_con_otra_clave_responde_401(self):
        self.con_token(token_como_spring(self.admin_central, clave='otra-clave-que-no-es-la-de-spring-123456'))
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_token_expirado_responde_401(self):
        self.con_token(token_como_spring(self.admin_central, expira_en=timedelta(seconds=-1)))
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_empleado_inactivo_con_token_valido_responde_401(self):
        self.con_token(token_como_spring(self.mozo_inactivo))
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_empleado_que_no_existe_responde_401(self):
        fantasma = Empleado(id=999_999, restaurante=self.central, rol_id=self.admin_central.rol_id,
                            correo='fantasma@test.com')
        self.con_token(token_como_spring(fantasma))
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_token_sin_usuario_id_responde_401(self):
        token = jwt.encode({'sub': 'x', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
                           settings.JWT_SECRET, algorithm='HS256')
        self.con_token(token)
        self.assertEqual(self.client.get(URL).status_code, 401)


class InsumosMultiTenantTest(BaseCatalogoTest):
    """HU-05: cada restaurante ve solo sus insumos."""

    def test_lista_solo_los_insumos_del_restaurante_ordenados_por_nombre(self):
        self.con_token(token_como_spring(self.admin_central))
        datos = self.client.get(URL).json()
        self.assertEqual([i['nombre'] for i in datos], ['Arroz', 'Tomate'])
        self.assertNotIn('restaurante', datos[0])

    def test_marca_los_insumos_bajo_stock_minimo(self):
        self.con_token(token_como_spring(self.admin_central))
        datos = {i['nombre']: i['bajo_stock_minimo'] for i in self.client.get(URL).json()}
        self.assertEqual(datos, {'Arroz': False, 'Tomate': True})

    def test_insumo_de_otro_restaurante_responde_404(self):
        self.con_token(token_como_spring(self.admin_central))
        self.assertEqual(self.client.get(f'{URL}{self.pollo_norte.id}/').status_code, 404)
        self.assertEqual(self.client.get(f'{URL}{self.tomate.id}/').status_code, 200)

    def test_el_restaurante_sale_de_la_bd_y_no_del_claim(self):
        # Aunque el token dijera otro restaurante, manda el restaurante del empleado en la BD
        self.con_token(token_como_spring(self.admin_central, restaurante_id=self.norte.id))
        self.assertEqual([i['nombre'] for i in self.client.get(URL).json()], ['Arroz', 'Tomate'])

    def test_busqueda_por_nombre(self):
        self.con_token(token_como_spring(self.admin_central))
        self.assertEqual([i['nombre'] for i in self.client.get(URL, {'search': 'tom'}).json()], ['Tomate'])

    def test_por_ahora_es_solo_lectura(self):
        self.con_token(token_como_spring(self.admin_central))
        respuesta = self.client.post(URL, {'nombre': 'Sal', 'unidad_medida': 'kg', 'costo_unitario': '1'})
        self.assertEqual(respuesta.status_code, 405)
