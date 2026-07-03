import hashlib
import json
import logging
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache, caches
from django.http import HttpResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeo de rutas a acciones descriptivas
# ---------------------------------------------------------------------------
ACCIONES_POR_RUTA = {
    'recovery': 'RECUPERACION_CONTRASENA',
    'cambiar-password': 'CAMBIO_CONTRASENA',
    'register': 'REGISTRO_USUARIO',
    'unarchive': 'DESARCHIVADO',
    'archive': 'ARCHIVADO',
    'create': 'CREACION',
    'update': 'EDICION',
    'edit': 'EDICION',
    'delete': 'ELIMINACION',
    'toggle-bloqueo': 'BLOQUEO_USUARIO',
    'export': 'EXPORTACION',
    'import': 'IMPORTACION',
    'upload': 'SUBIDA',
    'download': 'DESCARGA',
    'generar': 'GENERACION',
    'preview': 'PREVISUALIZACION',
}


def _extraer_ip(request):
    """Extrae la IP real del request (soporta proxies)."""
    return request.META.get(
        'HTTP_X_FORWARDED_FOR',
        request.META.get('REMOTE_ADDR', '0.0.0.0')
    ).split(',')[0].strip()


def _determinar_accion(request):
    """Determina la acción humana basada en la ruta."""
    path_lower = request.path.lower()
    for keyword, accion in ACCIONES_POR_RUTA.items():
        if keyword in path_lower:
            return accion
    method_map = {
        'POST': 'CREACION',
        'PUT': 'EDICION',
        'PATCH': 'EDICION',
        'DELETE': 'ELIMINACION',
        'GET': 'CONSULTA',
    }
    return method_map.get(request.method, request.method)


def _determinar_modulo(request):
    """Extrae el módulo (app_name) o asigna uno por ruta."""
    from django.urls import resolve, Resolver404
    try:
        match = resolve(request.path_info)
        return match.app_name.upper() if match.app_name else 'CORE'
    except Resolver404:
        pass
    # Fallback por palabras clave en la ruta
    path = request.path.lower()
    if '/auth/' in path:
        return 'AUTH'
    if '/expedientes/' in path:
        return 'EXPEDIENTES'
    if '/documentos/' in path:
        return 'DOCUMENTOS'
    if '/biblioteca/' in path:
        return 'BIBLIOTECA'
    if '/usuarios/' in path:
        return 'USUARIOS'
    return 'CORE'


# ---------------------------------------------------------------------------
# Generación de descripciones en lenguaje natural
# ---------------------------------------------------------------------------
DESCRIPCIONES_POR_ACCION = {
    'RECUPERACION_CONTRASENA': 'Recuperación de contraseña',
    'CAMBIO_CONTRASENA': 'Cambio de contraseña',
    'REGISTRO_USUARIO': 'Registro de usuario',
    'CREACION': 'Creación de registro',
    'EDICION': 'Edición de registro',
    'ELIMINACION': 'Eliminación de registro',
    'ARCHIVADO': 'Archivado de expediente',
    'DESARCHIVADO': 'Desarchivado de expediente',
    'BLOQUEO_USUARIO': 'Bloqueo/desbloqueo de usuario',
    'EXPORTACION': 'Exportación de datos',
    'IMPORTACION': 'Importación de datos',
    'SUBIDA': 'Subida de archivo',
    'DESCARGA': 'Descarga de archivo',
    'GENERACION': 'Generación de documento',
    'PREVISUALIZACION': 'Previsualización de documento',
    'CONSULTA': 'Consulta de información',
}


def _generar_descripcion(request, accion):
    return DESCRIPCIONES_POR_ACCION.get(accion, f"Operación {request.method}")


# ---------------------------------------------------------------------------
# Detección de anomalías
# ---------------------------------------------------------------------------
CACHE_IPS = caches['session_control'] if 'session_control' in caches else cache


def _detectar_anomalias(request, usuario, ip, accion):
    """
    Analiza el contexto de la operación y devuelve una lista de alertas
    (strings cortos) si detecta actividad inusual.
    """
    alertas = []

    if not usuario:
        # Operación anónima en ruta no-auth: extraño
        if 'login' not in request.path.lower() and 'recovery' not in request.path.lower():
            alertas.append('ANONIMO_EN_RUTA_PROTEGIDA')
        return alertas

    hora_actual = datetime.now().hour

    # 1. Horario inusual (10pm - 6am)
    if hora_actual < 6 or hora_actual >= 22:
        alertas.append('HORARIO_INUSUAL')

    # 2. IP diferente al último registro del usuario
    if accion == 'INICIO_SESION':
        last_ip_key = f'audit_last_ip:usuario:{usuario.id}'
        last_ip = CACHE_IPS.get(last_ip_key)
        if last_ip and last_ip != ip:
            alertas.append('IP_DIFERENTE')
        # Guardar IP actual para futuras comparaciones
        CACHE_IPS.set(last_ip_key, ip, 86400 * 30)  # 30 días

    # 3. Actividad rápida sucesiva (más de X operaciones en 1 minuto)
    rapid_key = f'audit_rapid:ip:{ip}'
    rapid_count = CACHE_IPS.get(rapid_key, 0) + 1
    CACHE_IPS.set(rapid_key, rapid_count, 60)
    if rapid_count > 20:
        alertas.append('ACTIVIDAD_RAPIDA')

    # 4. Múltiples operaciones de eliminación
    if accion == 'ELIMINACION':
        del_key = f'audit_deletes:user:{usuario.id}'
        del_count = CACHE_IPS.get(del_key, 0) + 1
        CACHE_IPS.set(del_key, del_count, 300)  # 5 min ventana
        if del_count >= 5:
            alertas.append('ELIMINACIONES_MASIVAS')

    return alertas


# ---------------------------------------------------------------------------
# Rate Limit Middleware
# ---------------------------------------------------------------------------
class RateLimitMiddleware:
    """
    Middleware de rate limiting para prevenir ataques de fuerza bruta.
    Permite máximo 20 requests/minuto por IP en rutas sensibles.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('POST',) and any(p in request.path for p in ['/auth/login', '/auth/recovery']):
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            cache_key = f'ratelimit:{ip}'
            count = cache.get(cache_key, 0)
            if count >= 20:
                response = HttpResponse(
                    json.dumps({'error': 'Demasiadas solicitudes. Intente más tarde.'}),
                    content_type='application/json',
                    status=429
                )
                return response
            cache.set(cache_key, count + 1, 60)
        return self.get_response(request)


# ---------------------------------------------------------------------------
# Session Control Middleware
# ---------------------------------------------------------------------------
class SessionControlMiddleware:
    """
    Middleware que detecta inicios de sesión concurrentes.
    Usa DatabaseCache (compartido entre workers) para almacenar
    la sesión activa de cada usuario. Si un usuario inicia sesión
    desde otro navegador/dispositivo, invalida la sesión anterior.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        sc_cache = caches['session_control']
        if request.user.is_authenticated:
            session_key = request.session.session_key
            expected_key = sc_cache.get(f'session_control:{request.user.id}')
            if expected_key and expected_key != session_key:
                from django.contrib.auth import logout
                logout(request)
                return redirect('/auth/login/')
        response = self.get_response(request)
        if request.user.is_authenticated and request.session.session_key:
            sc_cache.set(f'session_control:{request.user.id}', request.session.session_key, 86400)
        return response


# ---------------------------------------------------------------------------
# Auditoría Inmutable Middleware
# ---------------------------------------------------------------------------
class AuditoriaInmutableMiddleware:
    """
    Middleware de auditoría inmutable con hash SHA-256 encadenados.
    Registra TODA acción del usuario en el sistema, detecta actividad
    inusual, y marca alertas de seguridad como IP diferente, horario
    extraño, eliminaciones masivas, etc.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._audit_tracked = False
        request._audit_skip = getattr(request, '_audit_skip', False)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            request._audit_tracked = True
        response = self.get_response(request)
        if request._audit_tracked and not request._audit_skip and response.status_code in (200, 201, 302):
            self._registrar_bitacora(request, response)
        return response

    def _registrar_bitacora(self, request, response):
        from apps.usuarios.models import BitacoraAuditoria

        try:
            usuario = request.user if request.user.is_authenticated else None
            ip = _extraer_ip(request)
            accion = _determinar_accion(request)
            modulo = _determinar_modulo(request)
            descripcion = _generar_descripcion(request, accion)

            # Detectar anomalías
            alertas = _detectar_anomalias(request, usuario, ip, accion)
            tipo = ','.join(alertas) if alertas else ''

            with transaction.atomic():
                ultimo_log = (
                    BitacoraAuditoria.objects.select_for_update()
                    .order_by('-id').first()
                )
                prev_hash = ultimo_log.hash_integridad if ultimo_log else "GENESIS_HASH"

                raw_string = (
                    f"{prev_hash}|{usuario.id if usuario else 'ANON'}|"
                    f"{accion}|{modulo}|{ip}|{descripcion}"
                )
                hash_integridad = hashlib.sha256(
                    raw_string.encode('utf-8')
                ).hexdigest()

                BitacoraAuditoria.objects.create(
                    usuario=usuario,
                    fecha_hora=timezone.now(),
                    accion=accion,
                    tipo=tipo,
                    descripcion=descripcion,
                    modulo=modulo,
                    ip_address=ip,
                    hash_integridad=hash_integridad,
                )


        except Exception as e:
            logger.error(f"Error en bitácora de auditoría: {e}")
