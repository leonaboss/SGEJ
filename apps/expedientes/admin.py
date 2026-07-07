from django.contrib import admin
from .models import (
    Personal, Cargo, PersonaCargo, Motivo, Tribunal, Expediente,
    Actuacion, AudienciaAgenda, LitigioContraparte, Notificacion,
    SustanciacionNotificacion, SujetoProcesal
)

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombres', 'apellidos', 'correo', 'telefono', 'created_at']
    search_fields = ['nombres', 'apellidos', 'cedula', 'correo']
    list_filter = ['created_at']

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['categoria', 'tipo', 'marco_legal']
    list_filter = ['categoria', 'tipo']

@admin.register(PersonaCargo)
class PersonaCargoAdmin(admin.ModelAdmin):
    list_display = ['personal', 'cargo', 'fecha_inicio', 'fecha_fin', 'es_cargo_actual']
    list_filter = ['es_cargo_actual']

@admin.register(Motivo)
class MotivoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'tipo']
    search_fields = ['descripcion']

@admin.register(Tribunal)
class TribunalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo']
    list_filter = ['tipo']
    search_fields = ['nombre']

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ['numero_expediente', 'tipo_modulo', 'estatus', 'personal',
                    'usuario', 'is_archivado', 'created_at']
    list_filter = ['tipo_modulo', 'estatus', 'is_archivado', 'tema_filtro']
    search_fields = ['numero_expediente', 'personal__nombres', 'personal__apellidos']
    date_hierarchy = 'created_at'

@admin.register(Actuacion)
class ActuacionAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'usuario', 'created_at']
    list_filter = ['created_at']
    search_fields = ['descripcion']

@admin.register(AudienciaAgenda)
class AudienciaAgendaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_evento', 'fecha_hora', 'expediente']
    list_filter = ['tipo_evento', 'fecha_hora']
    search_fields = ['titulo', 'expediente__numero_expediente']

@admin.register(LitigioContraparte)
class LitigioContraparteAdmin(admin.ModelAdmin):
    list_display = ['nombre_abogado', 'expediente', 'es_abogado']
    list_filter = ['es_abogado']
    search_fields = ['nombre_abogado']

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'mensaje', 'tipo_alerta', 'leido', 'fecha_creacion']
    list_filter = ['leido', 'tipo_alerta']

@admin.register(SustanciacionNotificacion)
class SustanciacionNotificacionAdmin(admin.ModelAdmin):
    list_display = ['expediente', 'personal', 'fecha', 'hora', 'lugar']
    list_filter = ['fecha']

@admin.register(SujetoProcesal)
class SujetoProcesalAdmin(admin.ModelAdmin):
    list_display = ['nombres', 'apellidos', 'tipo', 'cedula', 'telefono', 'correo', 'tribunal']
    list_filter = ['tipo', 'tribunal']
    search_fields = ['nombres', 'cedula', 'correo']
