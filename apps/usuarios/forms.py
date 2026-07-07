from django import forms
from django.contrib.auth.hashers import check_password
from .models import Usuario, HistorialContrasena
import re


def validate_password_strength(password):
    if len(password) < 16:
        raise forms.ValidationError('La contraseña debe tener al menos 16 caracteres.')
    if not re.search(r'[A-Za-z]', password):
        raise forms.ValidationError('La contraseña debe contener al menos una letra.')
    if not re.search(r'[A-Z]', password):
        raise forms.ValidationError('La contraseña debe contener al menos una letra mayúscula.')
    if not re.search(r'\d', password):
        raise forms.ValidationError('La contraseña debe contener al menos un número.')
    if not re.search(r'[!@#$%^&*()_+\-=[\]{};\'"\\|,.<>/?~`]', password):
        raise forms.ValidationError('La contraseña debe contener al menos un carácter especial como @.')
    return password


def clean_personal_text(value):
    """Resuelve texto 'nombres apellidos' en un objeto Personal (get_or_create)."""
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


class PersonalTextFieldMixin:
    """Mixin que reemplaza el field 'personal' (FK) por un CharField con TextInput."""

    def _init_personal_textfield(self):
        initial = ''
        if self.instance and self.instance.pk and self.instance.personal_id:
            try:
                initial = self.instance.personal.get_full_name()
            except Exception:
                initial = self.instance.personal_id
        self.fields['personal'] = forms.CharField(
            label='Nombres y Apellidos',
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres Apellidos (opcional)'}),
            help_text='Opcional. Si se omite, se usará el nombre de usuario.',
        )
        self.initial['personal'] = initial

    def clean_personal(self):
        value = self.cleaned_data.get('personal')
        if not value:
            return None
        from apps.expedientes.models import Personal
        if isinstance(value, Personal):
            return value
        if isinstance(value, int):
            try:
                return Personal.objects.get(id=value)
            except Personal.DoesNotExist:
                raise forms.ValidationError('Personal no encontrado.')
        if isinstance(value, str):
            if value.isdigit():
                try:
                    return Personal.objects.get(id=int(value))
                except Personal.DoesNotExist:
                    raise forms.ValidationError('Personal no encontrado.')
            return clean_personal_text(value)
        return value


class UsuarioCreationForm(forms.ModelForm, PersonalTextFieldMixin):
    password = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        required=True,
        help_text='Mínimo 16 caracteres, debe incluir letras, números, una mayúscula y un carácter especial como @.'
    )
    password_repeat = forms.CharField(
        label='Repetir Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        required=True,
    )
    frase_seguridad = forms.CharField(
        label='Frase de Seguridad', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        required=True,
        help_text='Se usará para recuperar su contraseña si olvida el correo o la contraseña.',
    )

    def __init__(self, *args, **kwargs):
        roles_filter = kwargs.pop('roles_filter', None)
        super().__init__(*args, **kwargs)
        if roles_filter:
            self.fields['rol'].choices = roles_filter
        self._init_personal_textfield()

    class Meta:
        model = Usuario
        fields = ['usuario', 'personal', 'cedula', 'correo',
                  'telefono', 'rol']
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_usuario(self):
        value = (self.cleaned_data.get('usuario') or '').strip()
        if not value:
            raise forms.ValidationError('El nombre de usuario es obligatorio.')
        if len(value) < 3:
            raise forms.ValidationError('El usuario debe tener al menos 3 caracteres.')
        return value

    def clean_cedula(self):
        value = (self.cleaned_data.get('cedula') or '').strip().upper()
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

    def clean_correo(self):
        value = (self.cleaned_data.get('correo') or '').strip()
        if not value:
            raise forms.ValidationError('El correo electrónico es obligatorio.')
        if '@' not in value:
            raise forms.ValidationError('Ingrese un correo electrónico válido.')
        return value

    def clean_telefono(self):
        value = (self.cleaned_data.get('telefono') or '').strip()
        if value and not value.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números.')
        return value

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if password:
            validate_password_strength(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_repeat = cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError({'password_repeat': 'Las contraseñas no coinciden.'})
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password_plana = self.cleaned_data['password']
        usuario.set_password(password_plana)
        usuario._password_plana_temporal = password_plana
        usuario.set_frase_seguridad(self.cleaned_data.get('frase_seguridad', ''))
        if commit:
            usuario.save()
        return usuario


class UsuarioChangeForm(forms.ModelForm, PersonalTextFieldMixin):
    frase_seguridad = forms.CharField(
        label='Frase de Seguridad', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'off',  # Evita que el navegador sugiera contraseñas
            'readonly': False,
        }),
        required=False,
        min_length=8,
        help_text='Dejar en blanco para conservar la frase actual. (La frase no se puede visualizar por seguridad).',
    )

    def __init__(self, *args, **kwargs):
        roles_filter = kwargs.pop('roles_filter', None)
        super().__init__(*args, **kwargs)
        # --- CORRECCIÓN CRÍTICA ---
        # Forzamos que este campo NO tome valores de la instancia (evita mostrar hashes o contraseñas)
        self.fields['frase_seguridad'].initial = ''
        self.fields['frase_seguridad'].widget.attrs['value'] = ''
        # ---------------------------
        if roles_filter:
            self.fields['rol'].choices = roles_filter
        self._init_personal_textfield()

    def clean_frase_seguridad(self):
        frase = self.cleaned_data.get('frase_seguridad', '').strip()
        if frase and len(frase) < 8:
            raise forms.ValidationError('La frase de seguridad debe tener al menos 8 caracteres.')
        return frase

    def save(self, commit=True):
        usuario = super().save(commit=False)
        frase = self.cleaned_data.get('frase_seguridad', '').strip()
        if frase:
            usuario.set_frase_seguridad(frase)
        # Si no hay frase, no hacemos nada (mantenemos la anterior)
        if commit:
            usuario.save()
        return usuario

    class Meta:
        model = Usuario
        fields = ['personal', 'cedula', 'correo', 'telefono',
                  'rol', 'foto_perfil']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif,image/webp'}),
        }

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

    def clean_correo(self):
        value = (self.cleaned_data.get('correo') or '').strip()
        if value and '@' not in value:
            raise forms.ValidationError('Ingrese un correo electrónico válido.')
        return value

    def clean_telefono(self):
        value = (self.cleaned_data.get('telefono') or '').strip()
        if value and not value.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números.')
        return value


class RegistroUsuarioForm(forms.ModelForm, PersonalTextFieldMixin):
    password = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        required=True,
        help_text='Mínimo 16 caracteres, debe incluir letras, números, una mayúscula y un carácter especial como @.'
    )
    password_repeat = forms.CharField(
        label='Repetir Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        required=True,
    )
    frase_seguridad = forms.CharField(
        label='Frase de Seguridad', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        required=True,
        help_text='Se usará para recuperar su contraseña si olvida el correo o la contraseña.',
    )

    def __init__(self, *args, **kwargs):
        roles_filter = kwargs.pop('roles_filter', None)
        super().__init__(*args, **kwargs)
        if roles_filter:
            self.fields['rol'].choices = roles_filter
        self._init_personal_textfield()

    class Meta:
        model = Usuario
        fields = ['usuario', 'personal', 'cedula', 'correo',
                  'telefono', 'rol']
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_usuario(self):
        value = (self.cleaned_data.get('usuario') or '').strip()
        if not value:
            raise forms.ValidationError('El nombre de usuario es obligatorio.')
        if len(value) < 3:
            raise forms.ValidationError('El usuario debe tener al menos 3 caracteres.')
        return value

    def clean_cedula(self):
        value = (self.cleaned_data.get('cedula') or '').strip().upper()
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

    def clean_correo(self):
        value = (self.cleaned_data.get('correo') or '').strip()
        if not value:
            raise forms.ValidationError('El correo electrónico es obligatorio.')
        if '@' not in value:
            raise forms.ValidationError('Ingrese un correo electrónico válido.')
        return value

    def clean_telefono(self):
        value = (self.cleaned_data.get('telefono') or '').strip()
        if value and not value.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números.')
        return value

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if password:
            validate_password_strength(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_repeat = cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError({'password_repeat': 'Las contraseñas no coinciden.'})
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password_plana = self.cleaned_data['password']
        usuario.set_password(password_plana)
        usuario._password_plana_temporal = password_plana
        usuario.set_frase_seguridad(self.cleaned_data.get('frase_seguridad', ''))
        if commit:
            usuario.save()
        return usuario


class PasswordChangeForm(forms.Form):
    password_actual = forms.CharField(
        label='Contraseña Actual', widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    nueva_password = forms.CharField(
        label='Nueva Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        help_text='Mínimo 16 caracteres, letras, números, una mayúscula y un carácter especial como @.'
    )
    nueva_password_repeat = forms.CharField(
        label='Repetir Nueva Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16
    )

    def __init__(self, usuario, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_password_actual(self):
        password = self.cleaned_data.get('password_actual', '')
        if not password:
            raise forms.ValidationError('Debe ingresar su contraseña actual.')
        if not check_password(password, self.usuario.password):
            raise forms.ValidationError('La contraseña actual no es correcta.')
        return password

    def clean_nueva_password(self):
        password = self.cleaned_data.get('nueva_password', '')
        if password:
            validate_password_strength(password)
        historial = HistorialContrasena.objects.filter(
            usuario=self.usuario
        ).order_by('-created_at')[:3]
        for h in historial:
            if check_password(password, h.password_hash):
                raise forms.ValidationError(
                    'No puedes reutilizar ninguna de tus últimas 3 contraseñas.'
                )
        return password

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get('nueva_password')
        repeat = cleaned_data.get('nueva_password_repeat')
        if nueva and repeat and nueva != repeat:
            raise forms.ValidationError({'nueva_password_repeat': 'Las contraseñas no coinciden.'})
        return cleaned_data

    def save(self):
        password_plana = self.cleaned_data['nueva_password']
        self.usuario.set_password(password_plana)
        self.usuario._password_plana_temporal = password_plana
        self.usuario.save(update_fields=['password'])
