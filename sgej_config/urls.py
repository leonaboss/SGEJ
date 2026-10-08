from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import Http404
import os
import qrcode

def serve_media_with_fallback(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # Auto-regenerate QR code if missing on disk (ephemeral storage on Render)
    if path.startswith('qrs/QR_') and not os.path.exists(file_path):
        filename = os.path.basename(path)
        if filename.startswith('QR_') and filename.endswith('.png'):
            hash_sha256 = filename[3:-4]
            try:
                from apps.documentos.models import Documento
                doc = Documento.objects.filter(hash_sha256=hash_sha256).first()
                if doc:
                    qr_data = doc.qr_code_content or f"SGIJ-EXPEDIENTE:{doc.expediente.numero_expediente}|HASH:{hash_sha256}"
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="black", back_color="white")
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    img_qr.save(file_path)
            except Exception:
                pass

    if os.path.exists(file_path):
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    raise Http404("Archivo no encontrado.")

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
    re_path(r'^media/(?P<path>.*)$', serve_media_with_fallback),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'django.views.defaults.permission_denied'
