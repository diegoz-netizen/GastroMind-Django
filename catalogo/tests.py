from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

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
        cls.almacenero_central = empleado(cls.central, Rol.objects.create(nombre='ALMACENERO'),
                                          'almacen@test.com')
        cls.cocinero_central = empleado(cls.central, Rol.objects.create(nombre='COCINERO'), 'cocina@test.com')

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

    def test_token_anterior_al_cambio_de_contrasena_responde_401(self):
        # HL-035: Spring sube version_token al restablecer la contraseña
        Empleado.objects.filter(pk=self.admin_central.pk).update(version_token=1)
        self.con_token(token_como_spring(self.admin_central, version_token=0))
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.con_token(token_como_spring(self.admin_central))  # sin el claim = versión 0
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_token_con_la_version_actual_responde_200(self):
        Empleado.objects.filter(pk=self.admin_central.pk).update(version_token=1)
        self.con_token(token_como_spring(self.admin_central, version_token=1))
        self.assertEqual(self.client.get(URL).status_code, 200)

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

    def test_no_se_puede_editar_ni_borrar(self):
        # HU-05 es solo el alta; editar o borrar insumos no entra en este sprint
        self.con_token(token_como_spring(self.admin_central))
        self.assertEqual(self.client.put(f'{URL}{self.tomate.id}/', {}).status_code, 405)
        self.assertEqual(self.client.delete(f'{URL}{self.tomate.id}/').status_code, 405)


class RegistrarInsumoTest(BaseCatalogoTest):
    """HU-05: POST /api/catalogo/insumos/ con las validaciones de CA-05."""

    VALIDO = {'nombre': 'Sal', 'unidad_medida': 'kg', 'costo_unitario': '1.50', 'stock_minimo': '2'}

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def registrar(self, **cambios):
        datos = {**self.VALIDO, **cambios}
        return self.client.post(URL, {k: v for k, v in datos.items() if v is not None}, format='json')

    def assertError400(self, respuesta, campo):
        self.assertEqual(respuesta.status_code, 400, respuesta.content)
        self.assertEqual(respuesta.json()['error'], 'VALIDACION')
        self.assertIn(campo, respuesta.json()['campos'])

    # --- camino feliz ---

    def test_registra_el_insumo_en_el_restaurante_del_token(self):
        respuesta = self.registrar()
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        insumo = Ingrediente.objects.get(id=respuesta.json()['id'])
        self.assertEqual(insumo.restaurante_id, self.central.id)
        self.assertEqual((insumo.nombre, insumo.unidad_medida, insumo.costo_unitario, insumo.stock_minimo),
                         ('Sal', 'kg', Decimal('1.50'), Decimal('2.00')))
        self.assertEqual(insumo.stock_actual, Decimal('0'))
        self.assertEqual(insumo.tipo_control, 'RECETA')
        self.assertTrue(respuesta.json()['bajo_stock_minimo'])

    def test_ignora_el_restaurante_que_mande_el_cliente(self):
        respuesta = self.registrar(restaurante=self.norte.id, restaurante_id=self.norte.id)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Ingrediente.objects.get(id=respuesta.json()['id']).restaurante_id, self.central.id)

    def test_el_nuevo_insumo_aparece_solo_en_su_restaurante(self):
        self.registrar()
        self.assertIn('Sal', [i['nombre'] for i in self.client.get(URL).json()])
        self.con_token(token_como_spring(self.admin_norte))
        self.assertNotIn('Sal', [i['nombre'] for i in self.client.get(URL).json()])

    def test_quita_espacios_del_nombre(self):
        self.assertEqual(self.registrar(nombre='  Sal  ').json()['nombre'], 'Sal')

    # --- CA-05: obligatorios ---

    def test_sin_nombre_responde_400(self):
        self.assertError400(self.registrar(nombre=None), 'nombre')
        self.assertError400(self.registrar(nombre='   '), 'nombre')

    def test_sin_unidad_responde_400(self):
        self.assertError400(self.registrar(unidad_medida=None), 'unidad_medida')

    def test_unidad_no_valida_responde_400(self):
        self.assertError400(self.registrar(unidad_medida='toneladas'), 'unidad_medida')

    def test_sin_costo_responde_400(self):
        self.assertError400(self.registrar(costo_unitario=None), 'costo_unitario')

    def test_sin_stock_minimo_responde_400(self):
        # La BD le pondría 0 por defecto, pero el CA exige > 0
        self.assertError400(self.registrar(stock_minimo=None), 'stock_minimo')

    # --- CA-05: costo y stock mínimo > 0 ---

    def test_costo_cero_o_negativo_responde_400(self):
        for costo in ('0', '-5'):
            with self.subTest(costo=costo):
                self.assertError400(self.registrar(costo_unitario=costo), 'costo_unitario')

    def test_stock_minimo_cero_o_negativo_responde_400(self):
        for minimo in ('0', '-1'):
            with self.subTest(minimo=minimo):
                self.assertError400(self.registrar(stock_minimo=minimo), 'stock_minimo')

    def test_stock_actual_negativo_responde_400(self):
        self.assertError400(self.registrar(stock_actual='-1'), 'stock_actual')

    def test_no_guarda_nada_si_hay_error(self):
        antes = Ingrediente.objects.count()
        self.registrar(costo_unitario='0')
        self.assertEqual(Ingrediente.objects.count(), antes)

    # --- duplicado (restaurante, nombre) ---

    def test_nombre_repetido_en_el_mismo_restaurante_responde_400(self):
        self.assertError400(self.registrar(nombre='Tomate'), 'nombre')
        self.assertError400(self.registrar(nombre='tomate'), 'nombre')

    def test_el_mismo_nombre_en_otro_restaurante_si_se_puede(self):
        # "Pollo" existe en Norte, no en Central
        self.assertEqual(self.registrar(nombre='Pollo').status_code, 201)

    # --- tipo de control (CHECK chk_dotacion_libre) ---

    def test_libre_sin_dotacion_responde_400(self):
        respuesta = self.registrar(tipo_control='LIBRE')
        self.assertError400(respuesta, 'dotacion_cantidad')
        self.assertIn('dotacion_periodo', respuesta.json()['campos'])

    def test_libre_con_dotacion_se_registra(self):
        respuesta = self.registrar(nombre='Detergente', unidad_medida='l', tipo_control='LIBRE',
                                   dotacion_cantidad='5', dotacion_periodo='SEMANAL')
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        self.assertEqual(respuesta.json()['dotacion_periodo'], 'SEMANAL')

    def test_receta_ignora_la_dotacion(self):
        respuesta = self.registrar(dotacion_cantidad='5', dotacion_periodo='SEMANAL')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIsNone(respuesta.json()['dotacion_cantidad'])
        self.assertIsNone(respuesta.json()['dotacion_periodo'])

    # --- roles ---

    def test_almacenero_puede_registrar(self):
        self.con_token(token_como_spring(self.almacenero_central))
        self.assertEqual(self.registrar().status_code, 201)

    def test_cocinero_no_puede_registrar_pero_si_consultar(self):
        self.con_token(token_como_spring(self.cocinero_central))
        self.assertEqual(self.registrar().status_code, 403)
        self.assertEqual(self.client.get(URL).status_code, 200)

    def test_sin_token_responde_401(self):
        self.client.credentials()
        self.assertEqual(self.registrar().status_code, 401)


class FormatoErroresTest(BaseCatalogoTest):
    """HL-014: los errores salen como {error, mensaje, campos?}, con los mismos códigos que Spring."""

    def assertFormato(self, respuesta, status, error):
        self.assertEqual(respuesta.status_code, status, respuesta.content)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo['error'], error)
        self.assertIsInstance(cuerpo['mensaje'], str)
        self.assertNotIn('detail', cuerpo)
        return cuerpo

    def test_sin_token_401_y_conserva_www_authenticate(self):
        respuesta = self.client.get(URL)
        cuerpo = self.assertFormato(respuesta, 401, 'NO_AUTENTICADO')
        self.assertEqual(cuerpo['mensaje'], 'Tu sesión no es válida o expiró. Vuelve a iniciar sesión.')
        self.assertEqual(respuesta['WWW-Authenticate'], 'Bearer')

    def test_token_expirado_401_con_su_mensaje(self):
        self.con_token(token_como_spring(self.admin_central, expira_en=timedelta(seconds=-1)))
        cuerpo = self.assertFormato(self.client.get(URL), 401, 'NO_AUTENTICADO')
        self.assertEqual(cuerpo['mensaje'], 'El token expiró.')

    def test_validacion_400_con_un_texto_por_campo(self):
        self.con_token(token_como_spring(self.admin_central))
        cuerpo = self.assertFormato(self.client.post(URL, {'nombre': 'Tomate', 'costo_unitario': '0'}, format='json'),
                                    400, 'VALIDACION')
        self.assertEqual(cuerpo['campos']['nombre'], 'Ya existe un insumo con ese nombre en el restaurante.')
        self.assertEqual(cuerpo['campos']['costo_unitario'], 'Debe ser mayor que 0.')
        self.assertIn('unidad_medida', cuerpo['campos'])

    def test_json_mal_formado_400(self):
        self.con_token(token_como_spring(self.admin_central))
        respuesta = self.client.post(URL, '{esto no es json', content_type='application/json')
        self.assertFormato(respuesta, 400, 'SOLICITUD_INVALIDA')

    def test_rol_sin_permiso_403(self):
        self.con_token(token_como_spring(self.cocinero_central))
        cuerpo = self.assertFormato(self.client.post(URL, {}, format='json'), 403, 'SIN_PERMISO')
        self.assertEqual(cuerpo['mensaje'], 'Se requiere rol ADMINISTRADOR o ALMACENERO.')

    def test_insumo_de_otro_restaurante_404(self):
        self.con_token(token_como_spring(self.admin_central))
        self.assertFormato(self.client.get(f'{URL}{self.pollo_norte.id}/'), 404, 'NO_ENCONTRADO')

    def test_metodo_no_permitido_405(self):
        self.con_token(token_como_spring(self.admin_central))
        self.assertFormato(self.client.delete(f'{URL}{self.tomate.id}/'), 405, 'METODO_NO_PERMITIDO')

    def test_error_inesperado_500_sin_detalles_internos(self):
        self.con_token(token_como_spring(self.admin_central))
        with mock.patch('catalogo.views.IngredienteViewSet.get_queryset', side_effect=RuntimeError('secreto')), \
                self.assertLogs('config.errores', level='ERROR'):
            respuesta = self.client.get(URL)
        cuerpo = self.assertFormato(respuesta, 500, 'ERROR_INTERNO')
        self.assertNotIn('secreto', respuesta.content.decode())
        self.assertEqual(set(cuerpo), {'error', 'mensaje'})


class CorsTest(TestCase):
    """CORS: solo el React de Vite (localhost:5173) puede llamar a la API desde el navegador, igual que Spring."""

    def preflight(self, origen):
        return self.client.options(URL, HTTP_ORIGIN=origen, HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                                   HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization, content-type')

    def test_el_react_de_vite_esta_permitido(self):
        respuesta = self.preflight('http://localhost:5173')
        self.assertEqual(respuesta['Access-Control-Allow-Origin'], 'http://localhost:5173')

    def test_otros_origenes_no_reciben_permiso(self):
        for origen in ('http://localhost:5174', 'http://localhost:3000', 'https://pagina-cualquiera.com'):
            with self.subTest(origen=origen):
                self.assertNotIn('Access-Control-Allow-Origin', self.preflight(origen))
