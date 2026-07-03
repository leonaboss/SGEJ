"""
App: documentos
Modelos para gestión de archivos cifrados, firmas y QRs.
"""
from django.db import models


class Documento(models.Model):
    """Documento cifrado at-rest con hash SHA-256 de integridad."""
    expediente = models.ForeignKey(
        'expedientes.Expediente', on_delete=models.PROTECT,
        blank=True, null=True, db_column='expediente_id'
    )
    biblioteca = models.ForeignKey(
        'biblioteca.ModuloBiblioteca', on_delete=models.PROTECT,
        blank=True, null=True, db_column='biblioteca_id'
    )
    nombre_original = models.CharField(max_length=255)
    nombre_cifrado = models.CharField(max_length=255)
    tipo_mime = models.TextField()
    hash_sha256 = models.CharField(max_length=64)
    iv_cifrado = models.CharField(max_length=512)
    qr_code_content = models.CharField(max_length=255, unique=True, blank=True, null=True)
    contenido_ocr = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1)
    parent_documento = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True,
        db_column='parent_documento_id'
    )
    normativa_citada = models.ForeignKey(
        'biblioteca.ModuloBiblioteca', on_delete=models.PROTECT,
        blank=True, null=True, related_name='citado_en_documentos',
        db_column='normativa_citada_id'
    )
    es_plantilla = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='created_by'
    )

    class Meta:
        db_table = 'documentos'
        ordering = ['-created_at']

    def __str__(self):
        return self.nombre_original


class DocumentoFirma(models.Model):
    """Firma digital de documentos por usuarios autorizados."""
    documento = models.ForeignKey(
        Documento, on_delete=models.PROTECT, db_column='documento_id'
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id'
    )
    hash_firma = models.CharField(max_length=64)
    sello_digital_path = models.CharField(max_length=255, blank=True, null=True)
    fecha_firma = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'documentos_firmas'
        unique_together = ('documento', 'usuario')

    def __str__(self):
        return f"Firma: {self.usuario} → {self.documento}"


class PlantillaDocumento(models.Model):
    """Plantilla para generación automática de documentos."""
    TIPOS_SALIDA = [
        ('DOCX', 'Word (.docx)'),
        ('PDF', 'PDF'),
    ]
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    archivo_plantilla = models.FileField(
        upload_to='plantillas/',
        help_text='Archivo .docx con placeholders {{variable}}'
    )
    tipo_salida = models.TextField(choices=TIPOS_SALIDA, default='DOCX')
    variables = models.JSONField(
        default=list, blank=True,
        help_text='Lista de variables disponibles: [{"nombre": "var1", "etiqueta": "Var 1", "tipo": "text"}]'
    )
    created_by = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='created_by'
    )
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plantillas_documentos'
        ordering = ['-created_at']

    def __str__(self):
        return self.nombre
