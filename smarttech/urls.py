"""
URL configuration for smarttech project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Login / logout / reset de contraseñas de django.contrib.auth
    path('accounts/', include('django.contrib.auth.urls')),
    # URLs de la tienda (store)
    path('', include('store.urls')),
]

# En modo DEBUG, sirve los archivos subidos en MEDIA_ROOT
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
