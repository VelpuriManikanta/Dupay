"""RBAC permission classes."""

from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """Allow access only to users with one of the given roles."""

    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_any_role(*self.allowed_roles)


class IsCustomer(HasRole):
    allowed_roles = ["customer"]


class IsAdmin(HasRole):
    allowed_roles = ["admin"]


class IsCompliance(HasRole):
    allowed_roles = ["compliance", "admin"]
    message = "Compliance or admin role required."


class HasPermission(BasePermission):
    """Allow access only to users whose role grants the given permission code."""

    permission_code = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_permission(self.permission_code)


class IsOwnerOrAdmin(BasePermission):
    """Allow access if the user is the owner of the object or an admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.has_any_role("admin"):
            return True
        owner_field = getattr(view, "owner_field", "user")
        owner = getattr(obj, owner_field, None)
        return owner == request.user