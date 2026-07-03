from django.contrib import admin
from .models import ModuloBiblioteca

@admin.register(ModuloBiblioteca)
class ModuloBibliotecaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_normativa', 'fecha_publicacion', 'created_at']
    list_filter = ['tipo_normativa', 'fecha_publicacion']
    search_fields = ['titulo']
