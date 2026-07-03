from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, filters
from .models import Documento, DocumentoFirma
from .serializers import DocumentoSerializer, DocumentoFirmaSerializer


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.filter(deleted_at__isnull=True).select_related('expediente', 'created_by', 'normativa_citada')
    serializer_class = DocumentoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre_original', 'expediente__numero_expediente']


class DocumentoFirmaViewSet(viewsets.ModelViewSet):
    queryset = DocumentoFirma.objects.filter(deleted_at__isnull=True)
    serializer_class = DocumentoFirmaSerializer


router = DefaultRouter()
router.register(r'documentos', DocumentoViewSet)
router.register(r'firmas', DocumentoFirmaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
