import random
import string
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .models import Usuario, HistorialContrasena

def enviar_correo_seguro(asunto, mensaje, destinatarios, html_mensaje=None):
    resend_api_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_api_key:
        url = 'https://api.resend.com/emails'
        headers = {
            'Authorization': f'Bearer {resend_api_key}',
            'Content-Type': 'application/json'
        }
        remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'onboarding@resend.dev')
        if not remitente or '@' not in remitente or 'uptag.edu.ve' in remitente:
            remitente = 'onboarding@resend.dev'
        
        payload = {
            'from': remitente,
            'to': list(destinatarios),
            'subject': asunto,
            'html': html_mensaje if html_mensaje else f"<pre>{mensaje}</pre>",
            'text': mensaje
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return True
        else:
            raise Exception(f"Resend API error: {response.status_code} - {response.text}")
    else:
        remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@uptag.edu.ve')
        send_mail(
            asunto,
            mensaje,
            remitente,
            list(destinatarios),
            fail_silently=False,
            html_message=html_mensaje
        )
        return True


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
            enviar_correo_seguro(asunto, mensaje, [usuario.correo], html_mensaje=mensaje)
            return True
        except Exception:
            return False
