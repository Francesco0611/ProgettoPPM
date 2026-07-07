from rest_framework import permissions

class IsStoreManager(permissions.BasePermission):
    """
    Allows access only to store managers or admins.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ['manager', 'admin'] or request.user.is_superuser or request.user.is_staff)
        )

class IsCustomer(permissions.BasePermission):
    """
    Allows access only to customers or admins.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ['customer', 'admin'] or request.user.is_superuser)
        )

class IsAdminUserOnly(permissions.BasePermission):
    """
    Allows access only to admins (admin role or is_superuser).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_superuser)
        )
