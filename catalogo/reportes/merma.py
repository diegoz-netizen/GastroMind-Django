"""
HU-19 (CA-19): la merma sobre el consumo total, en porcentaje, por periodo, insumo y motivo.
- Por insumo: merma ÷ todo lo que salió del almacén (CONSUMO + MERMA), en su unidad.
- Total del restaurante: en soles (costo de la merma ÷ costo de todo lo que salió), porque cada insumo
  tiene su unidad y no se pueden sumar kilos con unidades.
- Por motivo: cuánto costó cada uno y qué parte de la merma es.
?insumo= deja un solo insumo. ?motivo= cuenta solo la merma de ese motivo, siempre sobre todo el consumo.
"""
from collections import defaultdict
from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogo.models import Ingrediente, MotivoMerma, MovimientoInventario, RegistroMerma
from catalogo.permissions import EsAdmin
from .comun import CERO, periodo, rango, soles

TRES = Decimal('0.001')
UNO = Decimal('0.1')
SIN_MOTIVO = 'Sin motivo'


def motivos_disponibles(restaurante_id):
    """Los mismos que ofrece Spring al registrar (HU-17): los globales y los del restaurante."""
    return MotivoMerma.objects.filter(Q(es_global=True) | Q(restaurante_id=restaurante_id)).order_by('nombre')


def porcentaje(parte, total):
    return (parte * 100 / total).quantize(UNO) if total else CERO.quantize(UNO)


def salidas_del_periodo(restaurante_id, desde, hasta, insumo_id=None):
    inicio, fin = rango(desde, hasta)
    salidas = MovimientoInventario.objects.filter(ingrediente__restaurante_id=restaurante_id,
                                                  tipo__in=('CONSUMO', 'MERMA'), fecha__gte=inicio, fecha__lt=fin)
    return salidas.filter(ingrediente_id=insumo_id) if insumo_id else salidas


def _por_insumo(movimientos):
    # Las salidas se guardan en negativo
    return {m['ingrediente_id']: -m['total'] for m in movimientos.values('ingrediente_id').annotate(total=Sum('cantidad'))}


def resumen_merma(restaurante_id, desde, hasta, insumo_id=None, motivo_id=None):
    salidas = salidas_del_periodo(restaurante_id, desde, hasta, insumo_id)
    mermas = salidas.filter(tipo='MERMA')
    if motivo_id:
        mermas = mermas.filter(registro_merma_id__in=RegistroMerma.objects.filter(motivo_id=motivo_id).values('id'))
    consumo, merma = _por_insumo(salidas), _por_insumo(mermas)

    filas, costo_consumo, costo_merma = [], CERO, CERO
    for insumo in Ingrediente.objects.filter(id__in=consumo).order_by('nombre'):
        total, mermado = consumo[insumo.id], merma.get(insumo.id, CERO)
        if total <= 0:
            continue
        costo_consumo += total * insumo.costo_unitario
        costo_merma += mermado * insumo.costo_unitario
        filas.append({'id': insumo.id, 'insumo': insumo.nombre, 'unidad': insumo.unidad_medida,
                      'consumo': str(total.quantize(TRES)), 'merma': str(mermado.quantize(TRES)),
                      'porcentaje': str(porcentaje(mermado, total)),
                      'costo_merma': str(soles(mermado * insumo.costo_unitario))})
    # Primero lo que más se pierde
    filas.sort(key=lambda f: (-Decimal(f['porcentaje']), f['insumo']))
    total = {'costo_consumo': str(soles(costo_consumo)), 'costo_merma': str(soles(costo_merma)),
             'porcentaje': str(porcentaje(costo_merma, costo_consumo))}
    return filas, total


def merma_por_motivo(restaurante_id, desde, hasta, insumo_id=None):
    """Costo de la merma de cada motivo y su parte del total. Lo que no tiene registro_merma va como 'Sin motivo'."""
    mermas = list(salidas_del_periodo(restaurante_id, desde, hasta, insumo_id).filter(tipo='MERMA')
                  .values('registro_merma_id', 'cantidad', 'ingrediente__costo_unitario'))
    nombres = dict(RegistroMerma.objects.filter(id__in={m['registro_merma_id'] for m in mermas})
                   .values_list('id', 'motivo__nombre'))
    costos = defaultdict(Decimal)
    for m in mermas:
        costos[nombres.get(m['registro_merma_id'], SIN_MOTIVO)] += -m['cantidad'] * m['ingrediente__costo_unitario']
    total = sum(costos.values(), CERO)
    motivos = [{'motivo': nombre, 'costo': str(soles(costo)), 'porcentaje': str(porcentaje(costo, total))}
               for nombre, costo in costos.items()]
    motivos.sort(key=lambda m: (-Decimal(m['costo']), m['motivo']))
    return motivos


def _id(request, nombre, opciones, error):
    texto = request.query_params.get(nombre) or ''
    if not texto:
        return None
    # Uno de otro restaurante se trata como inexistente
    if not texto.isdigit() or not opciones.filter(id=texto).exists():
        raise ValidationError({nombre: [error]})
    return int(texto)


class MermaView(APIView):
    """GET /api/catalogo/reportes/merma/?desde=&hasta=&insumo=&motivo=   Solo ADMINISTRADOR."""

    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        restaurante_id = request.user.restaurante_id
        desde, hasta = periodo(request)
        motivos = motivos_disponibles(restaurante_id)
        insumo_id = _id(request, 'insumo', Ingrediente.objects.filter(restaurante_id=restaurante_id),
                        'Insumo no encontrado.')
        motivo_id = _id(request, 'motivo', motivos, 'Motivo no encontrado.')
        filas, total = resumen_merma(restaurante_id, desde, hasta, insumo_id, motivo_id)
        return Response({'desde': desde, 'hasta': hasta, 'insumo_id': insumo_id, 'motivo_id': motivo_id,
                         'total': total, 'filas': filas,
                         'motivos': merma_por_motivo(restaurante_id, desde, hasta, insumo_id),
                         'motivos_disponibles': [{'id': m.id, 'nombre': m.nombre} for m in motivos]})
