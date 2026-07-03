import os

# Original expedientes/models.py
exp_models = '''"""
App: expedientes
Modelos del núcleo de negocio jurídico.
Cada modelo mapea fielmente el DDL del Plan Maestro.
"""
from django.db import models


class Personal(models.Model):
    """Personas vinculadas a expedientes (empleados, demandantes, etc.)."""
    numero_expediente = models.CharField(max_length=50, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(max_length=150, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personal'
        verbose_name_plural = 'Personal'
        ordering = ['-created_at']

    def get_full_name(self):
        return f"{self.nombres} {self.apellidos}"

    def __str__(self):
        return f"{self.cedula} - {self.get_full_name()}"


class Cargo(models.Model):
    """Clasificación laboral estricta: DOC, ADM, OBR."""
    CATEGORIAS = [
        ('DOC', 'Docente'),
        ('ADM', 'Administrativo'),
        ('OBR', 'Obrero'),
    ]
    TIPOS = [
        ('FIJ', 'Fijo / Carrera'),
        ('CON', 'Contratado'),
        ('CAR', 'Libre Nombramiento y Remoción'),
    ]

    categoria = models.CharField(max_length=3, choices=CATEGORIAS)
    tipo = models.CharField(max_length=3, choices=TIPOS)
    marco_legal = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargos'
        unique_together = ('categoria', 'tipo')
        ordering = ['categoria', 'tipo']

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.get_tipo_display()}"


class PersonaCargo(models.Model):
    """Relación persona-cargo con rango temporal."""
    personal = models.ForeignKey(Personal, on_delete=models.PROTECT, db_column='personal_id')
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, db_column='cargo_id')
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    es_cargo_actual = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'persona_cargo'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.personal} → {self.cargo}"


class Motivo(models.Model):
    """Catálogo de motivos asociables a expedientes."""
    descripcion = models.TextField()
    tipo = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'motivos'
        ordering = ['-created_at']

    def __str__(self):
        return self.descripcion[:80]


class Tribunal(models.Model):
    """Catálogo de tribunales y órganos jurisdiccionales."""
    TIPOS = [
        ('CONT', 'Contencioso'),
        ('INSP', 'Inspectoría del Trabajo'),
        ('OTRO', 'Otros'),
    ]

    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.CharField(max_length=4, choices=TIPOS)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tribunales'
        verbose_name_plural = 'Tribunales'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Expediente(models.Model):
    """
    Modelo maestro de expedientes jurídicos.
    El campo tipo_modulo determina a qué módulo operativo pertenece.
    """
    MODULOS = [
        ('DESP', 'Calificación de Despido / Recientes'),
        ('INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'),
        ('OFIC', 'Expedientes en Oficina Consultoría Jurídica'),
        ('CONT', 'Contrataciones y Convenios de la Universidad'),
        ('LITI', 'Litigios Judiciales y Administrativos'),
        ('SUST', 'Sustanciación de Procedimientos Disciplinarios'),
        ('IND', 'Índices de Inspectoría del Trabajo'),
    ]
    TEMAS = [
        ('LAB', 'Laboral'),
        ('ADM', 'Administrativo'),
        ('ACA', 'Académico'),
    ]
    FASES = [
        ('INICIO', 'Auto de Inicio'),
        ('PRUEBAS', 'Periodo Probatorio'),
        ('CONCL', 'Conclusiones / Dictamen'),
    ]
    ESTATUS_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('EN_ANALISIS', 'En Análisis'),
        ('FIRMA', 'En Firma'),
        ('DESPACHADO', 'Despachado'),
        ('ARCHIVADO', 'Archivado'),
    ]

    numero_expediente = models.CharField(max_length=50, unique=True)
    numero_expediente_relativo = models.CharField(max_length=50, blank=True, null=True)
    nombre_apellido = models.CharField(max_length=200, verbose_name="Nombre y Apellido")
    cedula = models.CharField(max_length=20, verbose_name="Cédula")
    tipo_modulo = models.CharField(max_length=4, choices=MODULOS)
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id'
    )
    personal = models.ForeignKey(
        Personal, on_delete=models.PROTECT, blank=True, null=True, db_column='personal_id'
    )
    motivo = models.ForeignKey(
        Motivo, on_delete=models.PROTECT, blank=True, null=True, db_column='motivo_id'
    )
    estatus = models.CharField(
        max_length=50, choices=ESTATUS_CHOICES, default='RECIBIDO', blank=True, null=True
    )
    fecha_registro = models.DateField(blank=True, null=True)
    tema_filtro = models.CharField(max_length=3, choices=TEMAS, blank=True, null=True)
    cargo = models.ForeignKey(
        Cargo, on_delete=models.PROTECT, blank=True, null=True, db_column='cargo_id'
    )
    # Campos específicos de Convenios (CONT)
    institucion = models.CharField(max_length=200, blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    duracion = models.CharField(max_length=100, blank=True, null=True)
    tipo_convenio = models.TextField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    # Campos específicos de Litigios (LITI)
    tipo_demanda = models.CharField(max_length=150, blank=True, null=True)
    tribunal = models.ForeignKey(
        Tribunal, on_delete=models.PROTECT, blank=True, null=True, db_column='tribunal_id'
    )
    # Campos específicos de Sustanciación (SUST)
    hora_procedimiento = models.TimeField(blank=True, null=True)
    lugar_procedimiento = models.CharField(max_length=255, blank=True, null=True)
    fase_actual = models.CharField(max_length=7, choices=FASES, blank=True, null=True)
    cronometro_limite = models.DateTimeField(blank=True, null=True)
    # Contadores
    documentos_procesados = models.IntegerField(default=0)
    correspondencia_recibida = models.IntegerField(default=0)
    correspondencia_enviada = models.IntegerField(default=0)
    # Soft delete
    is_archivado = models.BooleanField(default=False, db_column='is_archivado')
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expedientes'
        ordering = ['-created_at']

    def __str__(self):
        return f"EXP-{self.numero_expediente} ({self.get_tipo_modulo_display()})"


class Actuacion(models.Model):
    """Actuaciones procesales vinculadas a un expediente."""
    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, db_column='expediente_id'
    )
    descripcion = models.TextField()
    documento = models.ForeignKey(
        'documentos.Documento', on_delete=models.PROTECT,
        blank=True, null=True, db_column='documento_id'
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id'
    )
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actuaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f"Actuación en {self.expediente.numero_expediente}"


class AudienciaAgenda(models.Model):
    """Agenda de audiencias y eventos con alertas 30/60/90 días."""
    EVENTOS = [
        ('AUD', 'Audiencia Judicial'),
        ('LAPS', 'Lapso Procesal'),
        ('VENC', 'Vencimiento Contrato'),
        ('REC', 'Recordatorio General'),
    ]

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, db_column='expediente_id'
    )
    titulo = models.CharField(max_length=200)
    tipo_evento = models.CharField(max_length=4, choices=EVENTOS)
    fecha_hora = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    notificado_30 = models.BooleanField(default=False)
    notificado_60 = models.BooleanField(default=False)
    notificado_90 = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audiencias_agenda'
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.titulo} - {self.fecha_hora}"


class LitigioContraparte(models.Model):
    """Abogados de la contraparte en litigios."""
    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, db_column='expediente_id'
    )
    nombre_abogado = models.CharField(max_length=150)
    datos_contacto = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'litigios_contrapartes'

    def __str__(self):
        return self.nombre_abogado


class Notificacion(models.Model):
    """Notificaciones del sistema para los usuarios."""
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id'
    )
    mensaje = models.TextField()
    tipo_alerta = models.CharField(max_length=50)
    leido = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Notif: {self.mensaje[:50]}"


class SustanciacionNotificacion(models.Model):
    """Notificaciones formales de sustanciación disciplinaria."""
    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, db_column='expediente_id'
    )
    personal = models.ForeignKey(
        Personal, on_delete=models.PROTECT, db_column='personal_id'
    )
    fecha = models.DateField()
    hora = models.TimeField()
    lugar = models.CharField(max_length=255)
    firma_digital_path = models.CharField(max_length=255, blank=True, null=True)
    huella_digital_hash = models.CharField(max_length=64, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sustanciacion_notificaciones'

    def __str__(self):
        return f"Notif. Sust. - {self.personal}"
'''

bib_models = '''from django.db import models

class ModuloBiblioteca(models.Model):
    """Repositorio de normativa legal: reglamentos, gacetas, resoluciones."""
    TIPOS = [
        ('REGL', 'Reglamento Interno'),
        ('RESCU', 'Resolución de Consejo Universitario'),
        ('GAC', 'Gaceta Oficial'),
    ]

    titulo = models.CharField(max_length=255)
    tipo_normativa = models.CharField(max_length=5, choices=TIPOS)
    fecha_publicacion = models.DateField()
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modulo_biblioteca'
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo
'''

doc_models = '''"""
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
    tipo_mime = models.CharField(max_length=100)
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
    tipo_salida = models.CharField(max_length=4, choices=TIPOS_SALIDA, default='DOCX')
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
'''

with open('/home/matrix/SGEJ/apps/expedientes/models.py', 'w') as f:
    f.write(exp_models)

with open('/home/matrix/SGEJ/apps/biblioteca/models.py', 'w') as f:
    f.write(bib_models)

with open('/home/matrix/SGEJ/apps/documentos/models.py', 'w') as f:
    f.write(doc_models)
