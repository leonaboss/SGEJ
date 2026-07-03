import hashlib
import logging
from datetime import datetime
from django.db import transaction
from django.db.models.signals import pre_save
from django.contrib.auth.signals import user_login_failed, user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from apps.usuarios.models import Usuario, HistorialContrasena, BitacoraAuditoria

logger = logging.getLogger(__name__)

# Cache for anomaly detection (shared across workers)
from django.core.cache import caches, cache
CACHE_ANOM = caches['session_control'] if 'session_control' in caches else cache


def _extraer_ip(request):
    return request.META.get(
        'HTTP_X_FORWARDED_FOR',
        request.META.get('REMOTE_ADDR', '0.0.0.0')
    ).split(',')[0].strip()


def _detectar_anomalias_auth(usuario, ip, accion, descripcion):
    """
    Detecta anomalías en eventos de autenticación.
    Retorna lista de alertas.
    """
    alertas = []
    hora_actual = datetime.now().hour

    # Horario inusual
    if hora_actual < 6 or hora_actual >= 22:
        alertas.append('HORARIO_INUSUAL')

    if accion == 'INICIO_SESION' and usuario:
        # IP diferente a la conocida
        last_ip_key = f'audit_last_ip:usuario:{usuario.id}'
        last_ip = CACHE_ANOM.get(last_ip_key)
        if last_ip and last_ip != ip:
            alertas.append('IP_DIFERENTE')
        CACHE_ANOM.set(last_ip_key, ip, 86400 * 30)

    if accion == 'INICIO_SESION_FALLIDO':
        # Múltiples fallos desde misma IP
        fail_key = f'audit_failures:ip:{ip}'
        fail_count = CACHE_ANOM.get(fail_key, 0) + 1
        CACHE_ANOM.set(fail_key, fail_count, 300)  # 5 min ventana
        if fail_count >= 5:
            alertas.append('MULTIPLES_FALLOS')
        if fail_count >= 15:
            alertas.append('POSIBLE_FUERZA_BRUTA')

    return alertas


def _registrar_en_bitacora(usuario, accion, modulo, descripcion, ip_address):
    """Helper para insertar un registro en la bitácora desde signals."""
    try:
        alertas = _detectar_anomalias_auth(usuario, ip_address, accion, descripcion)
        tipo = ','.join(alertas) if alertas else ''

        with transaction.atomic():
            ultimo = (
                BitacoraAuditoria.objects.select_for_update()
                .order_by('-id').first()
            )
            prev_hash = ultimo.hash_integridad if ultimo else "GENESIS_HASH"
            raw = (
                f"{prev_hash}|{usuario.id if usuario else 'ANON'}|"
                f"{accion}|{modulo}|{ip_address}|{descripcion}"
            )
            hash_integridad = hashlib.sha256(raw.encode('utf-8')).hexdigest()
            BitacoraAuditoria.objects.create(
                usuario=usuario,
                fecha_hora=timezone.now(),
                accion=accion,
                tipo=tipo,
                descripcion=descripcion,
                modulo=modulo,
                ip_address=ip_address,
                hash_integridad=hash_integridad,
            )
    except Exception as e:
        logger.error(f"Error registrando bitácora desde signal: {e}")


@receiver(user_logged_in)
def registrar_inicio_sesion(sender, request, user, **kwargs):
    request._audit_skip = True
    ip = _extraer_ip(request)
    _registrar_en_bitacora(
        usuario=user,
        accion='INICIO_SESION',
        modulo='AUTH',
        descripcion=f"Inicio de sesión: {user.usuario}",
        ip_address=ip,
    )


@receiver(user_logged_out)
def registrar_cierre_sesion(sender, request, user, **kwargs):
    if not user:
        return
    request._audit_skip = True
    ip = _extraer_ip(request)
    _registrar_en_bitacora(
        usuario=user,
        accion='CIERRE_SESION',
        modulo='AUTH',
        descripcion=f"Cierre de sesión: {user.usuario}",
        ip_address=ip,
    )


@receiver(user_login_failed)
def registrar_intento_fallo(sender, credentials, request, **kwargs):
    request._audit_skip = True
    username_tried = credentials.get('usuario', credentials.get('username', 'DESCONOCIDO'))
    ip = _extraer_ip(request)
    _registrar_en_bitacora(
        usuario=None,
        accion='INICIO_SESION_FALLIDO',
        modulo='AUTH',
        descripcion=f"Intento de inicio de sesión fallido para: {username_tried}",
        ip_address=ip,
    )


@receiver(pre_save, sender=Usuario)
def verificar_politica_y_guardar_historial(sender, instance, **kwargs):
    if instance.id:
        usuario_db = Usuario.objects.get(id=instance.id)
        if usuario_db.password != instance.password:
            historial = HistorialContrasena.objects.filter(usuario=instance).order_by('-created_at')[:3]
            if hasattr(instance, '_password_plana_temporal'):
                for h in historial:
                    if check_password(instance._password_plana_temporal, h.password_hash):
                        raise ValueError("No puedes reutilizar ninguna de tus últimas 3 contraseñas.")
            HistorialContrasena.objects.create(
                usuario=instance,
                password_hash=usuario_db.password
            )


@receiver(pre_save, sender=Usuario)
def registrar_cambio_contrasena(sender, instance, **kwargs):
    if not instance.id:
        return
    try:
        old = Usuario.objects.get(id=instance.id)
        if old.password != instance.password:
            _registrar_en_bitacora(
                usuario=instance,
                accion='CAMBIO_CONTRASENA',
                modulo='AUTH',
                descripcion=f"Cambio de contraseña: {instance.usuario}",
                ip_address='0.0.0.0',
            )
    except Usuario.DoesNotExist:
        pass
