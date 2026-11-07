from django.urls import path

from .consumo import ConsumoTeoricoRealView
from .merma import MermaView
from .panel import PanelView
from .proveedores import CompararProveedoresView
from .sugerencia import SugerenciaCompraView

# /api/catalogo/reportes/...  Solo ADMINISTRADOR (permissions.EsAdmin)
urlpatterns = [
    path('consumo/', ConsumoTeoricoRealView.as_view(), name='reporte-consumo'),  # HU-20
    path('panel/', PanelView.as_view(), name='reporte-panel'),  # HU-23
    path('merma/', MermaView.as_view(), name='reporte-merma'),  # HU-19
    path('proveedores/', CompararProveedoresView.as_view(), name='reporte-proveedores'),  # HU-22
    path('sugerencia/', SugerenciaCompraView.as_view(), name='reporte-sugerencia'),  # HU-21
]
