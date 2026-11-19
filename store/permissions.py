from rest_framework.permissions import SAFE_METHODS, BasePermission


class EsAdministradorOrReadOnly(BasePermission):
    """Lectura para cualquier usuario autenticado,
    escritura (crear/editar/borrar) solo para Administrador."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_staff or user.is_superuser
