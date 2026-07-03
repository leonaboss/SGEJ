from rest_framework import viewsets, filters
from .models import ModuloBiblioteca
from .serializers import ModuloBibliotecaSerializer

class ModuloBibliotecaViewSet(viewsets.ModelViewSet):
    queryset = ModuloBiblioteca.objects.filter(deleted_at__isnull=True)
    serializer_class = ModuloBibliotecaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'tipo_normativa']
    ordering_fields = ['fecha_publicacion', 'created_at']