import random
import string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .models import Usuario, HistorialContrasena

class UsuarioService:
    VALID_ROLES = ['ADMIN', 'ABOG', 'USR_PUBLICO']

    @staticmethod
    def bloquear_usuario(usuario):
        usuario.is_bloqueado = True
        usuario.save(update_fields=['is_bloqueado'])

    @staticmethod
    def desbloquear_usuario(usuario):
        usuario.is_bloqueado = False
        usuario.intentos_fallidos = 0
        usuario.save(update_fields=['is_bloqueado', 'intentos_fallidos'])

    @staticmethod
    def generar_totp_secret():
        return get_random_string(length=32)

    @staticmethod
    def generar_password_temporal():
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(random.choice(chars) for _ in range(16))

    @staticmethod
    def enviar_correo_credenciales(usuario, password_temporal):
        if not usuario.correo:
            return False
        asunto = 'SGEJ - Credenciales de Acceso'
        mensaje = render_to_string('emails/credenciales.html', {
            'usuario': usuario,
            'password_temporal': password_temporal,
            'entorno': getattr(settings, 'ENTORNO', 'localhost'),
        })
        try:
            send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
            return True
        except Exception:
            return False
