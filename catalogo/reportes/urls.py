from django.urls import path

from .panel import PanelView

# /api/catalogo/reportes/...  Solo ADMINISTRADOR (permissions.EsAdmin)
urlpatterns = [
    path('panel/', PanelView.as_view(), name='reporte-panel'),  # HU-23
]
