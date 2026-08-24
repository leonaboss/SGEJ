from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Expediente, Actuacion, PersonaCargo
from apps.usuarios.models import Usuario
from .services import NotificacionService


@receiver(post_save, sender=Expediente)
def registrar_actuacion_expediente(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return

    # Automatización de PersonaCargo
    if instance.personal and instance.cargo:
        # Marcar cualquier cargo anterior como no actual
        PersonaCargo.objects.filter(
            personal=instance.personal, 
            es_cargo_actual=True
        ).exclude(cargo=instance.cargo).update(es_cargo_actual=False)
        
        # Crear o actualizar la asignación actual
        PersonaCargo.objects.get_or_create(
            personal=instance.personal,
            cargo=instance.cargo,
            defaults={'es_cargo_actual': True}
        )
        # Asegurarse de que si existe pero no estaba marcada como actual, se marque
        PersonaCargo.objects.filter(
            personal=instance.personal,
            cargo=instance.cargo
        ).update(es_cargo_actual=True)

    if created:
        desc = f"Expediente {instance.numero_expediente} creado ({instance.get_tipo_modulo_display()})"
        Actuacion.objects.create(
            content_object=instance,
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

    if old.fase_actual != instance.fase_actual and instance.fase_actual:
        cambios.append(f"fase actualizada a '{instance.get_fase_actual_display()}'")
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
            content_object=instance,
            descripcion=desc,
            usuario=instance.usuario,
        )
        
        # Notificar al dueño del expediente
        if necesita_notificacion:
            NotificacionService.crear(
                usuario=instance.usuario,
                mensaje=desc,
                tipo_alerta='expediente',
            )

        # Notificar a administradores con detalle del módulo
        from apps.usuarios.models import Usuario
        admins = Usuario.objects.filter(rol='ADMIN', is_active=True)
        modulo_nombre = instance.get_tipo_modulo_display()
        mensaje = f"{instance.usuario.usuario} {'creó' if created else 'editó'} el expediente {instance.numero_expediente} en el módulo de {modulo_nombre}"
        for admin in admins:
            if admin != instance.usuario:
                NotificacionService.crear(usuario=admin, mensaje=mensaje, tipo_alerta='auditoria')


@receiver(post_save, sender=Actuacion)
def notificar_nueva_actuacion(sender, instance, created, **kwargs):
    if kwargs.get('raw', False) or not created:
        return

    # 1. Notificar al usuario dueño del objeto si aplica
    expediente = None
    if instance.content_type and instance.content_type.model == 'expediente':
        expediente = instance.content_object
    
    if expediente and expediente.usuario and instance.usuario != expediente.usuario:
        desc = f"Nueva actuación en expediente {expediente.numero_expediente}: {instance.descripcion[:80]}"
        NotificacionService.crear(
            usuario=expediente.usuario,
            mensaje=desc,
            tipo_alerta='actuacion',
        )

    # 2. Notificar a todos los administradores sobre la actividad en 'expedientes'
    # Solo si el app_label es 'expedientes' y no es el módulo de administración
    if instance.content_type and instance.content_type.app_label == 'expedientes':
        admins = Usuario.objects.filter(rol='ADMIN', is_active=True)
        desc_admin = f"Actividad en {instance.content_type.model.title()}: {instance.descripcion[:80]}"
        for admin in admins:
            if admin != instance.usuario:
                NotificacionService.crear(
                    usuario=admin,
                    mensaje=desc_admin,
                    tipo_alerta='auditoria',
                )
