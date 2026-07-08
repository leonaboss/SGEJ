from django.contrib import admin
from .models import Usuario, HistorialContrasena, BitacoraAuditoria

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'get_full_name', 'cedula', 'rol',
                    'is_bloqueado', 'is_active', 'is_2fa_enabled', 'created_at']
    list_filter = ['rol', 'is_bloqueado', 'is_active', 'is_2fa_enabled']
    search_fields = ['usuario', 'cedula', 'correo', 'personal__nombres', 'personal__apellidos']
    ordering = ['-created_at']

@admin.register(HistorialContrasena)
class HistorialContrasenaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'created_at']
    list_filter = ['created_at']
    search_fields = ['usuario__usuario']
    readonly_fields = ['password_hash']

@admin.register(BitacoraAuditoria)
class BitacoraAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['accion', 'modulo', 'usuario', 'ip_address', 'created_at']
    list_filter = ['accion', 'modulo', 'created_at']
    search_fields = ['descripcion', 'usuario__usuario', 'ip_address']
    readonly_fields = ['hash_integridad', 'created_at']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.rol == 'ADMIN'
    
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
