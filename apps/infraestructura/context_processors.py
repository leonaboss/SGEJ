from apps.expedientes.models import Notificacion


def notificaciones_count(request):
    if request.user.is_authenticated:
        count = Notificacion.objects.filter(
            usuario=request.user, leido=False, deleted_at__isnull=True
        ).count()
        return {'notificaciones_count': count}
    return {}
