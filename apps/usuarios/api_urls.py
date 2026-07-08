from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, permissions, filters
from .models import Usuario, BitacoraAuditoria
from .serializers import UsuarioSerializer, UsuarioCreateSerializer, BitacoraAuditoriaSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.filter(deleted_at__isnull=True)
    filter_backends = [filters.SearchFilter]
    search_fields = ['usuario', 'cedula', 'correo', 'personal__nombres', 'personal__apellidos']

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer


class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BitacoraAuditoria.objects.all()
    serializer_class = BitacoraAuditoriaSerializer
    permission_classes = [permissions.IsAdminUser]
    ordering = ['-created_at']


router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'bitacora', BitacoraViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
