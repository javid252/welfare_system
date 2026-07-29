"""
Role-based access-control helpers shared by the template views (core/views.py)
and the DRF API views (api/views.py). Kept in one place so permission rules
are defined only once.
"""

from .models import Role


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == Role.ADMIN)


def is_provincial_manager(user):
    return user.is_authenticated and user.role == Role.PROVINCIAL_MANAGER


def is_supervisor(user):
    return user.is_authenticated and user.role == Role.SUPERVISOR


def is_supervisor_or_above(user):
    return user.is_authenticated and (
        is_admin(user) or is_provincial_manager(user) or is_supervisor(user)
    )


def get_subordinate_ids(employee):
    """
    Returns the list of employee IDs that `employee` may manage:
    - ADMIN: everyone
    - PROVINCIAL_MANAGER: everyone in the same province
    - SUPERVISOR: direct subordinates
    - EMPLOYEE: only themselves
    """
    from .models import Employee  # local import to avoid circular import

    if is_admin(employee):
        return list(Employee.objects.values_list("id", flat=True))
    if is_provincial_manager(employee):
        return list(
            Employee.objects.filter(province_code=employee.province_code).values_list(
                "id", flat=True
            )
        )
    if is_supervisor(employee):
        return list(employee.subordinates.values_list("id", flat=True)) + [employee.id]
    return [employee.id]
