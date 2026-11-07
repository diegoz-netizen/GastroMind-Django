from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertasView, IngredienteViewSet, CategoriaViewSet, ProductoViewSet, ProveedorViewSet

router = DefaultRouter()
router.register(r'insumos', IngredienteViewSet, basename='insumo')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'proveedores', ProveedorViewSet, basename='proveedor')  # HU-22

urlpatterns = [
    path('alertas/', AlertasView.as_view(), name='alertas'),  # HU-16
    path('reportes/', include('catalogo.reportes.urls')),  # Sprint 4: HU-19 a HU-24
    path('', include(router.urls)),
]
