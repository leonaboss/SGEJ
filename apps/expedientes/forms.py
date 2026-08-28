import hashlib
import re
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Personal, Cargo, PersonaCargo, Motivo, Tribunal, Expediente,
    Actuacion, AudienciaAgenda, LitigioContraparte, SustanciacionNotificacion,
    SujetoProcesal
)
from apps.usuarios.models import Usuario

# --- Validaciones / Helpers ---
def validate_text_only(value):
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value.strip()):
        raise ValidationError('El campo solo debe contener letras y espacios.')

def validate_alphanumeric_text(value):
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s\.\,\-]+$', value.strip()):
        raise ValidationError('El campo contiene caracteres no permitidos.')

# --- Mixins de Validación ---
class PersonalValidationMixin:
    def clean_nombre_completo(self):
        value = self.cleaned_data.get('nombre_completo', '').strip()
        if not value or ' ' not in value:
            raise forms.ValidationError('Debe ingresar Nombres y Apellidos separados por un espacio.')
        return value

    def save_personal(self, instance):
        nombre_completo = self.cleaned_data.get('nombre_completo', '')
        if not nombre_completo: return
        parts = nombre_completo.split(' ', 1)
        nombres = parts[0]
        apellidos = parts[1] if len(parts) > 1 else ''
        cedula = (self.cleaned_data.get('cedula') or '').strip() or None
        
        if not nombres:
            return
        if not cedula:
            import hashlib
            raw = f"{nombres}|{apellidos}|{timezone.now().isoformat()}"
            cedula = f"TMP-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"
        
        personal = Personal.objects.filter(cedula=cedula, deleted_at__isnull=True).first()
        if not personal:
            personal = Personal.objects.filter(
                nombres=nombres, apellidos=apellidos, deleted_at__isnull=True
            ).first()
        if not personal:
            personal = Personal.objects.create(cedula=cedula, nombres=nombres, apellidos=apellidos)
        elif cedula and not personal.cedula.startswith('TMP-') and personal.cedula != cedula:
            personal.cedula = cedula
            personal.save(update_fields=['cedula'])
        instance.personal = personal

class CargoValidationMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'cargo' in self.fields:
            # Ya configuramos el campo como ModelChoiceField en BaseExpedienteForm
            # solo necesitamos asegurar el widget y etiquetas si es necesario
            self.fields['cargo'].widget = forms.Select(attrs={'class': 'form-select'})
            self.fields['cargo'].label = 'Cargo'
            self.fields['cargo'].required = False
            self.fields['cargo'].empty_label = 'Seleccione un cargo'

    def clean_cargo(self):
        return self.cleaned_data.get('cargo')
    
    def save_cargo(self, instance):
        if 'cargo' in self.cleaned_data and self.cleaned_data['cargo']:
            instance.cargo = self.cleaned_data['cargo']

class MotivoValidationMixin:
    def clean_motivo(self):
        if 'motivo' not in self.fields: return None
        value = self.cleaned_data.get('motivo')
        if not value: return None
        validate_alphanumeric_text(value)
        value = value.strip()
        motivo, _ = Motivo.objects.get_or_create(descripcion=value, defaults={'tipo': ''})
        return motivo
    
    def save_motivo(self, instance):
        if 'motivo' in self.cleaned_data and self.cleaned_data['motivo']: instance.motivo = self.cleaned_data['motivo']

class TribunalValidationMixin:
    def clean_tribunal(self):
        if 'tribunal' not in self.fields: return None
        value = self.cleaned_data.get('tribunal')
        if not value: return None
        if isinstance(value, Tribunal):
            return value
        validate_alphanumeric_text(value)
        value = value.strip()
        # El tribunal_tipo ya no se obtiene del form, se define por defecto o si se tiene de otra fuente
        tribunal, _ = Tribunal.objects.get_or_create(nombre=value, defaults={'tipo': 'OTRO'})
        return tribunal
    
    def save_tribunal(self, instance):
        if 'tribunal' in self.cleaned_data and self.cleaned_data['tribunal']: instance.tribunal = self.cleaned_data['tribunal']

# --- Base Form ---
class BaseExpedienteForm(forms.ModelForm):
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(deleted_at__isnull=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cargo',
        required=False,
        empty_label='Seleccione un cargo'
    )
    nombre_completo = forms.CharField(
        max_length=200, 
        label='Nombres y Apellidos', 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez'}),
        required=False
    )
    motivo = forms.CharField(
        max_length=255,
        label='Motivo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el motivo aquí'}),
        required=False
    )
    class Meta:
        model = Expediente
        exclude = ['deleted_at', 'created_at', 'updated_at', 'firma_digital_hash', 'huella_digital_hash', 'defensor', 'fiscal', 'juez', 'secretario', 'documentos_procesados', 'correspondencia_recibida', 'correspondencia_enviada', 'is_archivado', 'personal', 'tipo_modulo', 'nombre_completo', 'cargo']
        widgets = {
            'fecha_registro': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_demanda': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_procedimiento': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'cronometro_limite': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
        labels = {
            'numero_expediente': 'N° Expediente',
            'numero_expediente_relativo': 'N° Exp. Relativo',
            'cedula': 'Cédula',
            'estatus': 'Estatus',
            'fecha_registro': 'Fecha Registro',
            'fecha_demanda': 'Fecha de Demanda',
            'tribunal': 'Tribunal',
            'fase_actual': 'Fase',
            'cronometro_limite': 'Cronómetro Legal',
            'motivo': 'Motivo',
            'institucion': 'Institución',
            'ano': 'Año',
            'duracion': 'Duración',
            'tipo_convenio': 'Tipo de Convenio',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'tipo_demanda': 'Tipo de Demanda',
            'hora_procedimiento': 'Hora',
            'lugar_procedimiento': 'Lugar',
            'nombre_completo': 'Nombres y Apellidos',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.personal:
                self.initial['nombre_completo'] = self.instance.personal.get_full_name()
            if self.instance.motivo:
                self.initial['motivo'] = self.instance.motivo.descripcion
            if self.instance.cargo:
                self.initial['cargo'] = self.instance.cargo
        if hasattr(self, 'fields_order'):
            self.order_fields(self.fields_order)
    
    def clean_numero_expediente(self):
        # Solo validar si el campo es parte del formulario activo
        if 'numero_expediente' not in self.fields:
            return None
        value = self.cleaned_data.get('numero_expediente', '').strip()
        if not value: raise forms.ValidationError('El número de expediente es obligatorio.')
        return value

# --- Specialized Forms ---
class DespidoExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, MotivoValidationMixin, CargoValidationMixin):
    fields_order = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'estatus']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'estatus']
    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_motivo(instance)
        self.save_cargo(instance)
        if commit: instance.save()
        return instance

class InspectoriaExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, MotivoValidationMixin, CargoValidationMixin):
    fields_order = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'fecha_registro']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'fecha_registro']
    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_motivo(instance)
        self.save_cargo(instance)
        if commit: instance.save()
        return instance

class OficinaExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, CargoValidationMixin, MotivoValidationMixin):
    fields_order = ['numero_expediente', 'numero_expediente_relativo', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'estatus']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['numero_expediente', 'numero_expediente_relativo', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'estatus']
    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_cargo(instance)
        self.save_motivo(instance)
        if commit: instance.save()
        return instance

class ConvenioExpedienteForm(BaseExpedienteForm):
    numero_expediente = forms.CharField(
        max_length=50,
        label='N° de Convenio / Contrato',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CONV-2026-0001'}),
        required=True
    )
    fields_order = ['numero_expediente', 'institucion', 'ano', 'duracion', 'tipo_convenio', 'fecha_vencimiento']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['numero_expediente', 'institucion', 'ano', 'duracion', 'tipo_convenio', 'fecha_vencimiento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'motivo' in self.fields:
            del self.fields['motivo']
        if 'nombre_completo' in self.fields:
            del self.fields['nombre_completo']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.numero_expediente:
            import uuid
            instance.numero_expediente = f"CONT-{uuid.uuid4().hex[:8].upper()}"
        if commit:
            instance.save()
        return instance

class LitigioExpedienteForm(BaseExpedienteForm, TribunalValidationMixin):
    tipo_demanda = forms.CharField(
        max_length=255,
        label='Tipo de Demanda',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Demanda Laboral'}),
        required=True
    )
    tribunal = forms.CharField(
        max_length=255,
        label='Tribunal',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tribunal Supremo de Justicia'}),
        required=False
    )
    numero_expediente = forms.CharField(
        max_length=50,
        label='N° de Litigio',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: LITI-2026-0001'}),
        required=False,
        help_text='Si se deja vacío se genera automáticamente.'
    )
    fields_order = ['tipo_demanda', 'fecha_demanda', 'estatus', 'tribunal', 'numero_expediente']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['tipo_demanda', 'fecha_demanda', 'estatus', 'tribunal', 'numero_expediente']
    def clean_numero_expediente(self):
        value = self.cleaned_data.get('numero_expediente', '').strip()
        return value or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'motivo' in self.fields:
            del self.fields['motivo']
        if 'nombre_completo' in self.fields:
            del self.fields['nombre_completo']

    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_tribunal(instance)
        if not instance.numero_expediente:
            import uuid
            instance.numero_expediente = f"LITI-{uuid.uuid4().hex[:8].upper()}"
        if commit: instance.save()
        return instance

class SustanciacionExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, MotivoValidationMixin, CargoValidationMixin):
    fields_order = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'fecha_registro', 'hora_procedimiento', 'lugar_procedimiento', 'firma_digital_hash', 'huella_digital_hash', 'fase_actual', 'cronometro_limite', 'estatus']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['numero_expediente', 'nombre_completo', 'cedula', 'cargo', 'motivo', 'fecha_registro', 'hora_procedimiento', 'lugar_procedimiento', 'firma_digital_hash', 'huella_digital_hash', 'fase_actual', 'cronometro_limite', 'estatus']
        exclude = []
        labels = {
            **BaseExpedienteForm.Meta.labels,
            'fecha_registro': 'Fecha Notif.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aseguramos que los campos de hash estén presentes si no estaban
        if 'firma_digital_hash' not in self.fields:
            self.fields['firma_digital_hash'] = forms.CharField(required=False)
        if 'huella_digital_hash' not in self.fields:
            self.fields['huella_digital_hash'] = forms.CharField(required=False)
            
        self.fields['firma_digital_hash'].widget.attrs.update({'class': 'form-control font-monospace', 'readonly': True})
        self.fields['huella_digital_hash'].widget.attrs.update({'class': 'form-control font-monospace', 'readonly': True})
        self.fields['firma_digital_hash'].label = 'Firma (SHA-256)'
        self.fields['huella_digital_hash'].label = 'Huella'

    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_motivo(instance)
        self.save_cargo(instance)
        # Lógica de generación de hashes
        raw_firma = f"{instance.numero_expediente}|{instance.cedula}|{instance.personal.get_full_name() if instance.personal_id else ''}|{timezone.now().isoformat()}"
        instance.firma_digital_hash = hashlib.sha256(raw_firma.encode()).hexdigest()
        raw_huella = f"{instance.personal.get_full_name() if instance.personal_id else ''}|{instance.cedula}|{timezone.now().isoformat()}|{instance.numero_expediente}"
        instance.huella_digital_hash = hashlib.sha256(raw_huella.encode()).hexdigest()
        if commit: instance.save()
        return instance

class IndiceExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, MotivoValidationMixin, CargoValidationMixin):
    fields_order = ['nombre_completo', 'cedula', 'numero_expediente', 'cargo', 'motivo']
    class Meta(BaseExpedienteForm.Meta):
        fields = ['nombre_completo', 'cedula', 'numero_expediente', 'cargo', 'motivo']
    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_motivo(instance)
        self.save_cargo(instance)
        if commit: instance.save()
        return instance

class GeneralExpedienteForm(BaseExpedienteForm, PersonalValidationMixin, CargoValidationMixin, MotivoValidationMixin, TribunalValidationMixin):
    tribunal = forms.CharField(
        max_length=255,
        label='Tribunal',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tribunal Supremo de Justicia'}),
        required=False
    )
    class Meta(BaseExpedienteForm.Meta):
        fields = '__all__'
    def save(self, commit=True):
        instance = super().save(commit=False)
        self.save_personal(instance)
        self.save_cargo(instance)
        self.save_motivo(instance)
        self.save_tribunal(instance)
        if commit: instance.save()
        return instance

# Map for the views to use
FORM_FACTORY = {
    'DESP': DespidoExpedienteForm,
    'INSP': InspectoriaExpedienteForm,
    'OFIC': OficinaExpedienteForm,
    'CONT': ConvenioExpedienteForm,
    'LITI': LitigioExpedienteForm,
    'SUST': SustanciacionExpedienteForm,
    'IND': IndiceExpedienteForm,
    'DEFAULT': GeneralExpedienteForm
}

# --- Supporting Forms ---
class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        exclude = ['deleted_at']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_nombres(self):
        value = self.cleaned_data.get('nombres')
        validate_text_only(value)
        return value

    def clean_apellidos(self):
        value = self.cleaned_data.get('apellidos')
        validate_text_only(value)
        return value

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        exclude = ['deleted_at']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_descripcion(self):
        value = self.cleaned_data.get('descripcion')
        if value:
            validate_alphanumeric_text(value)
        return value

class MotivoForm(forms.ModelForm):
    class Meta:
        model = Motivo
        exclude = ['deleted_at']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Administrativo, Legal'}),
        }

    def clean_descripcion(self):
        value = self.cleaned_data.get('descripcion')
        if value:
            validate_alphanumeric_text(value)
        return value

    def clean_tipo(self):
        value = self.cleaned_data.get('tipo')
        if value:
            validate_alphanumeric_text(value)
        return value

class TribunalForm(forms.ModelForm):
    class Meta:
        model = Tribunal
        exclude = ['deleted_at']

    def clean_nombre(self):
        value = self.cleaned_data.get('nombre')
        if value:
            validate_alphanumeric_text(value)
        return value

class ActuacionForm(forms.ModelForm):
    class Meta:
        model = Actuacion
        exclude = ['deleted_at']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class AudienciaAgendaForm(forms.ModelForm):
    class Meta:
        model = AudienciaAgenda
        exclude = ['deleted_at']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'lugar': forms.TextInput(attrs={'placeholder': 'Ej: Juzgado 1° de Primera Instancia'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuario = self.fields.get('usuario')
        if usuario:
            usuario.widget = forms.Select(attrs={'class': 'form-select'})
            usuario.label = 'Abogado Asignado'
            usuario.required = False
            usuario.queryset = Usuario.objects.filter(
                rol='ABOG', deleted_at__isnull=True, is_active=True
            ).select_related('personal')
            usuario.choices = [(u.pk, f'{u.get_full_name()} ({u.usuario})') for u in usuario.queryset]

class LitigioContraparteForm(forms.ModelForm):
    class Meta:
        model = LitigioContraparte
        exclude = ['deleted_at']
        widgets = {
            'datos_contacto': forms.Textarea(attrs={'rows': 3}),
        }

class PersonaCargoForm(forms.ModelForm):
    class Meta:
        model = PersonaCargo
        exclude = ['deleted_at']

class SustanciacionNotificacionForm(forms.ModelForm):
    class Meta:
        model = SustanciacionNotificacion
        exclude = ['deleted_at']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['personal'] = forms.CharField(
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres Apellidos'}),
            label='Nombres y Apellidos',
            help_text='Escriba los nombres y apellidos del notificado. Si no existe se creará automáticamente.',
            required=True
        )
        if self.instance and self.instance.pk and self.instance.personal:
            self.initial['personal'] = self.instance.personal.get_full_name()
        
        firma = self.fields['firma_digital_hash']
        firma.widget = forms.TextInput(attrs={'class': 'form-control font-monospace', 'placeholder': 'Se genera automáticamente al guardar', 'readonly': True})
        firma.required = False
        
        huella = self.fields['huella_digital_hash']
        huella.widget = forms.TextInput(attrs={'class': 'form-control font-monospace', 'placeholder': 'Se genera automáticamente al guardar', 'readonly': True})
        huella.required = False

    def clean_personal(self):
        value = self.cleaned_data.get('personal', '')
        if not value:
            raise forms.ValidationError('Debe ingresar los nombres y apellidos del notificado.')
        
        # Lógica local para resolver personal sin importar de usuarios.forms
        from apps.expedientes.models import Personal
        partes = value.strip().split(None, 1)
        if len(partes) < 2:
            raise forms.ValidationError('Ingrese nombres y apellidos separados por espacio.')
        nombres = partes[0]
        apellidos = partes[1]
        
        personal, _ = Personal.objects.get_or_create(
            cedula='00000000',
            defaults={'nombres': nombres, 'apellidos': apellidos}
        )
        if personal.nombres != nombres or personal.apellidos != apellidos:
            personal.nombres = nombres
            personal.apellidos = apellidos
            personal.save(update_fields=['nombres', 'apellidos'])
        return personal

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.personal = self.cleaned_data['personal']
        raw_firma = f"{getattr(instance.expediente, 'numero_expediente', '')}|{instance.personal.get_full_name()}|{instance.fecha}|{instance.hora}|{instance.lugar}|{timezone.now().isoformat()}"
        instance.firma_digital_hash = hashlib.sha256(raw_firma.encode()).hexdigest()
        raw_huella = f"{instance.personal.get_full_name()}|{instance.personal.cedula}|{timezone.now().isoformat()}|{hash(instance)}"
        instance.huella_digital_hash = hashlib.sha256(raw_huella.encode()).hexdigest()
        if commit: instance.save()
        return instance

class SujetoProcesalForm(forms.ModelForm):
    class Meta:
        model = SujetoProcesal
        exclude = ['deleted_at']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].empty_label = None
        for f in self.fields.values():
            css = 'form-select' if isinstance(f.widget, forms.Select) else 'form-control'
            if isinstance(f.widget, forms.Textarea): css = 'form-control'
            f.widget.attrs.setdefault('class', css)
