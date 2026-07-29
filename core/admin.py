from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Employee,
    ServiceCatalog,
    Activity,
    TaskAssignment,
    WelfareYearlyBudget,
    WelfareDistribution,
    Holiday,
)


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    """Admin for Employee, extending Django's built-in UserAdmin."""

    list_display = (
        "employee_code", "username", "get_full_name", "role",
        "region_code", "supervisor", "is_active",
    )
    list_filter = ("role", "region_code", "province_code", "is_multitasking", "is_active")
    search_fields = ("employee_code", "username", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("اطلاعات سازمانی", {
            "fields": (
                "employee_code", "role", "region_code", "province_code",
                "region_coefficient", "is_multitasking", "multitasking_coefficient",
                "supervisor", "position", "appointed_date",
            )
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "نام کامل"


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ("service_code", "name", "base_swu", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("service_code", "name")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "service", "date_performed", "quantity",
        "adjusted_swu", "status", "is_complexity_approved", "audit_score",
    )
    list_filter = ("status", "is_complexity_approved", "is_audit_selected", "date_performed")
    search_fields = ("employee__employee_code", "service__service_code")
    readonly_fields = ("base_swu_total", "adjusted_swu")
    autocomplete_fields = ("employee", "service", "approved_by")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("description_short", "assigned_by", "assigned_to", "priority", "status", "deadline")
    list_filter = ("priority", "status")
    search_fields = ("description", "assigned_to__employee_code")

    def description_short(self, obj):
        return obj.description[:40]
    description_short.short_description = "شرح"


@admin.register(WelfareYearlyBudget)
class WelfareYearlyBudgetAdmin(admin.ModelAdmin):
    list_display = ("year", "total_budget", "reserved_fund", "distributable_budget", "is_locked")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("title", "jalali_month", "jalali_day", "jalali_year", "is_day_off")
    list_filter = ("is_day_off", "jalali_month")
    search_fields = ("title",)


@admin.register(WelfareDistribution)
class WelfareDistributionAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "annual_adjusted_swu", "distribution_share", "paid")
    list_filter = ("year", "paid")
    search_fields = ("employee__employee_code",)
