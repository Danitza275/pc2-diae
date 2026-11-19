"""URLs de la app store: la API REST está montada en /api/."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import OrderViewSet, ProductViewSet

app_name = 'store'

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    # Cliente
    path('carrito/', views.carrito, name='carrito'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    # Administrador
    path('productos/', views.gestion_productos, name='gestion_productos'),
    path('pedidos/', views.gestion_pedidos, name='gestion_pedidos'),
    path('api/', include(router.urls)),
    # Clasificación de imágenes con Hugging Face
    path('api/clasificar/', views.ClasificarImagen.as_view(), name='api_clasificar'),
    # Página de clasificación
    path('clasificar/', views.pagina_clasificar, name='clasificar'),
]
