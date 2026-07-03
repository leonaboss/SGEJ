from django.apps import AppConfig

class DocumentosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documentos'

    def ready(self):
        import apps.documentos.signals
