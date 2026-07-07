from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class UsuarioBackend(ModelBackend):
    """Backend de autenticación compatible con el campo de login 'usuario'."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('usuario')
        if username is None:
            return None

        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None

        if password is None:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
