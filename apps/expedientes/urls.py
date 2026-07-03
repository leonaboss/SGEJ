from django.urls import path
from . import views

app_name = 'expedientes'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('api/dashboard/counts/', views.DashboardCountsAPIView.as_view(), name='api_dashboard_counts'),

    path('modulo/<str:tipo_modulo>/', views.ExpedienteModuloListView.as_view(), name='modulo_list'),
    path('expediente/<int:pk>/', views.ExpedienteDetailView.as_view(), name='expediente_detail'),
    path('expediente/crear/', views.ExpedienteCreateView.as_view(), name='expediente_create'),
    path('expediente/editar/<int:pk>/', views.ExpedienteUpdateView.as_view(), name='expediente_update'),
    path('expediente/eliminar/<int:pk>/', views.ExpedienteDeleteView.as_view(), name='expediente_delete'),
    path('expediente/<int:pk>/archivar/', views.ExpedienteArchivarView.as_view(), name='expediente_archivar'),
    path('expediente/<int:pk>/desarchivar/', views.ExpedienteDesarchivarView.as_view(), name='expediente_desarchivar'),

    path('actuaciones/', views.ActuacionListView.as_view(), name='actuacion_list'),
    path('actuaciones/editar/<int:pk>/', views.ActuacionUpdateView.as_view(), name='actuacion_update'),
    path('actuaciones/eliminar/<int:pk>/', views.ActuacionDeleteView.as_view(), name='actuacion_delete'),
    path('expediente/<int:expediente_pk>/actuacion/crear/', views.ActuacionCreateView.as_view(), name='actuacion_create'),
    path('expediente/<int:expediente_pk>/audiencia/crear/', views.AudienciaAgendaCreateView.as_view(), name='audiencia_create'),

    path('personal/', views.PersonalListView.as_view(), name='personal_list'),
    path('personal/crear/', views.PersonalCreateView.as_view(), name='personal_create'),
    path('personal/editar/<int:pk>/', views.PersonalUpdateView.as_view(), name='personal_update'),
    path('personal/eliminar/<int:pk>/', views.PersonalDeleteView.as_view(), name='personal_delete'),

    path('audiencias/', views.AudienciaAgendaListView.as_view(), name='audiencia_list'),
    path('audiencias/editar/<int:pk>/', views.AudienciaAgendaUpdateView.as_view(), name='audiencia_update'),
    path('audiencias/eliminar/<int:pk>/', views.AudienciaAgendaDeleteView.as_view(), name='audiencia_delete'),

    path('calendario/', views.CalendarioLapsosView.as_view(), name='calendario_lapsos'),
    path('calendario/eventos.json', views.CalendarioEventosJSONView.as_view(), name='calendario_eventos_json'),

    path('contrapartes/', views.LitigioContraparteListView.as_view(), name='litigiocontraparte_list'),
    path('contrapartes/crear/', views.LitigioContraparteCreateView.as_view(), name='litigiocontraparte_create'),
    path('contrapartes/editar/<int:pk>/', views.LitigioContraparteUpdateView.as_view(), name='litigiocontraparte_update'),
    path('contrapartes/eliminar/<int:pk>/', views.LitigioContraparteDeleteView.as_view(), name='litigiocontraparte_delete'),

    path('asignaciones/', views.PersonaCargoListView.as_view(), name='personacargo_list'),
    path('asignaciones/crear/', views.PersonaCargoCreateView.as_view(), name='personacargo_create'),
    path('asignaciones/editar/<int:pk>/', views.PersonaCargoUpdateView.as_view(), name='personacargo_update'),
    path('asignaciones/eliminar/<int:pk>/', views.PersonaCargoDeleteView.as_view(), name='personacargo_delete'),

    path('sustanciacion-notificaciones/', views.SustanciacionNotificacionListView.as_view(), name='sustanciacionnotificacion_list'),
    path('sustanciacion-notificaciones/crear/', views.SustanciacionNotificacionCreateView.as_view(), name='sustanciacionnotificacion_create'),
    path('sustanciacion-notificaciones/editar/<int:pk>/', views.SustanciacionNotificacionUpdateView.as_view(), name='sustanciacionnotificacion_update'),
    path('sustanciacion-notificaciones/eliminar/<int:pk>/', views.SustanciacionNotificacionDeleteView.as_view(), name='sustanciacionnotificacion_delete'),

    path('cargos/', views.CargoListView.as_view(), name='cargo_list'),
    path('cargos/crear/', views.CargoCreateView.as_view(), name='cargo_create'),
    path('cargos/editar/<int:pk>/', views.CargoUpdateView.as_view(), name='cargo_update'),
    path('cargos/eliminar/<int:pk>/', views.CargoDeleteView.as_view(), name='cargo_delete'),

    path('motivos/', views.MotivoListView.as_view(), name='motivo_list'),
    path('motivos/crear/', views.MotivoCreateView.as_view(), name='motivo_create'),
    path('motivos/editar/<int:pk>/', views.MotivoUpdateView.as_view(), name='motivo_update'),
    path('motivos/eliminar/<int:pk>/', views.MotivoDeleteView.as_view(), name='motivo_delete'),

    path('tribunales/', views.TribunalListView.as_view(), name='tribunal_list'),
    path('tribunales/crear/', views.TribunalCreateView.as_view(), name='tribunal_create'),
    path('tribunales/editar/<int:pk>/', views.TribunalUpdateView.as_view(), name='tribunal_update'),
    path('tribunales/eliminar/<int:pk>/', views.TribunalDeleteView.as_view(), name='tribunal_delete'),

    path('notificaciones/', views.NotificacionListView.as_view(), name='notificacion_list'),

    path('exportar/expedientes/', views.ExportarExpedientesExcelView.as_view(), name='exportar_expedientes'),
    path('exportar/personal/', views.ExportarPersonalExcelView.as_view(), name='exportar_personal'),
    path('exportar/cargos/', views.ExportarCargosExcelView.as_view(), name='exportar_cargos'),
    path('exportar/motivos/', views.ExportarMotivosExcelView.as_view(), name='exportar_motivos'),
    path('exportar/tribunales/', views.ExportarTribunalesExcelView.as_view(), name='exportar_tribunales'),
    path('exportar/asignaciones/', views.ExportarAsignacionesExcelView.as_view(), name='exportar_asignaciones'),
    path('exportar/audiencias/', views.ExportarAudienciasExcelView.as_view(), name='exportar_audiencias'),
    path('exportar/contrapartes/', views.ExportarLitigiosContraparteExcelView.as_view(), name='exportar_contrapartes'),
    path('exportar/sustanciacion-notificaciones/', views.ExportarSustanciacionNotificacionExcelView.as_view(), name='exportar_sustanciacion_notificaciones'),

    path('importar/<str:modelo>/', views.ImportarExcelView.as_view(), name='importar_excel'),

    path('notificacion/<int:pk>/marcar-leida/', views.NotificacionMarcarLeidaView.as_view(), name='notificacion_marcar_leida'),

    path('sujetos-procesales/', views.SujetoProcesalListView.as_view(), name='sujetoprocesal_list'),
    path('sujetos-procesales/crear/', views.SujetoProcesalCreateView.as_view(), name='sujetoprocesal_create'),
    path('sujetos-procesales/editar/<int:pk>/', views.SujetoProcesalUpdateView.as_view(), name='sujetoprocesal_update'),
    path('sujetos-procesales/eliminar/<int:pk>/', views.SujetoProcesalDeleteView.as_view(), name='sujetoprocesal_delete'),
    path('exportar/sujetos-procesales/', views.ExportarSujetosProcesalesExcelView.as_view(), name='exportar_sujetos_procesales'),
]
