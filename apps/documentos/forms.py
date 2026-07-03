import os
from django import forms
from apps.expedientes.models import Expediente
from .models import Documento, PlantillaDocumento

MAGIC_NUMBERS = {
    b'%PDF': 'application/pdf',
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'PK\x03\x04': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'}


class DocumentoUploadForm(forms.Form):
    expediente = forms.ModelChoiceField(
        queryset=Expediente.objects.filter(deleted_at__isnull=True),
        required=True, label='Expediente'
    )
    archivo = forms.FileField(
        label='Archivo',
        help_text='Formatos permitidos: PDF, DOC, DOCX, JPG, PNG, JPEG'
    )
    tipo = forms.ChoiceField(
        choices=[('DOC', 'Documento'), ('PLANTILLA', 'Plantilla')],
        required=True, label='Tipo',
        initial='DOC',
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if archivo.size > MAX_FILE_SIZE:
            raise forms.ValidationError('El archivo no puede superar los 50MB.')

        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(f'Extensión "{ext}" no permitida.')

        archivo.seek(0)
        header = archivo.read(32)
        archivo.seek(0)

        matched = False
        for magic, mime in MAGIC_NUMBERS.items():
            if header.startswith(magic):
                matched = True
                break
        if not matched:
            if header.startswith(b'\xd0\xcf\x11\xe0'):
                matched = True
            elif header.startswith(b'wORD') or header.startswith(b'\xef\xbb\xbf'):
                matched = True

        if not matched:
            raise forms.ValidationError('El tipo de archivo real no coincide con la extensión.')

        return archivo

class DocumentoUpdateForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nombre_original', 'expediente', 'biblioteca', 'es_plantilla', 'normativa_citada']


class PlantillaForm(forms.ModelForm):
    class Meta:
        model = PlantillaDocumento
        fields = ['nombre', 'descripcion', 'archivo_plantilla', 'tipo_salida']
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_salida': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control'})
        self.fields['archivo_plantilla'].widget.attrs.update({'class': 'form-control'})
        self.fields['archivo_plantilla'].help_text = 'Archivo .docx con placeholders en formato {{variable}}'
