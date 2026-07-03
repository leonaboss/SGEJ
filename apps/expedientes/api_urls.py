from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    PersonalViewSet, CargoViewSet,
    MotivoViewSet, TribunalViewSet, ExpedienteViewSet,
    ActuacionViewSet, AudienciaAgendaViewSet, LitigioContraparteViewSet,
    NotificacionViewSet, SustanciacionNotificacionViewSet,
    SujetoProcesalViewSet
)

router = DefaultRouter()
router.register(r'personal', PersonalViewSet)
router.register(r'cargos', CargoViewSet)
router.register(r'motivos', MotivoViewSet)
router.register(r'tribunales', TribunalViewSet)
router.register(r'expedientes', ExpedienteViewSet)
router.register(r'actuaciones', ActuacionViewSet)
router.register(r'audiencias', AudienciaAgendaViewSet)
router.register(r'contrapartes', LitigioContraparteViewSet)
router.register(r'notificaciones', NotificacionViewSet)
router.register(r'sustanciacion-notificaciones', SustanciacionNotificacionViewSet)
router.register(r'sujetos-procesales', SujetoProcesalViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
