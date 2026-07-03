from rest_framework import serializers
from .models import ModuloBiblioteca

class ModuloBibliotecaSerializer(serializers.ModelSerializer):
    tipo_normativa_display = serializers.CharField(source='get_tipo_normativa_display', read_only=True)

    class Meta:
        model = ModuloBiblioteca
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
