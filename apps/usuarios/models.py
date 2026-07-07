"""
App: usuarios
Modelos de autenticación, RBAC y auditoría.
Responsabilidad: Identidad, roles, historial de contraseñas y bitácora.
"""
from django.db import models
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class BaseQuerySet(models.QuerySet):
    """QuerySet base para aislamiento de datos."""
    def for_user(self, user):
        if user.is_authenticated and user.rol == 'ADMIN':
            return self
        return self.filter(usuario=user)

class UsuarioManager(BaseUserManager):
    """Manager personalizado que usa 'usuario' como campo de login."""
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)

    def create_user(self, usuario, password=None, **extra_fields):
        if not usuario:
            raise ValueError('El campo usuario es obligatorio.')
        user = self.model(usuario=usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ADMIN')
        return self.create_user(usuario, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado con RBAC integrado.
    Campo de login: 'usuario' (no email).
    """
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('ABOG', 'Abogado'),
        ('USR_PUBLICO', 'Usuario Público'),
    ]

    usuario = models.CharField(max_length=50, unique=True)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(max_length=150, unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    personal = models.ForeignKey(
        'expedientes.Personal', on_delete=models.PROTECT,
        db_column='personal_id', blank=True, null=True
    )
    rol = models.CharField(max_length=12, choices=ROLES, default='USR_PUBLICO')
    foto_perfil = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
    )
    totp_secret = models.CharField(max_length=64, blank=True, null=True)
    frase_seguridad = models.CharField(max_length=255, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)
    intentos_fallidos = models.IntegerField(default=0)
    is_bloqueado = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['cedula']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']

    def get_full_name(self):
        if self.personal_id:
            return self.personal.get_full_name()
        return self.usuario

    def get_short_name(self):
        if self.personal_id:
            return self.personal.nombres
        return self.usuario

    def get_rol_display_label(self):
        """Retorna la etiqueta legible del rol para el sidebar."""
        return dict(self.ROLES).get(self.rol, 'Sin Rol')

    def __str__(self):
        return f"{self.usuario} ({self.get_full_name()})"

    def set_frase_seguridad(self, frase):
        if frase:
            self.frase_seguridad = make_password(frase)
        else:
            self.frase_seguridad = None

    def check_frase_seguridad(self, frase):
        if not self.frase_seguridad or not frase:
            return False
        return check_password(frase, self.frase_seguridad)


class HistorialContrasena(models.Model):
    """Historial inmutable de contraseñas previas (máx. 3 para validación)."""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='historial_contrasenas',
        db_column='usuario_id'
    )
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_contrasenas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Historial #{self.id} - {self.usuario.usuario}"

class SecurityQuestion(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='security_question')
    pregunta = models.CharField(max_length=255)
    respuesta_hash = models.CharField(max_length=255)

    def set_respuesta(self, respuesta):
        self.respuesta_hash = make_password(respuesta)

    def check_respuesta(self, respuesta):
        return check_password(respuesta, self.respuesta_hash)

    class Meta:
        db_table = 'security_questions'


class BitacoraAuditoria(models.Model):
    """
    Bitácora de auditoría inmutable con hashes SHA-256 encadenados.
    Solo INSERT permitido. UPDATE/DELETE prohibidos por middleware.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        db_column='usuario_id'
    )
    fecha_hora = models.DateTimeField(blank=True, null=True)
    accion = models.CharField(max_length=50)
    tipo = models.TextField(blank=True, null=True)
    descripcion = models.TextField()
    registro = models.TextField(blank=True, null=True)
    modulo = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    hash_integridad = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bitacora_auditoria'
        ordering = ['-created_at']

    def __str__(self):
        alerta = f" ⚠ {self.tipo}" if self.tipo else ""
        return f"[{self.created_at}] {self.accion} - {self.modulo}{alerta}"

    @property
    def es_sospechoso(self):
        return bool(self.tipo)

    @property
    def alertas_lista(self):
        if not self.tipo:
            return []
        return [a.strip() for a in self.tipo.split(',') if a.strip()]

    @property
    def ip_formateada(self):
        return self.ip_address or '0.0.0.0'

    @property
    def descripcion_limpia(self):
        """Retorna la descripción en lenguaje natural.
        Transforma automáticamente registros viejos con formato técnico."""
        import re
        d = self.descripcion

        # Honeypot
        if self.accion == 'HONEYPOT' or d.startswith('HONEYPOT_TRAP'):
            return 'Registro de seguridad del sistema'

        # Formato viejo: "Usuario ejecutó POST en la ruta /path/ con código de respuesta 302"
        m = re.match(r'^Usuario ejecutó \w+ en la ruta (.+?) con código de respuesta \d+$', d)
        if m:
            path = m.group(1)
            return self._descripcion_desde_path(path)

        # Formato viejo de middleware intermedio: "POST /path/ -> 302 [ACCION]"
        m2 = re.match(r'^\w+ .+? -> \d+ \[(\w+)\]$', d)
        if m2:
            return self._descripcion_desde_accion(m2.group(1))

        # Si ya está en formato nuevo, devolver tal cual
        return d

    def _descripcion_desde_path(self, path):
        desc_map = {
            'LOGIN_INTENT': 'Inicio de sesión',
            'POST': 'Creación',
            'PUT': 'Edición',
            'PATCH': 'Edición',
            'DELETE': 'Eliminación',
        }
        base = desc_map.get(self.accion, self.accion)
        parts = [p for p in path.split('/') if p and not p.isdigit()]
        recurso = parts[-1] if parts else ''
        if recurso in ('login', 'logout', 'recovery'):
            return "Inicio de sesión"
        if recurso:
            return f"{base}: {recurso}"
        return base

    def _descripcion_desde_accion(self, accion_old):
        old_extra = {
            'LOGIN_INTENT': 'Inicio de sesión',
        }
        if accion_old in old_extra:
            return old_extra[accion_old]
        from apps.infraestructura.middleware import DESCRIPCIONES_POR_ACCION
        return DESCRIPCIONES_POR_ACCION.get(accion_old, accion_old)

    @property
    def usuario_visible(self):
        """Muestra quién realizó la acción de forma legible."""
        import re
        if self.usuario:
            return self.usuario.get_full_name() or self.usuario.usuario
        m = re.search(r'fallido para: (.+)$', self.descripcion)
        if m:
            return f"Intento: {m.group(1)}"
        if self.accion == 'HONEYPOT':
            return 'Sistema'
        return f"Externo ({self.ip_address})"

    @property
    def modulo_display(self):
        nombres = {
            'AUTH': 'Autenticación',
            'EXPEDIENTES': 'Expedientes',
            'DOCUMENTOS': 'Documentos',
            'BIBLIOTECA': 'Biblioteca',
            'USUARIOS': 'Usuarios',
            'CORE': 'Sistema',
            'SYS': 'Sistema',
        }
        return nombres.get(self.modulo, self.modulo)

    @property
    def accion_limpia(self):
        """Transforma acciones viejas (POST, LOGIN_INTENT) a nuevo formato."""
        if self.accion == 'HONEYPOT':
            return 'SEGURIDAD'
        old_map = {
            'POST': 'CREACION',
            'PUT': 'EDICION',
            'PATCH': 'EDICION',
            'DELETE': 'ELIMINACION',
            'GET': 'CONSULTA',
            'LOGIN_INTENT': 'INICIO_SESION',
        }
        return old_map.get(self.accion, self.accion)
