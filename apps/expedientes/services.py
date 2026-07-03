import logging
import openpyxl
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Expediente, AudienciaAgenda, Notificacion

logger = logging.getLogger(__name__)


class AlertasService:
    """Gestión de alertas por correo electrónico y SMS para la agenda procesal."""

    @staticmethod
    def enviar_alerta_email(evento):
        """Envía alerta por correo al abogado asignado."""
        if not evento.usuario or not evento.usuario.correo:
            logger.warning(f'Evento {evento.pk}: sin abogado o correo asignado.')
            return False
        if evento.notificado_email:
            return False

        asunto = f'⏰ Alerta Procesal: {evento.titulo}'
        mensaje = render_to_string('emails/alerta_agenda.html', {
            'evento': evento,
            'dias_restantes': (evento.fecha_hora.date() - timezone.now().date()).days,
        })
        try:
            send_mail(
                asunto, mensaje, settings.DEFAULT_FROM_EMAIL,
                [evento.usuario.correo], fail_silently=False,
                html_message=mensaje,
            )
            evento.notificado_email = True
            evento.save(update_fields=['notificado_email'])
            logger.info(f'Alerta email enviada a {evento.usuario.correo} para evento {evento.pk}')
            return True
        except Exception as e:
            logger.error(f'Error enviando email a {evento.usuario.correo}: {e}')
            return False

    @staticmethod
    def enviar_alerta_sms(evento):
        """Envía alerta SMS al teléfono del abogado asignado."""
        if not evento.usuario or not evento.usuario.telefono:
            logger.warning(f'Evento {evento.pk}: sin abogado o teléfono asignado.')
            return False
        if evento.notificado_sms:
            return False
        if not evento.alerta_sms:
            return False

        telefono = evento.usuario.telefono
        mensaje = (
            f'SGEJ - Alerta Procesal: {evento.titulo}\n'
            f'Fecha: {evento.fecha_hora.strftime("%d/%m/%Y %H:%M")}\n'
            f'Expediente: {evento.expediente.numero_expediente}'
        )
        try:
            gateway = getattr(settings, 'SMS_GATEWAY', None)
            if gateway == 'twilio':
                from twilio.rest import Client
                client = Client(
                    settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                )
                client.messages.create(
                    body=mensaje, from_=settings.TWILIO_FROM_NUMBER, to=telefono
                )
            elif gateway == 'whatsapp':
                import requests
                requests.post(
                    f'https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_ID}/messages',
                    json={
                        'messaging_product': 'whatsapp',
                        'to': telefono,
                        'type': 'text',
                        'text': {'body': mensaje},
                    },
                    headers={'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}'},
                )
            else:
                logger.info(f'[SMS Gateway - Consola] Para: {telefono} | Mensaje: {mensaje[:60]}...')

            evento.notificado_sms = True
            evento.save(update_fields=['notificado_sms'])
            logger.info(f'Alerta SMS enviada a {telefono} para evento {evento.pk}')
            return True
        except Exception as e:
            logger.error(f'Error enviando SMS a {telefono}: {e}')
            return False

    @classmethod
    def verificar_y_notificar(cls):
        """Verifica eventos próximos y envía alertas según configuración."""
        hoy = timezone.now().date()
        umbrales = {30: 'notificado_30', 60: 'notificado_60', 90: 'notificado_90'}
        resultados = {'email': 0, 'sms': 0}

        for dias, flag in umbrales.items():
            fecha_limite = hoy + timezone.timedelta(days=dias)
            eventos = AudienciaAgenda.objects.filter(
                deleted_at__isnull=True,
                fecha_hora__date=fecha_limite,
                **{flag: False},
            ).select_related('usuario', 'expediente')

            for evento in eventos:
                if evento.alerta_email:
                    if cls.enviar_alerta_email(evento):
                        resultados['email'] += 1
                if evento.alerta_sms:
                    if cls.enviar_alerta_sms(evento):
                        resultados['sms'] += 1
                setattr(evento, flag, True)
                evento.save(update_fields=[flag])

        return resultados


class NotificacionService:
    """Gestión de notificaciones in-app del sistema."""

    @staticmethod
    def crear(usuario, mensaje, tipo_alerta='info'):
        """Crea una notificación para un usuario."""
        if not usuario or not usuario.pk:
            return None
        return Notificacion.objects.create(
            usuario=usuario,
            mensaje=mensaje,
            tipo_alerta=tipo_alerta,
        )


class ExportacionService:
    @staticmethod
    def exportar_expedientes_excel(queryset=None):
        if queryset is None:
            queryset = Expediente.objects.filter(deleted_at__isnull=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Expedientes'
        encabezados = ['N° Expediente', 'Módulo', 'Estatus', 'Personal', 'Cédula',
                       'Motivo', 'Fecha Registro', 'Fase', 'Archivado']
        ws.append(encabezados)
        for exp in queryset.select_related('personal', 'motivo'):
            ws.append([
                exp.numero_expediente,
                exp.get_tipo_modulo_display(),
                exp.get_estatus_display(),
                exp.personal.get_full_name() if exp.personal else '-',
                exp.personal.cedula if exp.personal else '-',
                str(exp.motivo) if exp.motivo else '-',
                exp.fecha_registro,
                exp.get_fase_actual_display() if exp.fase_actual else '-',
                'Sí' if exp.is_archivado else 'No',
            ])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=expedientes_{timezone.now().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        return response

    @staticmethod
    def exportar_audiencias_excel(queryset=None):
        if queryset is None:
            queryset = AudienciaAgenda.objects.filter(deleted_at__isnull=True)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Audiencias'
        encabezados = ['Título', 'Tipo Evento', 'Fecha/Hora', 'Expediente', 'Descripción']
        ws.append(encabezados)
        for aud in queryset.select_related('expediente'):
            ws.append([
                aud.titulo,
                aud.get_tipo_evento_display(),
                aud.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                aud.expediente.numero_expediente,
                aud.descripcion,
            ])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=audiencias_{timezone.now().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        return response
