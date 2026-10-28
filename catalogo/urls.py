from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertasView, IngredienteViewSet, CategoriaViewSet, ProductoViewSet

router = DefaultRouter()
router.register(r'insumos', IngredienteViewSet, basename='insumo')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    path('alertas/', AlertasView.as_view(), name='alertas'),  # HU-16
    path('', include(router.urls)),
]
