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
        url_target = f"/documentos/{instance.pk}/" if hasattr(instance, 'pk') else "/documentos/"
        if instance.expediente and instance.expediente.usuario and instance.created_by != instance.expediente.usuario:
            desc = f"Nuevo documento en expediente {exp_num}: {instance.nombre_original}"
            NotificacionService.crear(
                usuario=instance.expediente.usuario,
                mensaje=desc,
                tipo_alerta='documento',
                url_destino=f"/expedientes/{instance.expediente.pk}/"
            )
        
        # Notificar a administradores (ojo de dios)
        from apps.usuarios.models import Usuario
        admins = Usuario.objects.filter(rol='ADMIN', is_active=True)
        autor = instance.created_by.usuario if instance.created_by else "Usuario"
        msg_admin = f"{autor} subió el documento '{instance.nombre_original}' (Exp: {exp_num})"
        for admin in admins:
            if instance.created_by and admin != instance.created_by:
                NotificacionService.crear(usuario=admin, mensaje=msg_admin, tipo_alerta='auditoria', url_destino=url_target)
