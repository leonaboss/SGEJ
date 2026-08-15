from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.usuarios.models import Usuario, BitacoraAuditoria
from apps.expedientes.services import NotificacionService

class Command(BaseCommand):
    help = 'Notifica a los usuarios por inactividad de 3 horas'

    def handle(self, *args, **options):
        tres_horas_atras = timezone.now() - timedelta(hours=3)
        usuarios_activos = Usuario.objects.filter(is_active=True)
        
        notificados = 0
        for usuario in usuarios_activos:
            # Buscar última actividad
            ultima_actividad = BitacoraAuditoria.objects.filter(usuario=usuario).order_by('-fecha_hora').first()
            
            # Si no ha tenido actividad o su última actividad fue hace más de 3 horas
            if not ultima_actividad or ultima_actividad.fecha_hora < tres_horas_atras:
                mensaje = "Has estado inactivo por más de 3 horas. Por seguridad, te recordamos cerrar sesión si no estás usando el sistema."
                NotificacionService.crear(usuario=usuario, mensaje=mensaje, tipo_alerta='alerta')
                notificados += 1
        
        self.stdout.write(self.style.SUCCESS(f'Se enviaron {notificados} notificaciones de inactividad.'))
