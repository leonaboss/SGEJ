import io
import base64
import qrcode
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import Usuario, HistorialContrasena, BitacoraAuditoria
from .forms import UsuarioCreationForm, UsuarioChangeForm, PasswordChangeForm, RegistroUsuarioForm

class RoleRequiredMixin(LoginRequiredMixin):
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in self.roles_permitidos:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('expedientes:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(View):
    template_name = 'auth/login.html'
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('expedientes:dashboard')
        return render(request, self.template_name)
    def post(self, request):
        username = request.POST.get('usuario', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, self.template_name)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_bloqueado:
                messages.error(request, 'Su cuenta ha sido bloqueada por múltiples intentos fallidos. Contacte al Administrador General.')
                return render(request, self.template_name)
            user.intentos_fallidos = 0
            user.save(update_fields=['intentos_fallidos'])
            if user.is_2fa_enabled:
                request.session['2fa_user_id'] = user.id
                return redirect('usuarios:totp_verify')
            login(request, user)
            return redirect('expedientes:dashboard')
        else:
            try:
                target_user = Usuario.objects.get(usuario=username)
                target_user.intentos_fallidos += 1
                if target_user.intentos_fallidos >= 3:
                    target_user.is_bloqueado = True
                    messages.error(request, 'Cuenta bloqueada tras 3 intentos fallidos. Contacte al Administrador General.')
                else:
                    remaining = 3 - target_user.intentos_fallidos
                    messages.error(request, f'Credenciales inválidas. Le quedan {remaining} intento(s).')
                target_user.save(update_fields=['intentos_fallidos', 'is_bloqueado'])
            except Usuario.DoesNotExist:
                messages.error(request, 'Credenciales inválidas.')
            return render(request, self.template_name)

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('usuarios:login')
    def post(self, request):
        logout(request)
        return redirect('usuarios:login')

class TOTPVerifyView(View):
    template_name = 'auth/totp_verify.html'
    def get(self, request):
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            return redirect('usuarios:login')
        return render(request, self.template_name)
    def post(self, request):
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            return redirect('usuarios:login')
        try:
            user = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            return redirect('usuarios:login')
        token = request.POST.get('token', '').strip()
        if not token:
            messages.error(request, 'Ingrese el código de verificación.')
            return render(request, self.template_name)
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device and device.verify_token(token):
            del request.session['2fa_user_id']
            login(request, user)
            messages.success(request, 'Verificación de dos factores exitosa.')
            return redirect('expedientes:dashboard')
        messages.error(request, 'Código de verificación inválido. Intente de nuevo.')
        return render(request, self.template_name)


class Setup2FAView(LoginRequiredMixin, View):
    template_name = 'usuarios/setup_2fa.html'

    def _cleanup_unconfirmed(self, request):
        TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()

    def get(self, request):
        device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
        if device:
            messages.info(request, 'Ya tiene 2FA activado.')
            return redirect('usuarios:profile')
        self._cleanup_unconfirmed(request)
        try:
            new_device = TOTPDevice.objects.create(
                user=request.user,
                name=f"{request.user.usuario}_totp",
                confirmed=False,
                tolerance=1,
                ttl=30
            )
            otp_url = new_device.config_url
            qr = qrcode.make(otp_url)
            buf = io.BytesIO()
            qr.save(buf, format='PNG')
            qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return render(request, self.template_name, {
                'qr_code': qr_b64,
                'device_id': new_device.id,
                'secret_key': new_device.key
            })
        except Exception as e:
            messages.error(request, f'Error al generar el código QR: {e}')
            return redirect('usuarios:profile')

    def post(self, request):
        device_id = request.POST.get('device_id')
        token = request.POST.get('token', '').strip()
        if not token:
            messages.error(request, 'Ingrese el código generado por su app.')
            return redirect('usuarios:setup_2fa')
        try:
            device = TOTPDevice.objects.get(id=device_id, user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            messages.error(request, 'Dispositivo no encontrado. Intente de nuevo.')
            return redirect('usuarios:setup_2fa')
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            request.user.is_2fa_enabled = True
            request.user.totp_secret = device.key
            request.user.save(update_fields=['is_2fa_enabled', 'totp_secret'])
            messages.success(request, '2FA activado exitosamente.')
            return redirect('usuarios:profile')
        messages.error(request, 'Código inválido. Asegúrese de haber escaneado el QR e ingrese el código de 6 dígitos.')
        return render(request, 'usuarios/setup_2fa.html', {
            'device_id': device.id,
            'secret_key': device.key
        })


class Disable2FAView(LoginRequiredMixin, View):
    def post(self, request):
        TOTPDevice.objects.filter(user=request.user).delete()
        request.user.is_2fa_enabled = False
        request.user.totp_secret = None
        request.user.save(update_fields=['is_2fa_enabled', 'totp_secret'])
        messages.success(request, '2FA desactivado.')
        return redirect('usuarios:profile')


class ConfirmBlock2FAView(LoginRequiredMixin, View):
    template_name = 'auth/totp_verify.html'
    def get(self, request):
        if 'block_user_id' not in request.session:
            return redirect('usuarios:usuario_list')
        return render(request, self.template_name, {'action_label': 'Confirmar bloqueo/desbloqueo'})
    def post(self, request):
        pk = request.session.get('block_user_id')
        if not pk:
            return redirect('usuarios:usuario_list')
        token = request.POST.get('token', '').strip()
        if not token:
            messages.error(request, 'Ingrese el código de verificación.')
            return render(request, self.template_name)
        device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
        if device and device.verify_token(token):
            del request.session['block_user_id']
            usuario = get_object_or_404(Usuario, pk=pk, deleted_at__isnull=True)
            if usuario.is_bloqueado:
                usuario.is_bloqueado = False
                usuario.intentos_fallidos = 0
                messages.success(request, f'Usuario {usuario.usuario} desbloqueado.')
            else:
                usuario.is_bloqueado = True
                messages.warning(request, f'Usuario {usuario.usuario} bloqueado.')
            usuario.save(update_fields=['is_bloqueado', 'intentos_fallidos'])
            return redirect('usuarios:usuario_list')
        messages.error(request, 'Código de verificación inválido.')
        return render(request, self.template_name)


class RecoveryResetView(View):
    template_name = 'auth/recovery.html'
    def get(self, request):
        token = request.GET.get('token', '')
        uid = request.GET.get('uid', '')
        saved_token = request.session.get('recovery_token')
        saved_uid = request.session.get('recovery_user_id')
        if not token or not uid or token != saved_token or int(uid) != saved_uid:
            messages.error(request, 'Enlace de recuperación inválido o expirado.')
            return redirect('usuarios:recovery')
        try:
            user = Usuario.objects.get(id=uid, deleted_at__isnull=True)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('usuarios:recovery')
        from .services import UsuarioService
        nueva_pass = UsuarioService.generar_password_temporal()
        user.set_password(nueva_pass)
        user.save(update_fields=['password'])
        HistorialContrasena.objects.create(usuario=user, password_hash=user.password)
        del request.session['recovery_token']
        del request.session['recovery_user_id']
        messages.success(request, f'Contraseña restablecida. Su nueva contraseña temporal es: {nueva_pass}')
        return redirect('usuarios:login')


class RecoveryView(View):
    template_name = 'auth/recovery.html'
    def get(self, request):
        from django.conf import settings
        context = {'entorno': getattr(settings, 'ENTORNO', 'localhost')}
        return render(request, self.template_name, context)
    def post(self, request):
        from django.conf import settings
        from django.utils.crypto import get_random_string
        from django.core.mail import send_mail
        from django.contrib.auth.hashers import make_password
        entorno = getattr(settings, 'ENTORNO', 'localhost')
        usuario_input = request.POST.get('usuario', '').strip()
        if not usuario_input:
            messages.error(request, 'Debe ingresar su nombre de usuario.')
            return render(request, self.template_name, {'entorno': entorno})
        try:
            user = Usuario.objects.get(usuario=usuario_input, deleted_at__isnull=True)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return render(request, self.template_name, {'entorno': entorno})
        if entorno == 'produccion':
            token = get_random_string(64)
            request.session['recovery_token'] = token
            request.session['recovery_user_id'] = user.id
            enlace = request.build_absolute_uri(f"/auth/recovery/reset?token={token}&uid={user.id}")
            send_mail(
                'Recuperación de Contraseña - SGEJ',
                f'Use el siguiente enlace para restablecer su contraseña: {enlace}',
                settings.DEFAULT_FROM_EMAIL,
                [user.correo] if user.correo else [],
                fail_silently=True,
            )
            messages.success(request, 'Revise su correo institucional para el enlace de recuperación.')
        else:
            frase = request.POST.get('frase_seguridad', '').strip()
            cedula = request.POST.get('cedula', '').strip()
            frase_maestra = getattr(settings, 'FRASE_SEGURIDAD_MAESTRA', '')
            if not frase or not cedula:
                messages.error(request, 'Debe ingresar la Frase de Seguridad Maestra y su Cédula.')
                return render(request, self.template_name, {'entorno': entorno})
            if frase == frase_maestra and cedula == user.cedula:
                from .services import UsuarioService
                nueva_pass = UsuarioService.generar_password_temporal()
                user.set_password(nueva_pass)
                user.save(update_fields=['password'])
                HistorialContrasena.objects.create(
                    usuario=user,
                    password_hash=user.password
                )
                messages.success(request, f'Contraseña restablecida. Su nueva contraseña temporal es: {nueva_pass}')
            else:
                messages.error(request, 'Frase de Seguridad o Cédula incorrectos.')
                return render(request, self.template_name, {'entorno': entorno})
        return redirect('usuarios:login')

class RegisterView(View):
    template_name = 'auth/register.html'

    def get_roles_disponibles(self):
        if Usuario.objects.count() == 0:
            return Usuario.ROLES
        return [r for r in Usuario.ROLES if r[0] != 'ADMIN']

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('expedientes:dashboard')
        form = RegistroUsuarioForm(roles_filter=self.get_roles_disponibles())
        return render(request, self.template_name, {
            'form': form, 'es_primero': Usuario.objects.count() == 0,
        })
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('expedientes:dashboard')
        form = RegistroUsuarioForm(request.POST, roles_filter=self.get_roles_disponibles())
        if form.is_valid():
            usuario = form.save()
            from django.contrib.auth import login
            login(request, usuario)
            messages.success(request, f'Cuenta creada exitosamente. ¡Bienvenido {usuario.usuario}!')
            return redirect('expedientes:dashboard')
        return render(request, self.template_name, {
            'form': form, 'es_primero': Usuario.objects.count() == 0,
        })

class ProfileView(LoginRequiredMixin, View):
    template_name = 'usuarios/profile.html'
    def get(self, request):
        form = UsuarioChangeForm(instance=request.user)
        return render(request, self.template_name, {'form': form})
    def post(self, request):
        form = UsuarioChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('usuarios:profile')
        return render(request, self.template_name, {'form': form})

class ProfileDeleteFotoView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.foto_perfil.delete(save=False)
        request.user.foto_perfil = None
        request.user.save(update_fields=['foto_perfil'])
        messages.success(request, 'Foto de perfil eliminada.')
        return redirect('usuarios:profile')


class PasswordChangeView(LoginRequiredMixin, View):
    template_name = 'usuarios/change_password.html'
    def get(self, request):
        form = PasswordChangeForm(request.user)
        return render(request, self.template_name, {'form': form})
    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('usuarios:profile')
        return render(request, self.template_name, {'form': form})

class UsuarioListView(RoleRequiredMixin, ListView):
    roles_permitidos = ['ADMIN', 'ABOG']
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    def get_queryset(self):
        qs = Usuario.objects.filter(deleted_at__isnull=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(usuario__icontains=q) | qs.filter(cedula__icontains=q) | qs.filter(personal__nombres__icontains=q) | qs.filter(personal__apellidos__icontains=q)
        rol = self.request.GET.get('rol', '').strip()
        if rol:
            qs = qs.filter(rol=rol)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['rol_filter'] = self.request.GET.get('rol', '')
        context['roles'] = Usuario.ROLES
        return context

class UsuarioCreateView(RoleRequiredMixin, View):
    roles_permitidos = ['ADMIN', 'ABOG']
    template_name = 'usuarios/usuario_form.html'
    def get_roles_filter(self):
        if self.request.user.rol == 'ADMIN':
            return Usuario.ROLES
        return [r for r in Usuario.ROLES if r[0] != 'ADMIN']

    def get(self, request):
        form = UsuarioCreationForm(roles_filter=self.get_roles_filter())
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})
    def post(self, request):
        form = UsuarioCreationForm(request.POST, request.FILES, roles_filter=self.get_roles_filter())
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.usuario} creado exitosamente.')
            return redirect('usuarios:usuario_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Crear'})

class UsuarioUpdateView(RoleRequiredMixin, View):
    roles_permitidos = ['ADMIN', 'ABOG']
    template_name = 'usuarios/usuario_form.html'
    def get_roles_filter(self):
        if self.request.user.rol == 'ADMIN':
            return Usuario.ROLES
        return [r for r in Usuario.ROLES if r[0] != 'ADMIN']

    def get(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk, deleted_at__isnull=True)
        if request.user.rol != 'ADMIN' and usuario.rol == 'ADMIN':
            messages.error(request, 'No tienes permiso para editar un Administrador.')
            return redirect('usuarios:usuario_list')
        form = UsuarioChangeForm(instance=usuario, roles_filter=self.get_roles_filter())
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'usuario_obj': usuario})
    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk, deleted_at__isnull=True)
        if request.user.rol != 'ADMIN' and usuario.rol == 'ADMIN':
            messages.error(request, 'No tienes permiso para editar un Administrador.')
            return redirect('usuarios:usuario_list')
        form = UsuarioChangeForm(request.POST, request.FILES, instance=usuario, roles_filter=self.get_roles_filter())
        if form.is_valid():
            if request.user.rol != 'ADMIN' and form.cleaned_data.get('rol') == 'ADMIN':
                messages.error(request, 'No tienes permiso para asignar rol Administrador.')
                return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'usuario_obj': usuario})
            form.save()
            messages.success(request, f'Usuario {usuario.usuario} actualizado.')
            return redirect('usuarios:usuario_list')
        return render(request, self.template_name, {'form': form, 'accion': 'Editar', 'usuario_obj': usuario})

class UsuarioToggleBlockView(RoleRequiredMixin, View):
    roles_permitidos = ['ADMIN']
    def post(self, request, pk):
        if request.user.is_2fa_enabled:
            token = request.POST.get('totp_token', '').strip()
            if token:
                device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
                if not device or not device.verify_token(token):
                    messages.error(request, 'Debe ingresar su código 2FA válido para realizar esta acción.')
                    return redirect('usuarios:usuario_list')
            else:
                request.session['block_user_id'] = pk
                return redirect('usuarios:confirm_block_2fa')
        usuario = get_object_or_404(Usuario, pk=pk, deleted_at__isnull=True)
        if usuario.is_bloqueado:
            usuario.is_bloqueado = False
            usuario.intentos_fallidos = 0
            messages.success(request, f'Usuario {usuario.usuario} desbloqueado.')
        else:
            usuario.is_bloqueado = True
            messages.warning(request, f'Usuario {usuario.usuario} bloqueado.')
        usuario.save(update_fields=['is_bloqueado', 'intentos_fallidos'])
        return redirect('usuarios:usuario_list')


class UsuarioDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        from .models import Usuario
        from django.utils import timezone
        if request.user.rol != 'ADMIN':
            messages.error(request, 'Solo administradores pueden eliminar usuarios.')
            return redirect('usuarios:usuario_list')
        obj = get_object_or_404(Usuario, pk=pk, deleted_at__isnull=True)
        if obj == request.user:
            messages.error(request, 'No puedes eliminarte a ti mismo.')
            return redirect('usuarios:usuario_list')
        obj.deleted_at = timezone.now()
        obj.is_active = False
        obj.save(update_fields=['deleted_at', 'is_active'])
        messages.success(request, f'Usuario {obj.usuario} eliminado lógicamente.')
        return redirect('usuarios:usuario_list')


class BitacoraListView(RoleRequiredMixin, ListView):
    roles_permitidos = ['ADMIN']
    model = BitacoraAuditoria
    template_name = 'usuarios/bitacora_list.html'
    context_object_name = 'bitacora_list'
    paginate_by = 25

    def get_queryset(self):
        qs = BitacoraAuditoria.objects.filter(usuario__isnull=False)

        usuario_id = self.request.GET.get('usuario', '').strip()
        accion = self.request.GET.get('accion', '').strip()
        fecha_desde = self.request.GET.get('fecha_desde', '').strip()
        fecha_hasta = self.request.GET.get('fecha_hasta', '').strip()
        q = self.request.GET.get('q', '').strip()

        if usuario_id and usuario_id != '0':
            qs = qs.filter(usuario_id=usuario_id)
        if accion and accion != '0':
            qs = qs.filter(accion=accion)
        if fecha_desde:
            qs = qs.filter(created_at__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(created_at__lte=f'{fecha_hasta} 23:59:59')
        if q:
            qs = qs.filter(descripcion__icontains=q) | qs.filter(modulo__icontains=q) | qs.filter(accion__icontains=q) | qs.filter(usuario__usuario__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = {}
        for k in ('usuario', 'accion', 'fecha_desde', 'fecha_hasta', 'q'):
            v = self.request.GET.get(k, '').strip()
            if v and not (k == 'usuario' and v == '0') and not (k == 'accion' and v == '0'):
                params[k] = v
        from urllib.parse import urlencode
        context['filtros_qs'] = urlencode(params)

        context['search_query'] = self.request.GET.get('q', '')
        context['filtro_usuario'] = self.request.GET.get('usuario', '0')
        context['filtro_accion'] = self.request.GET.get('accion', '0')
        context['filtro_desde'] = self.request.GET.get('fecha_desde', '')
        context['filtro_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['usuarios_filtro'] = Usuario.objects.filter(deleted_at__isnull=True).order_by('usuario')
        acciones_qs = BitacoraAuditoria.objects.filter(usuario__isnull=False).values_list('accion', flat=True).distinct().order_by('accion')
        context['acciones_filtro'] = [(a, a) for a in acciones_qs]
        return context


CAMPOS_USUARIOS = [
    ('usuario', 'Usuario'),
    ('get_full_name', 'Nombre Completo'),
    ('cedula', 'Cédula'),
    ('correo', 'Correo'),
    ('telefono', 'Teléfono'),
    ('get_rol_display_label', 'Rol'),
    ('is_active', 'Activo'),
    ('is_2fa_enabled', '2FA'),
]

class ExportarUsuariosExcelView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import Usuario
        from apps.infraestructura.services import ImportExportService
        qs = Usuario.objects.filter(deleted_at__isnull=True)
        return ImportExportService.exportar_modelo_excel(qs, 'Usuarios', CAMPOS_USUARIOS)


class ImportarUsuariosExcelView(LoginRequiredMixin, View):
    def post(self, request):
        import openpyxl
        from apps.expedientes.models import Personal
        archivo = request.FILES.get('archivo')
        if not archivo:
            messages.error(request, 'Debe seleccionar un archivo Excel.')
            return redirect('usuarios:usuario_list')
        try:
            wb = openpyxl.load_workbook(archivo, read_only=True)
            ws = wb.active
            filas = list(ws.iter_rows(min_row=2, values_only=True))
            from .models import Usuario
            creados = 0
            for fila in filas:
                if not any(fila):
                    continue
                try:
                    personal_obj, _ = Personal.objects.get_or_create(
                        cedula=str(fila[2]) if len(fila) > 2 and fila[2] else '00000000',
                        defaults={
                            'nombres': str(fila[0]) if len(fila) > 0 else '',
                            'apellidos': str(fila[1]) if len(fila) > 1 else '',
                        }
                    )
                    u = Usuario(
                        usuario=str(fila[0]),
                        personal=personal_obj,
                        cedula=str(fila[2]) if len(fila) > 2 and fila[2] else '',
                    )
                    u.set_password('SGEJ' + u.cedula)
                    u.save()
                    creados += 1
                except Exception:
                    continue
            messages.success(request, f'Se importaron {creados} usuarios.')
        except Exception as e:
            messages.error(request, f'Error al importar: {e}')
        return redirect('usuarios:usuario_list')
