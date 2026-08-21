from django.db import models
from apps.expedientes.models import BaseManager

class ModuloBiblioteca(models.Model):
    objects = BaseManager()
    """Repositorio de normativa legal: reglamentos, gacetas, resoluciones."""
    class ModuloChoices(models.TextChoices):
        DESP = 'DESP', 'Calificación de Despido / Recientes'
        INSP = 'INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'
        OFIC = 'OFIC', 'Expedientes en Oficina Consultoría Jurídica'
        CONT = 'CONT', 'Contrataciones y Convenios de la Universidad'
        LITI = 'LITI', 'Litigios Judiciales y Administrativos'
        SUST = 'SUST', 'Sustanciación de Procedimientos Disciplinarios'
        IND = 'IND', 'Índices de Inspectoría del Trabajo'

    TIPOS = [
        ('REGL', 'Reglamento Interno'),
        ('RESCU', 'Resolución de Consejo Universitario'),
        ('GAC', 'Gaceta Oficial'),
    ]

    modulo = models.TextField(choices=ModuloChoices.choices, blank=True, null=True)
    titulo = models.CharField(max_length=255)
    tipo_normativa = models.TextField(choices=TIPOS)
    fecha_publicacion = models.DateField()
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.CASCADE, db_column='usuario_id',
        null=True, blank=True, verbose_name='Usuario creador'
    )
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modulo_biblioteca'
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo
