from django.contrib import admin
from .models import Documento, DocumentoFirma, PlantillaDocumento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre_original', 'tipo_mime', 'version', 'created_by',
                    'expediente', 'es_plantilla', 'created_at']
    list_filter = ['tipo_mime', 'es_plantilla', 'created_at']
    search_fields = ['nombre_original', 'hash_sha256']
    readonly_fields = ['hash_sha256', 'iv_cifrado', 'qr_code_content']

@admin.register(DocumentoFirma)
class DocumentoFirmaAdmin(admin.ModelAdmin):
    list_display = ['documento', 'usuario', 'fecha_firma']
    list_filter = ['fecha_firma']
    search_fields = ['documento__nombre_original', 'usuario__usuario']

@admin.register(PlantillaDocumento)
class PlantillaDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_salida', 'created_by', 'created_at']
    list_filter = ['tipo_salida', 'created_at']
    search_fields = ['nombre', 'descripcion']
