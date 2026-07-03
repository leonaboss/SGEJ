from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('recovery/', views.RecoveryView.as_view(), name='recovery'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('perfil/eliminar-foto/', views.ProfileDeleteFotoView.as_view(), name='profile_delete_foto'),
    path('perfil/cambiar-password/', views.PasswordChangeView.as_view(), name='change_password'),
    path('2fa/verify/', views.TOTPVerifyView.as_view(), name='totp_verify'),
    path('2fa/setup/', views.Setup2FAView.as_view(), name='setup_2fa'),
    path('2fa/disable/', views.Disable2FAView.as_view(), name='disable_2fa'),
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/crear/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/editar/<int:pk>/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/toggle-bloqueo/<int:pk>/', views.UsuarioToggleBlockView.as_view(), name='usuario_toggle_block'),
    path('2fa/confirm-block/', views.ConfirmBlock2FAView.as_view(), name='confirm_block_2fa'),
    path('recovery/reset/', views.RecoveryResetView.as_view(), name='recovery_reset'),
    path('usuarios/eliminar/<int:pk>/', views.UsuarioDeleteView.as_view(), name='usuario_delete'),
    path('exportar/usuarios/', views.ExportarUsuariosExcelView.as_view(), name='exportar_usuarios'),
    path('importar/usuarios/', views.ImportarUsuariosExcelView.as_view(), name='importar_usuarios'),
    path('bitacora/', views.BitacoraListView.as_view(), name='bitacora_list'),
]
