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


class UsuarioCreationForm(forms.ModelForm):
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

    class Meta:
        model = Usuario
        fields = ['usuario', 'correo', 'rol']
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

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


class UsuarioChangeForm(forms.ModelForm):
    nombres = forms.CharField(label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    apellidos = forms.CharField(label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    cedula = forms.CharField(label='Cédula', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    frase_seguridad = forms.CharField(
        label='Frase de Seguridad', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'off',
            'readonly': False,
        }),
        required=False,
        min_length=8,
        help_text='Dejar en blanco para conservar la frase actual.',
    )

    def __init__(self, *args, **kwargs):
        from apps.expedientes.models import Personal
        roles_filter = kwargs.pop('roles_filter', None)
        super().__init__(*args, **kwargs)
        
        # BÚSQUEDA FORZADA: Intentar encontrar el personal asociado por el usuario
        # Independientemente de si la relación de base de datos está activa o no.
        # Buscamos en Personal por el username del usuario.
        
        personal = None
        # Intento 1: Por la relación definida en el modelo
        if self.instance and hasattr(self.instance, 'personal'):
            personal = self.instance.personal
            
        # Intento 2: Búsqueda explícita por la cédula, si el usuario tiene una propiedad cedula
        if not personal and hasattr(self.instance, 'cedula') and self.instance.cedula:
            personal = Personal.objects.filter(cedula=self.instance.cedula).first()
            
        # Intento 3: Búsqueda por nombres/usuario si el sistema lo permite
        if not personal:
            # Dado que el usuario tiene 'usuario' como username, intentamos filtrar
            # Si en la tabla Personal existe un campo o relación que nos permita filtrar
            # Aquí asumimos que podemos buscar por algún campo relacionado
            pass

        if personal:
            self.fields['nombres'].initial = personal.nombres
            self.fields['apellidos'].initial = personal.apellidos
            self.fields['cedula'].initial = personal.cedula
            # Asegurar initial para ModelForm
            self.initial['nombres'] = personal.nombres
            self.initial['apellidos'] = personal.apellidos
            self.initial['cedula'] = personal.cedula
        
        self.fields['frase_seguridad'].initial = ''
        self.fields['frase_seguridad'].widget.attrs['value'] = ''
        
        if roles_filter:
            self.fields['rol'].choices = roles_filter

    # Validación de cédula eliminada para evitar bloqueos innecesarios al editar

    def save(self, commit=True):
        from apps.expedientes.models import Personal
        usuario = super().save(commit=False)
        frase = self.cleaned_data.get('frase_seguridad', '').strip()
        if frase:
            usuario.set_frase_seguridad(frase)
        
        # 1. Buscar registro personal existente
        personal = getattr(usuario, 'personal', None)
        if not personal and usuario.correo:
            personal = Personal.objects.filter(correo=usuario.correo).first()
            
        # 2. Si no existe, crear uno nuevo
        if not personal:
            cedula = self.cleaned_data.get('cedula')
            personal = Personal.objects.create(
                cedula=cedula or '',
                correo=usuario.correo,
                usuario=usuario,
                nombres=self.cleaned_data.get('nombres', ''),
                apellidos=self.cleaned_data.get('apellidos', '')
            )
            usuario.personal = personal
        else:
            # 3. Actualizar registro existente
            personal.nombres = self.cleaned_data.get('nombres', personal.nombres)
            personal.apellidos = self.cleaned_data.get('apellidos', personal.apellidos)
            
            nueva_cedula = self.cleaned_data.get('cedula')
            if nueva_cedula and nueva_cedula != personal.cedula:
                # Comprobar si otra fila TIENE esta cédula y lanzar error amigable
                if Personal.objects.filter(cedula=nueva_cedula).exclude(id=personal.id).exists():
                     raise forms.ValidationError('Esta cédula ya está siendo utilizada por otra persona.')
                personal.cedula = nueva_cedula
            
            if not personal.usuario:
                personal.usuario = usuario
            personal.save()
            usuario.personal = personal
            
        if commit:
            usuario.save()
        return usuario

    class Meta:
        model = Usuario
        fields = ['correo', 'foto_perfil', 'rol']
        widgets = {
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif,image/webp'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }


class RegistroUsuarioForm(forms.ModelForm):
    nombres = forms.CharField(label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    apellidos = forms.CharField(label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    cedula = forms.CharField(label='Cédula', widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    password = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
        required=True,
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
    )

    def __init__(self, *args, **kwargs):
        roles_filter = kwargs.pop('roles_filter', None)
        super().__init__(*args, **kwargs)
        if roles_filter:
            self.fields['rol'].choices = roles_filter

    class Meta:
        model = Usuario
        fields = ['usuario', 'correo', 'rol']
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

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
        from apps.expedientes.models import Personal
        usuario = super().save(commit=False)
        password_plana = self.cleaned_data['password']
        usuario.set_password(password_plana)
        usuario.set_frase_seguridad(self.cleaned_data.get('frase_seguridad', ''))
        
        if commit:
            usuario.save()
            # Crear y vincular Personal
            Personal.objects.create(
                usuario=usuario,
                cedula=self.cleaned_data['cedula'],
                nombres=self.cleaned_data['nombres'],
                apellidos=self.cleaned_data['apellidos'],
                correo=usuario.correo
            )
        return usuario



class PasswordChangeForm(forms.Form):
    password_actual = forms.CharField(
        label='Contraseña Actual', widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    nueva_password = forms.CharField(
        label='Nueva Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=16,
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
        self.usuario.save(update_fields=['password'])
