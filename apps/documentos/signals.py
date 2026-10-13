from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Documento
from apps.expedientes.services import NotificacionService
from apps.expedientes.models import Actuacion


@receiver(post_save, sender=Documento)
def registrar_actuacion_documento(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        exp_num = instance.expediente.numero_expediente if instance.expediente else "General"
        Actuacion.objects.create(
            content_object=instance,
            descripcion=f"Documento '{instance.nombre_original}' creado (Exp: {exp_num})",
            usuario=instance.created_by,
        )
        if instance.expediente and instance.expediente.usuario and instance.created_by != instance.expediente.usuario:
            desc = f"Nuevo documento en expediente {exp_num}: {instance.nombre_original}"
            NotificacionService.crear(
                usuario=instance.expediente.usuario,
                mensaje=desc,
                tipo_alerta='documento',
            )
