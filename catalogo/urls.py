from rest_framework.routers import DefaultRouter

from .views import IngredienteViewSet

router = DefaultRouter()
router.register('insumos', IngredienteViewSet, basename='insumo')

urlpatterns = router.urls
