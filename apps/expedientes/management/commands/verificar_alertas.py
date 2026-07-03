"""Management command para verificar y enviar alertas de la agenda procesal.
Ejecutar vía cron diariamente:
  0 8 * * * /ruta/venv/bin/python /ruta/manage.py verificar_alertas
"""
from django.core.management.base import BaseCommand
from apps.expedientes.services import AlertasService


class Command(BaseCommand):
    help = 'Verifica eventos próximos en la agenda y envía alertas (email/SMS).'

    def handle(self, *args, **options):
        resultados = AlertasService.verificar_y_notificar()
        self.stdout.write(
            self.style.SUCCESS(
                f'Alertas enviadas: {resultados["email"]} email(s), {resultados["sms"]} SMS(s)'
            )
        )
