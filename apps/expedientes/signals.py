from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Expediente, Actuacion, Notificacion
from .services import NotificacionService


@receiver(post_save, sender=Expediente)
def registrar_actuacion_expediente(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return

    if created:
        desc = f"Expediente {instance.numero_expediente} creado ({instance.get_tipo_modulo_display()})"
        Actuacion.objects.create(
            expediente=instance,
            descripcion=desc,
            usuario=instance.usuario,
        )
        return

    if not instance.pk:
        return

    try:
        old = Expediente.objects.get(pk=instance.pk)
    except Expediente.DoesNotExist:
        return

    cambios = []
    necesita_notificacion = False

    if old.is_archivado != instance.is_archivado:
        if instance.is_archivado:
            cambios.append("archivado")
        else:
            cambios.append("desarchivado")
        necesita_notificacion = True

    if old.deleted_at != instance.deleted_at and instance.deleted_at is not None:
        if not old.deleted_at and instance.deleted_at:
            cambios.append("eliminado (soft delete)")
            necesita_notificacion = True

    if old.estatus != instance.estatus and instance.estatus:
        cambios.append(f"estatus cambiado a '{instance.get_estatus_display()}'")
        necesita_notificacion = True

    if old.tribunal_id != instance.tribunal_id:
        cambios.append("tribunal modificado")

    if not cambios:
        campos = ['numero_expediente', 'personal_id', 'motivo_id', 'cargo_id',
                   'tema_filtro', 'fecha_registro', 'institucion', 'ano',
                   'duracion', 'tipo_convenio', 'fecha_vencimiento',
                   'tipo_demanda', 'fecha_demanda', 'hora_procedimiento',
                   'lugar_procedimiento', 'fase_actual', 'defensor_id',
                   'fiscal_id', 'juez_id', 'secretario_id']
        for c in campos:
            if getattr(old, c) != getattr(instance, c):
                cambios.append("editado")
                break

    if cambios:
        desc = f"Expediente {instance.numero_expediente}: {', '.join(cambios)}"
        Actuacion.objects.create(
            expediente=instance,
            descripcion=desc,
            usuario=instance.usuario,
        )
        if necesita_notificacion:
            NotificacionService.crear(
                usuario=instance.usuario,
                mensaje=desc,
                tipo_alerta='expediente',
            )


@receiver(post_save, sender=Actuacion)
def notificar_nueva_actuacion(sender, instance, created, **kwargs):
    if kwargs.get('raw', False) or not created:
        return
    if not instance.expediente or not instance.expediente.usuario:
        return
    if instance.usuario == instance.expediente.usuario:
        return
    desc = f"Nueva actuación en expediente {instance.expediente.numero_expediente}: {instance.descripcion[:80]}"
    NotificacionService.crear(
        usuario=instance.expediente.usuario,
        mensaje=desc,
        tipo_alerta='actuacion',
    )
