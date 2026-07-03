from django import forms
from .models import ModuloBiblioteca

class ModuloBibliotecaForm(forms.ModelForm):
    class Meta:
        model = ModuloBiblioteca
        exclude = ['deleted_at']
        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
        }
