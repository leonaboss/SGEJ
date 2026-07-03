import hashlib
from django import forms
from django.utils import timezone
from .models import (
    Personal, Cargo, PersonaCargo, Motivo, Tribunal, Expediente,
    Actuacion, AudienciaAgenda, LitigioContraparte, SustanciacionNotificacion,
    SujetoProcesal
)
from apps.usuarios.models import Usuario


def clean_personal_text(value):
    """Resuelve texto 'nombres apellidos' en un objeto Personal (get_or_create)."""
    partes = value.strip().split(None, 1)
    if len(partes) < 2:
        raise forms.ValidationError('Ingrese nombres y apellidos separados por espacio.')
    nombres = partes[0]
    apellidos = partes[1]
    qs = Personal.objects.filter(
        nombres=nombres, apellidos=apellidos, deleted_at__isnull=True
    )
    if qs.exists():
        return qs.first()
    raw = f"{value}|{timezone.now().isoformat()}"
    cedula_tmp = f"TMP-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"
    return Personal.objects.create(cedula=cedula_tmp, nombres=nombres, apellidos=apellidos)


class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        exclude = ['deleted_at']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        exclude = ['deleted_at']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class MotivoForm(forms.ModelForm):
    class Meta:
        model = Motivo
        exclude = ['deleted_at']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class TribunalForm(forms.ModelForm):
    class Meta:
        model = Tribunal
        exclude = ['deleted_at']


class ExpedienteForm(forms.ModelForm):
    tribunal_tipo = forms.ChoiceField(
        choices=Tribunal.TipoTribunalChoices.choices,
        label='Tipo de Tribunal',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    class Meta:
        model = Expediente
        fields = [
            'numero_expediente', 'numero_expediente_relativo', 'cedula', 'tipo_modulo',
            'personal', 'estatus', 'fecha_registro', 'motivo', 'cargo', 'tema_filtro',
            'institucion', 'ano', 'duracion', 'tipo_convenio', 'fecha_vencimiento',
            'tipo_demanda', 'fecha_demanda', 'tribunal',
            'hora_procedimiento', 'lugar_procedimiento', 'fase_actual', 'cronometro_limite',
            'firma_digital_hash', 'huella_digital_hash',
        ]
        widgets = {
            'tipo_convenio': forms.Textarea(attrs={'rows': 3}),
            'fecha_registro': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'numero_expediente': 'Ingrese el número único del expediente.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cedula = self.fields['cedula']
        cedula.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'V-12345678'})
        cedula.label = 'Cédula'
        cedula.help_text = 'Formato: V- seguido solo de números (ej: V-12345678).'

        personal = self.fields['personal']
        personal.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres Apellidos'})
        personal.label = 'Nombres y Apellidos de la Persona'
        personal.help_text = 'Escriba los nombres y apellidos. Si no existe se creará automáticamente.'
        if self.instance and self.instance.pk and self.instance.personal_id:
            personal.initial = self.instance.personal.get_full_name()

        cargo = self.fields['cargo']
        cargo.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Docente, Administrativo, Obrero'})
        cargo.label = 'Cargo'
        cargo.help_text = 'Escriba el cargo. Si no existe se creará automáticamente.'
        cargo.required = False
        if self.instance and self.instance.pk and self.instance.cargo_id:
            cargo.initial = str(self.instance.cargo)

        motivo = self.fields['motivo']
        motivo.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Jubilación, Renuncia, Ingreso'})
        motivo.label = 'Motivo'
        motivo.help_text = 'Escriba el motivo. Si no existe se creará automáticamente.'
        motivo.required = False
        if self.instance and self.instance.pk and self.instance.motivo_id:
            motivo.initial = str(self.instance.motivo)

        tribunal = self.fields['tribunal']
        tribunal.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del tribunal'})
        tribunal.label = 'Nombre del Tribunal'
        tribunal.help_text = 'Escriba el nombre del tribunal.'
        tribunal.required = False
        if self.instance and self.instance.pk and self.instance.tribunal_id:
            tribunal.initial = str(self.instance.tribunal)
            self.initial['tribunal_tipo'] = self.instance.tribunal.tipo

        tipo_modulo = self.initial.get('tipo_modulo')
        if self.instance and self.instance.pk:
            tipo_modulo = self.instance.tipo_modulo

        self._configure_fields_for_module(tipo_modulo)

    def _configure_fields_for_module(self, tipo_modulo):
        """Configura visibilidad y widgets según el módulo."""
        convenios_fields = ['institucion', 'ano', 'duracion', 'tipo_convenio', 'fecha_vencimiento']
        litigios_fields = ['tipo_demanda', 'tribunal_tipo', 'tribunal']
        sust_fields = ['hora_procedimiento', 'lugar_procedimiento', 'fase_actual', 'cronometro_limite',
                       'firma_digital_hash', 'huella_digital_hash']

        if tipo_modulo == 'SUST':
            for f in convenios_fields + litigios_fields:
                self.fields.pop(f, None)

            firma = self.fields['firma_digital_hash']
            firma.widget = forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Se genera automáticamente al guardar',
                'readonly': True,
            })
            firma.label = 'Firma Digital (SHA-256)'
            firma.help_text = 'Hash SHA-256 generado automáticamente.'
            firma.required = False

            huella = self.fields['huella_digital_hash']
            huella.widget = forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Se genera automáticamente al guardar',
                'readonly': True,
            })
            huella.label = 'Huella Digital (SHA-256)'
            huella.help_text = 'Hash SHA-256 generado automáticamente.'
            huella.required = False

        elif tipo_modulo == 'LITI':
            for f in convenios_fields + sust_fields:
                self.fields.pop(f, None)

            tipo_demanda = self.fields['tipo_demanda']
            tipo_demanda.widget = forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cobro de Bolívares, Daños y Perjuicios, etc.'
            })
            tipo_demanda.label = 'Tipo de Demanda'
            tipo_demanda.required = True

            fecha_demanda = self.fields['fecha_demanda']
            fecha_demanda.widget = forms.DateInput(attrs={
                'type': 'date', 'class': 'form-control'
            })
            fecha_demanda.label = 'Fecha de Demanda'
            fecha_demanda.required = True

        elif tipo_modulo == 'CONT':
            for f in litigios_fields + sust_fields:
                self.fields.pop(f, None)

        else:
            # DESP u otros: mostrar solo campos generales
            for f in convenios_fields + litigios_fields + sust_fields:
                self.fields.pop(f, None)

    def clean_personal(self):
        return clean_personal_text(self.cleaned_data['personal'])

    def clean_cargo(self):
        value = self.cleaned_data.get('cargo')
        if not value:
            return None
        value = value.strip()
        cargo, _ = Cargo.objects.get_or_create(
            descripcion=value,
            defaults={
                'categoria': 'DOC',
                'tipo': 'FIJ',
                'marco_legal': '',
            }
        )
        return cargo

    def clean_motivo(self):
        value = self.cleaned_data.get('motivo')
        if not value:
            return None
        value = value.strip()
        motivo, _ = Motivo.objects.get_or_create(
            descripcion=value,
            defaults={'tipo': ''}
        )
        return motivo

    def clean_tribunal(self):
        value = self.cleaned_data.get('tribunal')
        tribunal_tipo = self.cleaned_data.get('tribunal_tipo', '')
        if not value:
            return None
        value = value.strip()
        tribunal, _ = Tribunal.objects.get_or_create(
            nombre=value,
            defaults={'tipo': tribunal_tipo or 'OTRO'}
        )
        if tribunal.tipo != tribunal_tipo and tribunal_tipo:
            tribunal.tipo = tribunal_tipo
            tribunal.save(update_fields=['tipo'])
        return tribunal

    def clean_numero_expediente(self):
        value = self.cleaned_data.get('numero_expediente', '').strip()
        if not value:
            raise forms.ValidationError('El número de expediente es obligatorio.')
        return value

    def clean_cedula(self):
        value = self.cleaned_data.get('cedula', '').strip().upper()
        if not value:
            raise forms.ValidationError('La cédula es obligatoria.')
        if value.startswith('V-'):
            numeric = value[2:]
        elif value.startswith('V'):
            numeric = value[1:]
        else:
            numeric = value
        if not numeric or not numeric.isdigit():
            raise forms.ValidationError('Formato: V- seguido solo de números (ej: V-12345678).')
        if len(numeric) < 6:
            raise forms.ValidationError('La cédula debe tener al menos 6 dígitos.')
        return f'V-{numeric}'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.tipo_modulo == 'SUST':
            raw_firma = (
                str(instance.numero_expediente) + '|' +
                str(instance.cedula) + '|' +
                str(instance.personal.get_full_name() if instance.personal_id else '') + '|' +
                str(instance.cargo) + '|' +
                str(instance.motivo) + '|' +
                str(instance.tribunal) + '|' +
                timezone.now().isoformat()
            )
            instance.firma_digital_hash = hashlib.sha256(raw_firma.encode()).hexdigest()

            raw_huella = (
                str(instance.personal.get_full_name() if instance.personal_id else '') + '|' +
                str(instance.cedula) + '|' +
                timezone.now().isoformat() + '|' +
                str(hash(instance))
            )
            instance.huella_digital_hash = hashlib.sha256(raw_huella.encode()).hexdigest()
        if commit:
            instance.save()
        return instance


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

        personal = self.fields['personal']
        personal.widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres Apellidos'})
        personal.label = 'Nombres y Apellidos'
        personal.help_text = 'Escriba los nombres y apellidos del notificado. Si no existe se creará automáticamente.'
        if self.instance and self.instance.pk and self.instance.personal_id:
            personal.initial = self.instance.personal.get_full_name()

        firma = self.fields['firma_digital_hash']
        firma.widget = forms.TextInput(attrs={
            'class': 'form-control font-monospace',
            'placeholder': 'Se genera automáticamente al guardar',
            'readonly': True,
        })
        firma.label = 'Firma Digital (SHA-256)'
        firma.help_text = 'Hash SHA-256 generado automáticamente al guardar la notificación.'
        firma.required = False

        huella = self.fields['huella_digital_hash']
        huella.widget = forms.TextInput(attrs={
            'class': 'form-control font-monospace',
            'placeholder': 'Se genera automáticamente al guardar',
            'readonly': True,
        })
        huella.label = 'Huella Digital (SHA-256)'
        huella.help_text = 'Hash SHA-256 generado automáticamente al guardar la notificación.'
        huella.required = False

    def clean_personal(self):
        value = self.cleaned_data.get('personal', '')
        if not value:
            raise forms.ValidationError('Debe ingresar los nombres y apellidos del notificado.')
        return clean_personal_text(value)

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_firma = (
            str(getattr(instance.expediente, 'numero_expediente', '')) + '|' +
            str(instance.personal.get_full_name()) + '|' +
            str(instance.fecha) + '|' +
            str(instance.hora) + '|' +
            str(instance.lugar) + '|' +
            timezone.now().isoformat()
        )
        instance.firma_digital_hash = hashlib.sha256(raw_firma.encode()).hexdigest()

        raw_huella = (
            str(instance.personal.get_full_name()) + '|' +
            str(instance.personal.cedula) + '|' +
            timezone.now().isoformat() + '|' +
            str(hash(instance))
        )
        instance.huella_digital_hash = hashlib.sha256(raw_huella.encode()).hexdigest()

        if commit:
            instance.save()
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
            if isinstance(f.widget, forms.Textarea):
                css = 'form-control'
            f.widget.attrs.setdefault('class', css)
