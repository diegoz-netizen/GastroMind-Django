from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

import jwt
from django.conf import settings
from django.test import TestCase
from django.utils import timezone as dj_timezone
from rest_framework.test import APIClient

from .models import (Categoria, Empleado, Ingrediente, Producto, Proveedor, RecetaDetalle, RegistroIngresoProveedor,
                     Restaurante, Rol)

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


class RecetaPlatilloTest(BaseCatalogoTest):
    """HU-06 / CA-06: al menos un insumo con cantidad > 0 y sin insumos repetidos. Escribe solo el admin."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fondos = Categoria.objects.create(restaurante=cls.central, nombre='Fondos')
        cls.arroz_con_tomate = Producto.objects.create(categoria=cls.fondos, nombre='Arroz con tomate',
                                                       precio=Decimal('18.00'))
        cls.bebidas_norte = Categoria.objects.create(restaurante=cls.norte, nombre='Bebidas')
        cls.limonada_norte = Producto.objects.create(categoria=cls.bebidas_norte, nombre='Limonada',
                                                     precio=Decimal('6.00'))
        cls.chicha = Producto.objects.create(categoria=cls.fondos, nombre='Chicha morada', precio=Decimal('6.00'),
                                             requiere_receta=False)

    def url_receta(self, producto):
        return f'/api/catalogo/productos/{producto.id}/receta/'

    def guardar(self, producto, detalles, empleado=None):
        self.con_token(token_como_spring(empleado or self.admin_central))
        return self.client.post(self.url_receta(producto), {'detalles': detalles}, format='json')

    def test_admin_guarda_la_receta_y_se_puede_consultar(self):
        r = self.guardar(self.arroz_con_tomate, [
            {'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'},
            {'ingrediente': self.tomate.id, 'cantidad_requerida': '0.150'},
        ])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['detalles_receta']), 2)
        r = self.client.get(self.url_receta(self.arroz_con_tomate))
        self.assertEqual(r.status_code, 200)
        self.assertEqual({d['ingrediente_nombre'] for d in r.json()['detalles_receta']}, {'Arroz', 'Tomate'})

    def test_guardar_otra_vez_reemplaza_la_receta(self):
        self.guardar(self.arroz_con_tomate, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'}])
        self.guardar(self.arroz_con_tomate, [{'ingrediente': self.tomate.id, 'cantidad_requerida': '0.100'}])
        detalles = RecetaDetalle.objects.filter(producto=self.arroz_con_tomate)
        self.assertEqual([d.ingrediente_id for d in detalles], [self.tomate.id])

    def test_receta_sin_insumos_responde_400(self):
        r = self.guardar(self.arroz_con_tomate, [])
        self.assertEqual(r.status_code, 400)

    def test_cantidad_cero_o_negativa_responde_400(self):
        for cantidad in ('0', '-1'):
            r = self.guardar(self.arroz_con_tomate, [{'ingrediente': self.arroz.id, 'cantidad_requerida': cantidad}])
            self.assertEqual(r.status_code, 400, cantidad)
        self.assertFalse(RecetaDetalle.objects.exists())

    def test_insumo_repetido_responde_400(self):
        r = self.guardar(self.arroz_con_tomate, [
            {'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'},
            {'ingrediente': self.arroz.id, 'cantidad_requerida': '0.100'},
        ])
        self.assertEqual(r.status_code, 400)
        self.assertFalse(RecetaDetalle.objects.exists())

    def test_insumo_de_otro_restaurante_responde_400(self):
        r = self.guardar(self.arroz_con_tomate, [{'ingrediente': self.pollo_norte.id, 'cantidad_requerida': '0.300'}])
        self.assertEqual(r.status_code, 400)
        self.assertFalse(RecetaDetalle.objects.exists())

    def test_insumo_de_otro_restaurante_responde_igual_que_uno_inexistente(self):
        ajeno = self.guardar(self.arroz_con_tomate, [{'ingrediente': self.pollo_norte.id, 'cantidad_requerida': '1'}])
        inexistente = self.guardar(self.arroz_con_tomate, [{'ingrediente': 999999, 'cantidad_requerida': '1'}])
        self.assertNotIn('Pollo', ajeno.content.decode())
        self.assertEqual(ajeno.json()['campos']['detalles'].replace(str(self.pollo_norte.id), 'ID'),
                         inexistente.json()['campos']['detalles'].replace('999999', 'ID'))

    def test_error_de_validacion_usa_el_formato_hl014(self):
        r = self.guardar(self.arroz_con_tomate, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0'}])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'VALIDACION')
        self.assertIn('detalles', r.json()['campos'])

    def test_platillo_que_no_requiere_receta_responde_400(self):
        r = self.guardar(self.chicha, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0.100'}])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['mensaje'], 'Este platillo no requiere receta.')
        self.assertFalse(RecetaDetalle.objects.filter(producto=self.chicha).exists())

    def test_un_error_no_borra_la_receta_anterior(self):
        self.guardar(self.arroz_con_tomate, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'}])
        self.guardar(self.arroz_con_tomate, [{'ingrediente': self.tomate.id, 'cantidad_requerida': '0'}])
        self.assertEqual(RecetaDetalle.objects.filter(producto=self.arroz_con_tomate).count(), 1)

    def test_producto_de_otro_restaurante_responde_404(self):
        r = self.guardar(self.limonada_norte, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'}])
        self.assertEqual(r.status_code, 404)

    def test_cocinero_no_puede_guardar_la_receta_pero_si_consultarla(self):
        r = self.guardar(self.arroz_con_tomate, [{'ingrediente': self.arroz.id, 'cantidad_requerida': '0.200'}],
                         empleado=self.cocinero_central)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['mensaje'], 'Se requiere rol ADMINISTRADOR.')
        self.assertEqual(self.client.get(self.url_receta(self.arroz_con_tomate)).status_code, 200)

    def test_sin_token_responde_401(self):
        r = self.client.post(self.url_receta(self.arroz_con_tomate), {'detalles': []}, format='json')
        self.assertEqual(r.status_code, 401)


class CartaPermisosTest(BaseCatalogoTest):
    """Categorías y productos: cualquier empleado consulta los de su restaurante; solo el admin escribe."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fondos = Categoria.objects.create(restaurante=cls.central, nombre='Fondos')
        cls.bebidas_norte = Categoria.objects.create(restaurante=cls.norte, nombre='Bebidas')

    def test_admin_crea_categoria_en_su_restaurante(self):
        self.con_token(token_como_spring(self.admin_central))
        r = self.client.post('/api/catalogo/categorias/', {'nombre': 'Postres', 'restaurante': self.norte.id},
                             format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Categoria.objects.get(nombre='Postres').restaurante_id, self.central.id)

    def test_admin_crea_producto(self):
        self.con_token(token_como_spring(self.admin_central))
        r = self.client.post('/api/catalogo/productos/',
                             {'nombre': 'Lomo saltado', 'precio': '25.00', 'categoria': self.fondos.id}, format='json')
        self.assertEqual(r.status_code, 201)

    def test_producto_con_categoria_de_otro_restaurante_responde_400(self):
        self.con_token(token_como_spring(self.admin_central))
        r = self.client.post('/api/catalogo/productos/',
                             {'nombre': 'Chicha', 'precio': '5.00', 'categoria': self.bebidas_norte.id}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cocinero_no_puede_crear_categoria_ni_producto(self):
        self.con_token(token_como_spring(self.cocinero_central))
        r = self.client.post('/api/catalogo/categorias/', {'nombre': 'Postres'}, format='json')
        self.assertEqual(r.status_code, 403)
        r = self.client.post('/api/catalogo/productos/',
                             {'nombre': 'Lomo saltado', 'precio': '25.00', 'categoria': self.fondos.id}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_cada_restaurante_ve_solo_sus_categorias(self):
        self.con_token(token_como_spring(self.cocinero_central))
        r = self.client.get('/api/catalogo/categorias/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c['nombre'] for c in r.json()], ['Fondos'])

    def test_borrar_categoria_con_platillos_responde_409_y_no_borra_nada(self):
        lomo = Producto.objects.create(categoria=self.fondos, nombre='Lomo saltado', precio=Decimal('25.00'))
        RecetaDetalle.objects.create(producto=lomo, ingrediente=self.arroz, cantidad_requerida=Decimal('0.200'))
        self.con_token(token_como_spring(self.admin_central))
        r = self.client.delete(f'/api/catalogo/categorias/{self.fondos.id}/')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['error'], 'CONFLICTO')
        self.assertTrue(Categoria.objects.filter(id=self.fondos.id).exists())
        self.assertTrue(RecetaDetalle.objects.filter(producto=lomo).exists())

    def test_borrar_categoria_vacia_responde_204(self):
        vacia = Categoria.objects.create(restaurante=self.central, nombre='Postres')
        self.con_token(token_como_spring(self.admin_central))
        self.assertEqual(self.client.delete(f'/api/catalogo/categorias/{vacia.id}/').status_code, 204)
        self.assertFalse(Categoria.objects.filter(id=vacia.id).exists())


class GestionCartaTest(BaseCatalogoTest):
    """HU-07 / CA-07: el gerente crea, edita y desactiva platillos; el desactivado no sale para pedidos pero no se borra."""

    URL = '/api/catalogo/productos/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fondos = Categoria.objects.create(restaurante=cls.central, nombre='Fondos')
        cls.bebidas = Categoria.objects.create(restaurante=cls.central, nombre='Bebidas')
        cls.bebidas_norte = Categoria.objects.create(restaurante=cls.norte, nombre='Bebidas')
        cls.lomo = Producto.objects.create(categoria=cls.fondos, nombre='Lomo saltado', precio=Decimal('28.00'))
        cls.chicha = Producto.objects.create(categoria=cls.bebidas, nombre='Chicha morada', precio=Decimal('6.00'),
                                             requiere_receta=False)
        cls.limonada_norte = Producto.objects.create(categoria=cls.bebidas_norte, nombre='Limonada',
                                                     precio=Decimal('5.00'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.arroz, cantidad_requerida=Decimal('0.200'))

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def url(self, producto, extra=''):
        return f'{self.URL}{producto.id}/{extra}'

    def desactivar(self, producto):
        return self.client.patch(self.url(producto, 'estado/'), {'estado': 'INACTIVO'}, format='json')

    # --- Crear ---
    def test_admin_crea_platillo_con_su_precio_y_nace_activo(self):
        r = self.client.post(self.URL, {'nombre': '  Arroz con pollo ', 'precio': '22.50', 'categoria': self.fondos.id,
                                        'estado': 'INACTIVO'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        platillo = Producto.objects.get(id=r.json()['id'])
        self.assertEqual((platillo.nombre, platillo.precio, platillo.estado),
                         ('Arroz con pollo', Decimal('22.50'), 'ACTIVO'))

    def test_precio_cero_o_negativo_responde_400(self):
        for precio in ('0', '-3'):
            r = self.client.post(self.URL, {'nombre': 'Gratis', 'precio': precio, 'categoria': self.fondos.id},
                                 format='json')
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json()['campos']['precio'], 'Debe ser mayor que 0.')
        self.assertFalse(Producto.objects.filter(nombre='Gratis').exists())

    def test_sin_nombre_precio_ni_categoria_responde_400_por_campo(self):
        r = self.client.post(self.URL, {'nombre': '   '}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()['campos']), {'nombre', 'precio', 'categoria'})

    # --- Editar ---
    def test_admin_edita_nombre_precio_y_categoria(self):
        r = self.client.patch(self.url(self.chicha), {'nombre': 'Chicha morada (jarra)', 'precio': '18.00',
                                                      'categoria': self.fondos.id}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.chicha.refresh_from_db()
        self.assertEqual((self.chicha.nombre, self.chicha.precio, self.chicha.categoria_id),
                         ('Chicha morada (jarra)', Decimal('18.00'), self.fondos.id))

    def test_editar_no_cambia_el_estado(self):
        r = self.client.patch(self.url(self.lomo), {'estado': 'INACTIVO'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.lomo.refresh_from_db()
        self.assertEqual(self.lomo.estado, 'ACTIVO')

    def test_editar_con_precio_cero_responde_400_y_no_guarda(self):
        r = self.client.patch(self.url(self.lomo), {'precio': '0'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.lomo.refresh_from_db()
        self.assertEqual(self.lomo.precio, Decimal('28.00'))

    def test_editar_con_categoria_de_otro_restaurante_responde_400(self):
        r = self.client.patch(self.url(self.lomo), {'categoria': self.bebidas_norte.id}, format='json')
        self.assertEqual(r.status_code, 400)

    # --- Desactivar (CA-07) ---
    def test_desactivar_lo_saca_de_la_carta_para_pedidos(self):
        r = self.desactivar(self.lomo)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['estado'], 'INACTIVO')
        para_pedidos = self.client.get(self.URL, {'estado': 'ACTIVO'}).json()
        self.assertEqual([p['nombre'] for p in para_pedidos], ['Chicha morada'])

    def test_desactivado_se_conserva_con_su_receta(self):
        self.desactivar(self.lomo)
        self.assertTrue(Producto.objects.filter(id=self.lomo.id, estado='INACTIVO').exists())
        detalle = self.client.get(self.url(self.lomo))
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(len(detalle.json()['detalles_receta']), 1)
        todos = self.client.get(self.URL).json()
        self.assertEqual({p['nombre']: p['estado'] for p in todos},
                         {'Chicha morada': 'ACTIVO', 'Lomo saltado': 'INACTIVO'})

    def test_reactivar_lo_devuelve_a_la_carta(self):
        self.desactivar(self.lomo)
        r = self.client.patch(self.url(self.lomo, 'estado/'), {'estado': 'ACTIVO'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Lomo saltado', [p['nombre'] for p in self.client.get(self.URL, {'estado': 'ACTIVO'}).json()])

    def test_estado_invalido_responde_400(self):
        r = self.client.patch(self.url(self.lomo, 'estado/'), {'estado': 'BORRADO'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('estado', r.json()['campos'])
        r = self.client.get(self.URL, {'estado': 'otro'})
        self.assertEqual(r.status_code, 400)

    def test_borrar_no_existe_405_y_el_platillo_sigue(self):
        r = self.client.delete(self.url(self.lomo))
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r.json()['error'], 'METODO_NO_PERMITIDO')
        self.assertTrue(Producto.objects.filter(id=self.lomo.id).exists())

    # --- Permisos y restaurante ---
    def test_cocinero_consulta_pero_no_edita_ni_desactiva(self):
        self.con_token(token_como_spring(self.cocinero_central))
        self.assertEqual(self.client.get(self.URL).status_code, 200)
        self.assertEqual(self.client.patch(self.url(self.lomo), {'precio': '1.00'}, format='json').status_code, 403)
        self.assertEqual(self.desactivar(self.lomo).status_code, 403)
        self.lomo.refresh_from_db()
        self.assertEqual((self.lomo.precio, self.lomo.estado), (Decimal('28.00'), 'ACTIVO'))

    def test_platillo_de_otro_restaurante_responde_404(self):
        self.assertEqual(self.client.patch(self.url(self.limonada_norte), {'precio': '1.00'},
                                           format='json').status_code, 404)
        self.assertEqual(self.desactivar(self.limonada_norte).status_code, 404)
        self.limonada_norte.refresh_from_db()
        self.assertEqual(self.limonada_norte.estado, 'ACTIVO')

    def test_sin_token_responde_401(self):
        self.client.credentials()
        self.assertEqual(self.desactivar(self.lomo).status_code, 401)


class CostoPlatilloTest(BaseCatalogoTest):
    """HU-08 / CA-08: costo = Σ(cantidad × costo unitario) y se actualiza al cambiar la receta o el costo del insumo."""

    URL = '/api/catalogo/productos/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        fondos = Categoria.objects.create(restaurante=cls.central, nombre='Fondos')
        bebidas = Categoria.objects.create(restaurante=cls.central, nombre='Bebidas')

        def insumo(nombre, costo):
            return Ingrediente.objects.create(restaurante=cls.central, nombre=nombre, unidad_medida='kg',
                                              stock_actual=Decimal('10'), stock_minimo=Decimal('1'),
                                              costo_unitario=Decimal(costo))

        cls.lomo_res = insumo('Lomo de res', '38.00')
        cls.papa = insumo('Papa amarilla', '2.80')
        cls.lomo = Producto.objects.create(categoria=fondos, nombre='Lomo saltado', precio=Decimal('32.00'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.lomo_res, cantidad_requerida=Decimal('0.200'))
        RecetaDetalle.objects.create(producto=cls.lomo, ingrediente=cls.papa, cantidad_requerida=Decimal('0.250'))
        cls.chicha = Producto.objects.create(categoria=bebidas, nombre='Chicha morada', precio=Decimal('12.00'),
                                             requiere_receta=False)

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def detalle(self, producto):
        return self.client.get(f'{self.URL}{producto.id}/').json()

    def test_costo_es_la_suma_de_cantidad_por_costo_unitario(self):
        # 0.200 × 38.00 + 0.250 × 2.80 = 7.60 + 0.70
        platillo = self.detalle(self.lomo)
        self.assertEqual(platillo['costo'], '8.30')
        self.assertEqual(platillo['margen'], '23.70')
        self.assertEqual(platillo['porcentaje_costo'], '25.9')

    def test_la_lista_trae_el_costo_de_cada_platillo(self):
        costos = {p['nombre']: p['costo'] for p in self.client.get(self.URL).json()}
        self.assertEqual(costos, {'Lomo saltado': '8.30', 'Chicha morada': '0.00'})

    def test_platillo_sin_receta_cuesta_cero_y_su_margen_es_el_precio(self):
        platillo = self.detalle(self.chicha)
        self.assertEqual((platillo['costo'], platillo['margen'], platillo['porcentaje_costo']), ('0.00', '12.00', '0.0'))

    def test_al_cambiar_la_receta_cambia_el_costo(self):
        r = self.client.post(f'{self.URL}{self.lomo.id}/receta/',
                             {'detalles': [{'ingrediente': self.lomo_res.id, 'cantidad_requerida': '0.250'}]},
                             format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['costo'], '9.50')  # la respuesta ya trae el costo nuevo
        self.assertEqual(self.detalle(self.lomo)['costo'], '9.50')

    def test_al_cambiar_el_costo_del_insumo_cambia_el_costo_del_platillo(self):
        Ingrediente.objects.filter(pk=self.lomo_res.pk).update(costo_unitario=Decimal('40.00'))
        self.assertEqual(self.detalle(self.lomo)['costo'], '8.70')  # 8.00 + 0.70

    def test_se_redondea_una_sola_vez_al_final(self):
        # 0.005 × 1.00 dos veces = 0.010 → 0.01 (redondeando cada línea saldría 0.02)
        a, b = self.lomo_res, self.papa
        Ingrediente.objects.filter(pk__in=[a.pk, b.pk]).update(costo_unitario=Decimal('1.00'))
        RecetaDetalle.objects.filter(producto=self.lomo).update(cantidad_requerida=Decimal('0.005'))
        self.assertEqual(self.detalle(self.lomo)['costo'], '0.01')

    def test_el_costo_no_se_puede_escribir(self):
        r = self.client.patch(f'{self.URL}{self.lomo.id}/', {'costo': '1.00', 'margen': '31.00'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['costo'], '8.30')

    def test_el_cocinero_tambien_ve_el_costo(self):
        self.con_token(token_como_spring(self.cocinero_central))
        self.assertEqual(self.detalle(self.lomo)['costo'], '8.30')


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


URL_ALERTAS = '/api/catalogo/alertas/'


class AlertasTest(BaseCatalogoTest):
    """HU-16 (CA-16): stock en el mínimo o debajo, y lotes que vencen en 3 días o menos."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sal = Ingrediente.objects.create(restaurante=cls.central, nombre='Sal', unidad_medida='kg',
                                             stock_actual=Decimal('5'), stock_minimo=Decimal('5'),
                                             costo_unitario=Decimal('1.00'))
        cls.proveedor = Proveedor.objects.create(restaurante=cls.central, nombre='Mercado Central')
        cls.proveedor_norte = Proveedor.objects.create(restaurante=cls.norte, nombre='Mercado Norte')

    def lote(self, insumo, vence_en_dias, lote='L-1', proveedor=None):
        hoy = dj_timezone.localdate()
        vence = None if vence_en_dias is None else hoy + timedelta(days=vence_en_dias)
        return RegistroIngresoProveedor.objects.create(
            empleado=self.admin_central, proveedor=proveedor or self.proveedor, ingrediente=insumo, lote=lote,
            fecha_vencimiento=vence, cantidad_recibida=Decimal('3'), costo_total=Decimal('30'),
            fecha_registro=datetime.now(timezone.utc))

    def alertas(self, empleado=None):
        self.con_token(token_como_spring(empleado or self.admin_central))
        return self.client.get(URL_ALERTAS)

    def test_stock_en_el_minimo_o_debajo_salta_y_encima_no(self):
        datos = self.alertas().json()
        self.assertEqual([i['nombre'] for i in datos['stock_minimo']], ['Sal', 'Tomate'])  # Arroz 20/5 no
        tomate = datos['stock_minimo'][1]
        self.assertEqual(Decimal(tomate['faltante']), Decimal('3'))

    def test_el_listado_de_insumos_tambien_marca_el_minimo_exacto(self):
        # Mismo criterio en HU-05: con stock = mínimo, bajo_stock_minimo ya es True
        self.con_token(token_como_spring(self.admin_central))
        datos = {i['nombre']: i['bajo_stock_minimo'] for i in self.client.get(URL).json()}
        self.assertTrue(datos['Sal'])

    def test_lote_que_vence_en_3_dias_salta_y_en_4_no(self):
        self.lote(self.arroz, 3, lote='VENCE-3')
        self.lote(self.arroz, 4, lote='VENCE-4')
        self.lote(self.arroz, 0, lote='VENCE-HOY')
        self.lote(self.arroz, None, lote='NO-PERECIBLE')
        datos = self.alertas().json()['vencimiento']
        self.assertEqual([(l['lote'], l['dias_restantes'], l['vencido']) for l in datos],
                         [('VENCE-HOY', 0, False), ('VENCE-3', 3, False)])
        self.assertEqual(datos[0]['proveedor'], 'Mercado Central')
        self.assertEqual(datos[0]['insumo'], 'Arroz')

    def test_lote_vencido_sale_solo_si_el_insumo_tiene_stock(self):
        sin_stock = Ingrediente.objects.create(restaurante=self.central, nombre='Leche', unidad_medida='l',
                                               stock_actual=Decimal('0'), stock_minimo=Decimal('1'),
                                               costo_unitario=Decimal('4.00'))
        self.lote(self.arroz, -2, lote='VENCIDO-CON-STOCK')
        self.lote(sin_stock, -2, lote='VENCIDO-SIN-STOCK')
        datos = self.alertas().json()['vencimiento']
        self.assertEqual([(l['lote'], l['dias_restantes'], l['vencido']) for l in datos],
                         [('VENCIDO-CON-STOCK', -2, True)])

    def test_total_suma_las_dos_listas(self):
        self.lote(self.arroz, 1)
        datos = self.alertas().json()
        self.assertEqual(datos['total'], 3)  # Sal + Tomate + 1 lote

    def test_no_muestra_alertas_de_otro_restaurante(self):
        pollo_bajo = Ingrediente.objects.create(restaurante=self.norte, nombre='Ají', unidad_medida='kg',
                                                stock_actual=Decimal('0'), stock_minimo=Decimal('2'),
                                                costo_unitario=Decimal('3.00'))
        self.lote(pollo_bajo, 1, lote='NORTE', proveedor=self.proveedor_norte)
        datos = self.alertas().json()
        self.assertNotIn('Ají', [i['nombre'] for i in datos['stock_minimo']])
        self.assertEqual(datos['vencimiento'], [])
        norte = self.alertas(self.admin_norte).json()
        self.assertEqual([i['nombre'] for i in norte['stock_minimo']], ['Ají'])
        self.assertEqual([l['lote'] for l in norte['vencimiento']], ['NORTE'])

    def test_almacenero_las_ve_y_cocina_recibe_403(self):
        self.assertEqual(self.alertas(self.almacenero_central).status_code, 200)
        self.assertEqual(self.alertas(self.cocinero_central).status_code, 403)

    def test_sin_token_responde_401(self):
        self.assertEqual(self.client.get(URL_ALERTAS).status_code, 401)
