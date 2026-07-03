import os

exp_path = '/home/matrix/SGEJ/apps/expedientes/models.py'
bib_path = '/home/matrix/SGEJ/apps/biblioteca/models.py'
doc_path = '/home/matrix/SGEJ/apps/documentos/models.py'

with open(exp_path, 'r') as f:
    exp_content = f.read()

# Make the changes in expedientes/models.py
exp_content = exp_content.replace(
    "categoria = models.CharField(max_length=3, choices=CATEGORIAS)\n    tipo = models.CharField(max_length=3, choices=TIPOS)",
    "categoria = models.CharField(max_length=3, choices=CATEGORIAS)\n    tipo = models.TextField(choices=TIPOS)"
)

exp_content = exp_content.replace(
    "nombre = models.CharField(max_length=150, unique=True)\n    tipo = models.CharField(max_length=4, choices=TIPOS)",
    "nombre = models.CharField(max_length=150, unique=True)\n    tipo = models.TextField(choices=TIPOS)"
)

modulo_model = '''class Modulo(models.Model):
    """Módulos del sistema segmentados."""
    class NombreModulo(models.TextChoices):
        DESP = 'DESP', 'Calificación de Despido / Recientes'
        INSP = 'INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'
        OFIC = 'OFIC', 'Expedientes en Oficina Consultoría Jurídica'
        CONT = 'CONT', 'Contrataciones y Convenios de la Universidad'
        LITI = 'LITI', 'Litigios Judiciales y Administrativos'
        SUST = 'SUST', 'Sustanciación de Procedimientos Disciplinarios'
        IND = 'IND', 'Índices de Inspectoría del Trabajo'

    nombre = models.TextField(choices=NombreModulo.choices, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'modulos'
        verbose_name_plural = 'Módulos'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_nombre_display()


class Expediente(models.Model):'''

exp_content = exp_content.replace("class Expediente(models.Model):", modulo_model)

exp_content = exp_content.replace(
    '''    MODULOS = [
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
    ]''',
    '''    class TemaFiltroEnum(models.TextChoices):
        LAB = 'LAB', 'Laboral'
        ADM = 'ADM', 'Administrativo'
        ACA = 'ACA', 'Académico'
'''
)

exp_content = exp_content.replace(
    "tipo_modulo = models.CharField(max_length=4, choices=MODULOS)",
    "modulo = models.ForeignKey(Modulo, on_delete=models.PROTECT, db_column='modulo_id')"
)

exp_content = exp_content.replace(
    "tema_filtro = models.CharField(max_length=3, choices=TEMAS, blank=True, null=True)",
    "tema_filtro = models.TextField(choices=TemaFiltroEnum.choices, blank=True, null=True)"
)

exp_content = exp_content.replace(
    "tipo_demanda = models.CharField(max_length=150, blank=True, null=True)",
    "tipo_demanda = models.TextField(blank=True, null=True)"
)

exp_content = exp_content.replace(
    'return f"EXP-{self.numero_expediente} ({self.get_tipo_modulo_display()})"',
    'return f"EXP-{self.numero_expediente} ({self.modulo})"'
)

exp_content = exp_content.replace(
    "tipo_evento = models.CharField(max_length=4, choices=EVENTOS)",
    "tipo_evento = models.TextField(choices=EVENTOS)"
)

# Update the comment
exp_content = exp_content.replace("El campo tipo_modulo determina", "El campo modulo determina")

with open(exp_path, 'w') as f:
    f.write(exp_content)

# biblioteca
with open(bib_path, 'r') as f:
    bib_content = f.read()

bib_content = bib_content.replace(
    "tipo_normativa = models.CharField(max_length=5, choices=TIPOS)",
    "tipo_normativa = models.TextField(choices=TIPOS)"
)
with open(bib_path, 'w') as f:
    f.write(bib_content)

# documentos
with open(doc_path, 'r') as f:
    doc_content = f.read()

doc_content = doc_content.replace(
    "tipo_salida = models.CharField(max_length=4, choices=TIPOS_SALIDA, default='DOCX')",
    "tipo_salida = models.TextField(choices=TIPOS_SALIDA, default='DOCX')"
)
with open(doc_path, 'w') as f:
    f.write(doc_content)
