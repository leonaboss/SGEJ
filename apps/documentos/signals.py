from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Documento
from apps.expedientes.services import NotificacionService


@receiver(post_save, sender=Documento)
def notificar_nuevo_documento(sender, instance, created, **kwargs):
    if kwargs.get('raw', False) or not created:
        return
    if not instance.expediente or not instance.expediente.usuario:
        return
    if instance.created_by == instance.expediente.usuario:
        return
    desc = f"Nuevo documento en expediente {instance.expediente.numero_expediente}: {instance.nombre_original}"
    NotificacionService.crear(
        usuario=instance.expediente.usuario,
        mensaje=desc,
        tipo_alerta='documento',
    )
