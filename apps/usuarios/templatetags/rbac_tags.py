"""
Template tags para control RBAC en plantillas Django.
Uso: {% load rbac_tags %} → {% has_role 'ADMIN' %} ... {% end_has_role %}
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_has_role(context, *roles):
    """
    Verifica si el usuario actual tiene alguno de los roles especificados.
    Uso: {% user_has_role 'ADMIN' 'ABOG' as is_manager %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return request.user.rol in roles


@register.filter
def has_role(user, role_string):
    """
    Filtro para verificar rol en condicionales.
    Uso: {% if request.user|has_role:'ADMIN,COORD' %}
    """
    if not user or not user.is_authenticated:
        return False
    roles = [r.strip() for r in role_string.split(',')]
    return user.rol in roles


@register.inclusion_tag('components/sidebar_item.html', takes_context=True)
def sidebar_item(context, url, icon, label, active_module=None, required_roles=None, **kwargs):
    """
    Renderiza un item del sidebar con verificación RBAC.
    Solo muestra el item si el usuario tiene el rol requerido.
    Acepta kwargs adicionales (ej: tipo_modulo) que se pasan como args a reverse().
    """
    request = context.get('request')
    user = request.user if request else None
    is_visible = not required_roles

    if required_roles and user and user.is_authenticated:
        allowed = [r.strip() for r in required_roles.split(',')]
        is_visible = user.rol in allowed

    is_active = False
    if active_module and request:
        is_active = active_module in request.path

    from django.urls import reverse
    try:
        resolved_url = reverse(url, kwargs=kwargs)
    except Exception:
        resolved_url = url

    return {
        'url': resolved_url,
        'icon': icon,
        'label': label,
        'is_active': is_active,
        'is_visible': is_visible,
    }
