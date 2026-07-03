"""
App: expedientes
Modelos del núcleo de negocio jurídico.
Cada modelo mapea fielmente el DDL del Plan Maestro.
"""
from django.db import models


class SujetoProcesal(models.Model):
    """Directorio parametrizado de sujetos procesales."""
    class TipoSujeto(models.TextChoices):
        DEFENSOR = 'DEF', 'Defensor'
        FISCAL = 'FIS', 'Fiscal de Control'
        JUEZ = 'JUE', 'Juez de la Causa'
        SECRETARIO = 'SEC', 'Secretario Judicial'
        CONTRAPARTE = 'CON', 'Contraparte'

    tipo = models.CharField(max_length=3, choices=TipoSujeto.choices, verbose_name='Tipo')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    correo = models.EmailField(max_length=150, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    tribunal = models.TextField(
        choices=[('CONT', 'Contencioso'), ('INSP', 'Inspectoría del Trabajo'), ('OTRO', 'Otros')],
        blank=True, null=True, verbose_name='Tribunal asociado'
    )
    observaciones = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sujetos_procesales'
        verbose_name = 'Sujeto Procesal'
        verbose_name_plural = 'Sujetos Procesales'
        ordering = ['tipo', 'apellidos', 'nombres']

    def get_full_name(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.get_full_name()}"


class Personal(models.Model):
    """Personas vinculadas a expedientes (empleados, demandantes, etc.)."""
    numero_expediente = models.CharField(max_length=50, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(max_length=150, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    cargo = models.ForeignKey(
        'Cargo', on_delete=models.PROTECT, blank=True, null=True, db_column='cargo_id'
    )
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
    class CategoriaChoices(models.TextChoices):
        DOC = 'DOC', 'Docente'
        ADM = 'ADM', 'Administrativo'
        OBR = 'OBR', 'Obrero'

    class TipoCargoChoices(models.TextChoices):
        FIJ = 'FIJ', 'Fijo / Carrera'
        CON = 'CON', 'Contratado'
        CAR = 'CAR', 'Libre Nombramiento y Remoción'

    categoria = models.CharField(max_length=3, choices=CategoriaChoices.choices)
    tipo = models.TextField(choices=TipoCargoChoices.choices)
    marco_legal = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargos'
        ordering = ['categoria']

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
    class TipoTribunalChoices(models.TextChoices):
        CONT = 'CONT', 'Contencioso'
        INSP = 'INSP', 'Inspectoría del Trabajo'
        OTRO = 'OTRO', 'Otros'

    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.TextField(choices=TipoTribunalChoices.choices)
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
    class ModuloChoices(models.TextChoices):
        DESP = 'DESP', 'Calificación de Despido / Recientes'
        INSP = 'INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'
        OFIC = 'OFIC', 'Expedientes en Oficina Consultoría Jurídica'
        CONT = 'CONT', 'Contrataciones y Convenios de la Universidad'
        LITI = 'LITI', 'Litigios Judiciales y Administrativos'
        SUST = 'SUST', 'Sustanciación de Procedimientos Disciplinarios'
        IND = 'IND', 'Índices de Inspectoría del Trabajo'

    class TemaFiltroEnum(models.TextChoices):
        LAB = 'LAB', 'Laboral'
        ADM = 'ADM', 'Administrativo'
        ACA = 'ACA', 'Académico'

    class FaseChoices(models.TextChoices):
        INICIO = 'INICIO', 'Auto de Inicio'
        PRUEBAS = 'PRUEBAS', 'Periodo Probatorio'
        CONCL = 'CONCL', 'Conclusiones / Dictamen'

    class EstatusChoices(models.TextChoices):
        RECIBIDO = 'RECIBIDO', 'Recibido'
        EN_ANALISIS = 'EN_ANALISIS', 'En Análisis'
        FIRMA = 'FIRMA', 'En Firma'
        DESPACHADO = 'DESPACHADO', 'Despachado'
        ARCHIVADO = 'ARCHIVADO', 'Archivado'

    numero_expediente = models.CharField(max_length=50, unique=True)
    numero_expediente_relativo = models.CharField(max_length=50, blank=True, null=True)
    cedula = models.CharField(max_length=20, verbose_name="Cédula")
    tipo_modulo = models.TextField(choices=ModuloChoices.choices)
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.PROTECT, db_column='usuario_id'
    )
    personal = models.ForeignKey(
        Personal, on_delete=models.PROTECT, db_column='personal_id'
    )
    motivo = models.ForeignKey(
        Motivo, on_delete=models.PROTECT, blank=True, null=True, db_column='motivo_id'
    )
    estatus = models.CharField(
        max_length=50, choices=EstatusChoices.choices, default=EstatusChoices.RECIBIDO, blank=True, null=True
    )
    fecha_registro = models.DateField(blank=True, null=True)
    tema_filtro = models.TextField(choices=TemaFiltroEnum.choices, blank=True, null=True)
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
    tipo_demanda = models.TextField(blank=True, null=True)
    fecha_demanda = models.DateField(blank=True, null=True, verbose_name="Fecha de Demanda")
    tribunal = models.ForeignKey(
        Tribunal, on_delete=models.PROTECT, blank=True, null=True, db_column='tribunal_id'
    )
    # Campos específicos de Sustanciación (SUST)
    hora_procedimiento = models.TimeField(blank=True, null=True)
    lugar_procedimiento = models.CharField(max_length=255, blank=True, null=True)
    fase_actual = models.TextField(choices=FaseChoices.choices, blank=True, null=True)
    cronometro_limite = models.DateTimeField(blank=True, null=True)
    firma_digital_hash = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Firma Digital (SHA-256)',
        help_text='Hash SHA-256 que certifica la notificación.'
    )
    huella_digital_hash = models.CharField(
        max_length=64, blank=True, null=True,
        verbose_name='Huella Digital (SHA-256)'
    )
    # Sujetos procesales vinculados
    defensor = models.ForeignKey(
        SujetoProcesal, on_delete=models.PROTECT, blank=True, null=True,
        db_column='defensor_id', related_name='expedientes_defensor',
        verbose_name='Defensor'
    )
    fiscal = models.ForeignKey(
        SujetoProcesal, on_delete=models.PROTECT, blank=True, null=True,
        db_column='fiscal_id', related_name='expedientes_fiscal',
        verbose_name='Fiscal de Control'
    )
    juez = models.ForeignKey(
        SujetoProcesal, on_delete=models.PROTECT, blank=True, null=True,
        db_column='juez_id', related_name='expedientes_juez',
        verbose_name='Juez de la Causa'
    )
    secretario = models.ForeignKey(
        SujetoProcesal, on_delete=models.PROTECT, blank=True, null=True,
        db_column='secretario_id', related_name='expedientes_secretario',
        verbose_name='Secretario Judicial'
    )
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
    class EventoChoices(models.TextChoices):
        AUD = 'AUD', 'Audiencia Judicial'
        LAPS = 'LAPS', 'Lapso Procesal'
        VENC = 'VENC', 'Vencimiento Contrato'
        REC = 'REC', 'Recordatorio General'

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, db_column='expediente_id'
    )
    titulo = models.CharField(max_length=200)
    tipo_evento = models.TextField(choices=EventoChoices.choices)
    fecha_hora = models.DateTimeField()
    lugar = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, blank=True, null=True,
        db_column='usuario_id', verbose_name='Abogado asignado'
    )
    alerta_email = models.BooleanField(default=True, verbose_name='Notificar por correo')
    alerta_sms = models.BooleanField(default=False, verbose_name='Notificar por SMS')
    notificado_email = models.BooleanField(default=False)
    notificado_sms = models.BooleanField(default=False)
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
    es_abogado = models.BooleanField(default=True, verbose_name='Es abogado')
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
    tipo_alerta = models.TextField()
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
    firma_digital_hash = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name='Firma Digital (SHA-256)',
        help_text='Hash SHA-256 de la notificación registrada.'
    )
    huella_digital_hash = models.CharField(max_length=64, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sustanciacion_notificaciones'

    def __str__(self):
        return f"Notif. Sust. - {self.personal}"
