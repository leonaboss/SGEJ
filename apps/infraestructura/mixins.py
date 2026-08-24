from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin base para restringir acceso por rol. 
    Definido en la infraestructura central.
    """
    required_role = None
    required_roles = None

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.required_roles:
            return self.request.user.rol in self.required_roles
        return self.request.user.rol == self.required_role

    def handle_no_permission(self):
        # Dispara el 403.html centralizado
        raise PermissionDenied(f"Acceso denegado: Se requieren privilegios de {self.required_role}.")

class AdminRequiredMixin(RoleRequiredMixin):
    required_role = 'ADMIN'

class AbogadoRequiredMixin(RoleRequiredMixin):
    required_role = 'ABOG'

class CatalogRequiredMixin(RoleRequiredMixin):
    required_roles = ['ADMIN', 'ABOG']
