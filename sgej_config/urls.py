from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.expedientes.urls', namespace='expedientes')),
    path('auth/', include('apps.usuarios.urls', namespace='usuarios')),
    path('documentos/', include('apps.documentos.urls', namespace='documentos')),
    path('biblioteca/', include('apps.biblioteca.urls', namespace='biblioteca')),
    path('api/', include('apps.expedientes.api_urls')),
    path('api/auth/', include('apps.usuarios.api_urls')),
    path('api/documentos/', include('apps.documentos.api_urls')),
    path('api/biblioteca/', include('apps.biblioteca.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
