from rest_framework import viewsets, permissions, filters, mixins
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Personal, Cargo, PersonaCargo, Motivo, Tribunal, Expediente,
    Actuacion, AudienciaAgenda, LitigioContraparte, Notificacion,
    SustanciacionNotificacion, SujetoProcesal
)
from .serializers import (
    PersonalSerializer, CargoSerializer, PersonaCargoSerializer,
    MotivoSerializer, TribunalSerializer, ExpedienteListSerializer,
    ExpedienteDetalleSerializer, ActuacionSerializer,
    AudienciaAgendaSerializer, LitigioContraparteSerializer,
    NotificacionSerializer, SustanciacionNotificacionSerializer,
    SujetoProcesalSerializer
)


class PersonalViewSet(viewsets.ModelViewSet):
    queryset = Personal.objects.filter(deleted_at__isnull=True)
    serializer_class = PersonalSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nombres', 'apellidos', 'cedula', 'correo']


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.filter(deleted_at__isnull=True)
    serializer_class = CargoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoria', 'tipo']


class PersonaCargoViewSet(viewsets.ModelViewSet):
    queryset = PersonaCargo.objects.filter(deleted_at__isnull=True)
    serializer_class = PersonaCargoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['es_cargo_actual', 'personal', 'cargo']


class MotivoViewSet(viewsets.ModelViewSet):
    queryset = Motivo.objects.filter(deleted_at__isnull=True)
    serializer_class = MotivoSerializer
    search_fields = ['descripcion']


class TribunalViewSet(viewsets.ModelViewSet):
    queryset = Tribunal.objects.filter(deleted_at__isnull=True)
    serializer_class = TribunalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo']
    search_fields = ['nombre']


class ExpedienteViewSet(viewsets.ModelViewSet):
    queryset = Expediente.objects.filter(deleted_at__isnull=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_modulo', 'estatus', 'tema_filtro', 'fase_actual', 'is_archivado']
    search_fields = ['numero_expediente', 'personal__nombres', 'personal__apellidos', 'personal__cedula']
    ordering_fields = ['created_at', 'fecha_registro', 'numero_expediente']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExpedienteDetalleSerializer
        return ExpedienteListSerializer


class ActuacionViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Actuacion.objects.filter(deleted_at__isnull=True)
    serializer_class = ActuacionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['expediente', 'usuario']


class AudienciaAgendaViewSet(viewsets.ModelViewSet):
    queryset = AudienciaAgenda.objects.filter(deleted_at__isnull=True)
    serializer_class = AudienciaAgendaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['expediente', 'tipo_evento']


class LitigioContraparteViewSet(viewsets.ModelViewSet):
    queryset = LitigioContraparte.objects.filter(deleted_at__isnull=True)
    serializer_class = LitigioContraparteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['expediente']


class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.none()
    serializer_class = NotificacionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['leido', 'tipo_alerta']

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user, deleted_at__isnull=True)


class SustanciacionNotificacionViewSet(viewsets.ModelViewSet):
    queryset = SustanciacionNotificacion.objects.filter(deleted_at__isnull=True)
    serializer_class = SustanciacionNotificacionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['expediente', 'personal']


class SujetoProcesalViewSet(viewsets.ModelViewSet):
    queryset = SujetoProcesal.objects.filter(deleted_at__isnull=True)
    serializer_class = SujetoProcesalSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nombres', 'apellidos', 'cedula', 'correo']
    filterset_fields = ['tipo', 'tribunal']
