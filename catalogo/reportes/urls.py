from django.urls import path

from .consumo import ConsumoTeoricoRealView
from .panel import PanelView
from .proveedores import CompararProveedoresView

# /api/catalogo/reportes/...  Solo ADMINISTRADOR (permissions.EsAdmin)
urlpatterns = [
    path('consumo/', ConsumoTeoricoRealView.as_view(), name='reporte-consumo'),  # HU-20
    path('panel/', PanelView.as_view(), name='reporte-panel'),  # HU-23
    path('proveedores/', CompararProveedoresView.as_view(), name='reporte-proveedores'),  # HU-22
]
