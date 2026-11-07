from django.urls import path

from .consumo import ConsumoTeoricoRealView

# /api/catalogo/reportes/...  Solo ADMINISTRADOR (permissions.EsAdmin)
urlpatterns = [
    path('consumo/', ConsumoTeoricoRealView.as_view(), name='reporte-consumo'),  # HU-20
]
