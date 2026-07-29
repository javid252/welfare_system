"""Custom DRF permission classes built on top of core.permissions helpers."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.permissions import is_admin, is_supervisor_or_above


class IsAdmin(BasePermission):
    """Full access restricted to the national committee / superusers."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsSupervisorOrAbove(BasePermission):
    """Supervisors, provincial managers and admins."""

    def has_permission(self, request, view):
        return is_supervisor_or_above(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Anyone authenticated can read (e.g. the service catalog);
    only admins can create/update/delete."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return is_admin(request.user)


class IsOwnerOrSupervisor(BasePermission):
    """
    Object-level permission: the employee who owns the record, or a
    supervisor/manager/admin with authority over that employee, may act on it.
    """

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "employee", None) or getattr(obj, "assigned_to", None)
        if owner is None:
            return is_supervisor_or_above(request.user)
        if owner_id_matches(request.user, owner):
            return True
        return is_supervisor_or_above(request.user)


def owner_id_matches(user, owner):
    return user.id == owner.id
