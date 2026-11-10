"""HU-22: proveedores con sus precios (ProveedorViewSet) y el de menor costo total (CA-22)."""
from decimal import Decimal

from catalogo.models import Proveedor, ProveedorInsumo
from .test_catalogo import BaseCatalogoTest, token_como_spring

URL = '/api/catalogo/proveedores/'
COMPARAR = '/api/catalogo/reportes/proveedores/'


class BaseProveedoresTest(BaseCatalogoTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avicola = Proveedor.objects.create(restaurante=cls.central, nombre='Avícola Santa Rosa')
        cls.mercado = Proveedor.objects.create(restaurante=cls.central, nombre='Mercado Mayorista',
                                               contacto='Sr. Quispe')
        cls.litoral = Proveedor.objects.create(restaurante=cls.norte, nombre='Pescados del Litoral')

    def setUp(self):
        super().setUp()
        self.con_token(token_como_spring(self.admin_central))

    def precio(self, proveedor, insumo, precio, dias=1, flete='0'):
        return ProveedorInsumo.objects.create(proveedor=proveedor, ingrediente=insumo, precio_unitario=Decimal(precio),
                                              tiempo_entrega_dias=dias, flete=Decimal(flete))


class ProveedorViewSetTest(BaseProveedoresTest):

    def guardar_precio(self, proveedor, **datos):
        return self.client.post(f'{URL}{proveedor.id}/precios/', datos, format='json')

    def test_lista_solo_los_del_restaurante_con_sus_precios(self):
        self.precio(self.mercado, self.tomate, '4.30', dias=2, flete='5')
        datos = self.client.get(URL).json()
        self.assertEqual([p['nombre'] for p in datos], ['Avícola Santa Rosa', 'Mercado Mayorista'])
        mercado = datos[1]
        self.assertEqual(mercado['contacto'], 'Sr. Quispe')
        self.assertEqual(mercado['precios'], [{'id': mercado['precios'][0]['id'], 'insumo_id': self.tomate.id,
                                               'insumo': 'Tomate', 'unidad': 'kg', 'precio_unitario': '4.30',
                                               'tiempo_entrega_dias': 2, 'flete': '5.00'}])

    def test_registra_un_proveedor_en_el_restaurante_del_token(self):
        respuesta = self.client.post(URL, {'nombre': '  Carnes del Valle ', 'contacto': ''}, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        nuevo = Proveedor.objects.get(id=respuesta.json()['id'])
        self.assertEqual((nuevo.nombre, nuevo.contacto, nuevo.restaurante_id), ('Carnes del Valle', None,
                                                                                 self.central.id))

    def test_nombre_repetido_en_el_restaurante_responde_400_pero_en_otro_vale(self):
        respuesta = self.client.post(URL, {'nombre': 'avícola santa rosa'}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('nombre', respuesta.json()['campos'])
        self.assertEqual(self.client.post(URL, {'nombre': 'Pescados del Litoral'}, format='json').status_code, 201)

    def test_sin_nombre_responde_400(self):
        respuesta = self.client.post(URL, {'contacto': 'x'}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('nombre', respuesta.json()['campos'])

    def test_cambia_el_contacto_y_puede_conservar_su_nombre(self):
        respuesta = self.client.patch(f'{URL}{self.mercado.id}/', {'nombre': 'Mercado Mayorista',
                                                                   'contacto': '912 345 678'}, format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.mercado.refresh_from_db()
        self.assertEqual(self.mercado.contacto, '912 345 678')

    def test_no_se_borran(self):
        self.assertEqual(self.client.delete(f'{URL}{self.mercado.id}/').status_code, 405)
        self.assertTrue(Proveedor.objects.filter(id=self.mercado.id).exists())

    def test_proveedor_de_otro_restaurante_responde_404(self):
        self.assertEqual(self.client.get(f'{URL}{self.litoral.id}/').status_code, 404)
        self.assertEqual(self.guardar_precio(self.litoral, insumo_id=self.tomate.id, precio_unitario='1',
                                             tiempo_entrega_dias=1).status_code, 404)

    def test_guarda_un_precio_y_al_repetirlo_lo_reemplaza(self):
        nuevo = self.guardar_precio(self.mercado, insumo_id=self.tomate.id, precio_unitario='4.30',
                                    tiempo_entrega_dias=1)
        self.assertEqual(nuevo.status_code, 201, nuevo.content)
        self.assertEqual(nuevo.json()['flete'], '0.00')
        cambiado = self.guardar_precio(self.mercado, insumo_id=self.tomate.id, precio_unitario='4.10',
                                       tiempo_entrega_dias=2, flete='3.50')
        self.assertEqual(cambiado.status_code, 200, cambiado.content)
        precio = ProveedorInsumo.objects.get(proveedor=self.mercado, ingrediente=self.tomate)
        self.assertEqual((precio.precio_unitario, precio.tiempo_entrega_dias, precio.flete),
                         (Decimal('4.10'), 2, Decimal('3.50')))
        self.assertEqual(ProveedorInsumo.objects.filter(proveedor=self.mercado).count(), 1)

    def test_precio_con_datos_invalidos_responde_400_y_no_guarda(self):
        malos = [
            {'insumo_id': self.tomate.id, 'precio_unitario': '0', 'tiempo_entrega_dias': 1},
            {'insumo_id': self.tomate.id, 'precio_unitario': '4', 'tiempo_entrega_dias': -1},
            {'insumo_id': self.tomate.id, 'precio_unitario': '4', 'tiempo_entrega_dias': 1, 'flete': '-1'},
            {'insumo_id': self.pollo_norte.id, 'precio_unitario': '4', 'tiempo_entrega_dias': 1},
            {'precio_unitario': '4', 'tiempo_entrega_dias': 1},
        ]
        for datos in malos:
            with self.subTest(datos=datos):
                self.assertEqual(self.guardar_precio(self.mercado, **datos).status_code, 400)
        self.assertFalse(ProveedorInsumo.objects.exists())

    def test_solo_el_administrador(self):
        for empleado in (self.almacenero_central, self.cocinero_central):
            self.con_token(token_como_spring(empleado))
            self.assertEqual(self.client.get(URL).status_code, 403)
            self.assertEqual(self.client.post(URL, {'nombre': 'Otro'}, format='json').status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(URL).status_code, 401)


class CompararProveedoresTest(BaseProveedoresTest):
    """CA-22: ante dos proveedores del mismo insumo, se sugiere el de menor costo total (precio × cantidad + flete)."""

    def setUp(self):
        super().setUp()
        # Avícola: S/ 11.20 sin flete · Mercado: S/ 10.50 con S/ 12.00 de flete
        self.precio(self.avicola, self.tomate, '11.20', dias=1)
        self.precio(self.mercado, self.tomate, '10.50', dias=2, flete='12')

    def comparar(self, **params):
        respuesta = self.client.get(COMPARAR, {'insumo': self.tomate.id, **params})
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return respuesta.json()

    def test_con_poca_cantidad_conviene_el_que_no_cobra_flete(self):
        datos = self.comparar(cantidad='10')
        self.assertEqual([(o['proveedor'], o['costo_total'], o['sugerido']) for o in datos['opciones']],
                         [('Avícola Santa Rosa', '112.00', True), ('Mercado Mayorista', '117.00', False)])

    def test_con_mucha_cantidad_conviene_el_mas_barato_por_kilo(self):
        datos = self.comparar(cantidad='20')
        self.assertEqual(datos['opciones'][0]['proveedor'], 'Mercado Mayorista')
        self.assertEqual(datos['opciones'][0]['costo_total'], '222.00')
        self.assertEqual((datos['insumo'], datos['unidad'], datos['cantidad']), ('Tomate', 'kg', '20'))

    def test_si_empatan_gana_el_que_entrega_antes(self):
        ProveedorInsumo.objects.filter(proveedor=self.mercado).update(precio_unitario=Decimal('11.20'),
                                                                      flete=Decimal('0'))
        self.assertEqual(self.comparar(cantidad='5')['opciones'][0]['proveedor'], 'Avícola Santa Rosa')

    def test_sin_cantidad_compara_una_unidad(self):
        datos = self.comparar()
        self.assertEqual(datos['cantidad'], '1')
        self.assertEqual(datos['opciones'][0]['costo_total'], '11.20')

    def test_insumo_sin_proveedores_devuelve_la_lista_vacia(self):
        datos = self.client.get(COMPARAR, {'insumo': self.arroz.id}).json()
        self.assertEqual(datos['opciones'], [])

    def test_insumo_inexistente_o_de_otro_restaurante_responde_400(self):
        for insumo in ('', 'abc', '999999', str(self.pollo_norte.id)):
            with self.subTest(insumo=insumo):
                respuesta = self.client.get(COMPARAR, {'insumo': insumo})
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn('insumo', respuesta.json()['campos'])

    def test_cantidad_invalida_responde_400(self):
        for cantidad in ('0', '-2', 'diez', '1.0005', 'NaN'):
            with self.subTest(cantidad=cantidad):
                respuesta = self.client.get(COMPARAR, {'insumo': self.tomate.id, 'cantidad': cantidad})
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn('cantidad', respuesta.json()['campos'])

    def test_solo_el_administrador(self):
        self.con_token(token_como_spring(self.almacenero_central))
        self.assertEqual(self.client.get(COMPARAR, {'insumo': self.tomate.id}).status_code, 403)
