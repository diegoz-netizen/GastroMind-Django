"""
HU-24 (CA-24): descarga en Excel de los reportes de inventario y merma, con los mismos filtros de la pantalla.

GET /api/catalogo/reportes/exportar/?tipo=merma&desde=&hasta=&insumo=&motivo=   (HU-19)
GET /api/catalogo/reportes/exportar/?tipo=consumo&desde=&hasta=                  (HU-20, teórico contra real)
GET /api/catalogo/reportes/exportar/?tipo=inventario                             (stock de hoy de cada insumo)

Los números salen de las mismas funciones que la pantalla, así el Excel dice lo mismo que se ve.
Cada archivo trae arriba el restaurante, el periodo y los filtros aplicados.
"""
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from catalogo.models import Ingrediente, Restaurante
from catalogo.permissions import EsAdmin
from .comun import periodo
from .consumo import UMBRAL_DESVIACION, teorico_vs_real
from .merma import _id, merma_por_motivo, motivos_disponibles, resumen_merma

TIPOS = ('merma', 'consumo', 'inventario')
XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

NEGRITA = Font(bold=True)
TITULO = Font(bold=True, size=14)
RESALTADO = PatternFill('solid', fgColor='FFF4CE')
CANTIDAD, SOLES, PORCENTAJE = '#,##0.000', '"S/ "#,##0.00', '0.0" %"'


def _num(texto):
    """La API arma los números como texto ("0.850"); en el Excel van como número para poder sumarlos."""
    return None if texto is None else Decimal(texto)


def _fecha(dia):
    return dia.strftime('%d/%m/%Y')


class Hoja:
    """Una hoja con encabezado (título, restaurante, periodo y filtros) y tablas debajo."""

    def __init__(self, libro, titulo, restaurante, lineas):
        self.ws = libro.active  # un reporte por archivo
        self.ws.title = titulo[:31]
        self.ws.append([f'GastroMind · {titulo}'])
        self.ws['A1'].font = TITULO
        self.ws.append([restaurante])
        for linea in lineas:
            self.ws.append([linea])
        self.ws.append([f'Generado: {timezone.localtime().strftime("%d/%m/%Y %H:%M")}'])
        self.ws.append([])
        self.anchos = {}

    def tabla(self, columnas, filas, formatos, resaltar=None, subtitulo=None):
        """columnas: encabezados; filas: listas de valores; formatos: formato de número por columna (o None)."""
        if subtitulo:
            self.ws.append([subtitulo])
            self.ws.cell(self.ws.max_row, 1).font = NEGRITA
        self.ws.append(columnas)
        for celda in self.ws[self.ws.max_row]:
            celda.font = NEGRITA
        for i, fila in enumerate(filas):
            self.ws.append(fila)
            for col, formato in enumerate(formatos, start=1):
                celda = self.ws.cell(self.ws.max_row, col)
                if formato:
                    celda.number_format = formato
                if resaltar and resaltar[i]:
                    celda.fill = RESALTADO
        for col, titulo in enumerate(columnas, start=1):
            largo = max([len(str(titulo))] + [len(str(f[col - 1])) for f in filas if f[col - 1] is not None])
            self.anchos[col] = max(self.anchos.get(col, 10), min(largo + 3, 45))
        self.ws.append([])

    def cerrar(self):
        for col, ancho in self.anchos.items():
            self.ws.column_dimensions[get_column_letter(col)].width = ancho


def hoja_merma(libro, request, restaurante):
    restaurante_id = restaurante.id
    desde, hasta = periodo(request)
    motivos = motivos_disponibles(restaurante_id)
    insumos = Ingrediente.objects.filter(restaurante_id=restaurante_id)
    insumo_id = _id(request, 'insumo', insumos, 'Insumo no encontrado.')
    motivo_id = _id(request, 'motivo', motivos, 'Motivo no encontrado.')
    filas, total = resumen_merma(restaurante_id, desde, hasta, insumo_id, motivo_id)
    por_motivo = merma_por_motivo(restaurante_id, desde, hasta, insumo_id)

    insumo = insumos.get(id=insumo_id).nombre if insumo_id else 'todos'
    motivo = motivos.get(id=motivo_id).nombre if motivo_id else 'todos'
    hoja = Hoja(libro, 'Merma', restaurante.nombre, [
        f'Periodo: {_fecha(desde)} al {_fecha(hasta)}',
        f'Filtros: insumo {insumo} · motivo {motivo}',
        f'Merma sobre el consumo total: {total["porcentaje"]} % (S/ {total["costo_merma"]} de S/ {total["costo_consumo"]})',
    ])
    hoja.tabla(['Insumo', 'Unidad', 'Consumo total', 'Merma', '% merma', 'Costo de la merma'],
               [[f['insumo'], f['unidad'], _num(f['consumo']), _num(f['merma']), _num(f['porcentaje']),
                 _num(f['costo_merma'])] for f in filas],
               [None, None, CANTIDAD, CANTIDAD, PORCENTAJE, SOLES])
    hoja.tabla(['Motivo', 'Costo', '% de la merma'],
               [[m['motivo'], _num(m['costo']), _num(m['porcentaje'])] for m in por_motivo],
               [None, SOLES, PORCENTAJE], subtitulo='Por motivo')
    hoja.cerrar()
    return f'merma_{desde}_{hasta}'


def hoja_consumo(libro, request, restaurante):
    desde, hasta = periodo(request)
    filas = teorico_vs_real(restaurante.id, desde, hasta)
    hoja = Hoja(libro, 'Teórico vs. real', restaurante.nombre, [
        f'Periodo: {_fecha(desde)} al {_fecha(hasta)}',
        f'Teórico: platillos servidos × su receta. Real: lo que salió del almacén. '
        f'Resaltado: diferencia mayor a {UMBRAL_DESVIACION} % o sin teórico.',
    ])
    hoja.tabla(['Insumo', 'Unidad', 'Teórico', 'Real', 'Diferencia', '%', 'Revisar'],
               [[f['insumo'], f['unidad'], _num(f['teorico']), _num(f['real']), _num(f['diferencia']),
                 _num(f['porcentaje']), 'Sí' if f['resaltar'] else ''] for f in filas],
               [None, None, CANTIDAD, CANTIDAD, CANTIDAD, PORCENTAJE, None],
               resaltar=[f['resaltar'] for f in filas])
    hoja.cerrar()
    return f'teorico_vs_real_{desde}_{hasta}'


def hoja_inventario(libro, request, restaurante):
    hoy = timezone.localdate()
    insumos = Ingrediente.objects.filter(restaurante_id=restaurante.id).order_by('nombre')
    bajo = [i.stock_actual <= i.stock_minimo for i in insumos]
    hoja = Hoja(libro, 'Inventario', restaurante.nombre, [
        f'Stock al {_fecha(hoy)}. Resaltado: en el mínimo o por debajo.',
    ])
    hoja.tabla(['Insumo', 'Unidad', 'Control', 'Stock', 'Mínimo', 'Costo unitario', 'Valor del stock', 'Bajo mínimo'],
               [[i.nombre, i.unidad_medida, i.tipo_control, i.stock_actual, i.stock_minimo, i.costo_unitario,
                 (i.stock_actual * i.costo_unitario).quantize(Decimal('0.01')), 'Sí' if b else '']
                for i, b in zip(insumos, bajo)],
               [None, None, None, CANTIDAD, CANTIDAD, SOLES, SOLES, None], resaltar=bajo)
    hoja.cerrar()
    return f'inventario_{hoy}'


HOJAS = {'merma': hoja_merma, 'consumo': hoja_consumo, 'inventario': hoja_inventario}


class ExportarView(APIView):
    """GET /api/catalogo/reportes/exportar/?tipo=...   Solo ADMINISTRADOR. Devuelve un .xlsx."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        tipo = request.query_params.get('tipo', '')
        if tipo not in TIPOS:
            raise ValidationError({'tipo': [f'Debe ser uno de: {", ".join(TIPOS)}.']})
        restaurante = Restaurante.objects.get(id=request.user.restaurante_id)
        libro = Workbook()
        nombre = HOJAS[tipo](libro, request, restaurante)

        archivo = BytesIO()
        libro.save(archivo)
        respuesta = HttpResponse(archivo.getvalue(), content_type=XLSX)
        respuesta['Content-Disposition'] = f'attachment; filename="gastromind_{nombre}.xlsx"'
        return respuesta
