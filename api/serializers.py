from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import (
    ServiceCatalog,
    Activity,
    TaskAssignment,
    WelfareYearlyBudget,
    WelfareDistribution,
    Holiday,
)

Employee = get_user_model()


class EmployeeMiniSerializer(serializers.ModelSerializer):
    """Lightweight employee representation used inside nested serializers."""
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "employee_code", "full_name", "role", "region_code", "position"]


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    supervisor_name = serializers.CharField(
        source="supervisor.get_full_name", read_only=True, default=""
    )

    class Meta:
        model = Employee
        fields = [
            "id", "username", "employee_code", "first_name", "last_name", "full_name",
            "role", "region_code", "province_code", "region_coefficient",
            "is_multitasking", "multitasking_coefficient", "supervisor", "supervisor_name",
            "position", "appointed_date", "is_active", "email",
        ]
        extra_kwargs = {"username": {"required": True}}

    def create(self, validated_data):
        # Admin-created employees get a default password equal to their
        # employee_code; they are expected to change it on first login.
        password = validated_data.pop("password", None) or validated_data["employee_code"]
        user = Employee(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ServiceCatalogSerializer(serializers.ModelSerializer):
    is_deletable = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCatalog
        fields = [
            "id", "service_code", "name", "description", "base_swu",
            "is_active", "updated_at", "created_at", "is_deletable",
        ]

    def get_is_deletable(self, obj):
        """A service can only be safely deleted if no Activity or
        TaskAssignment references it yet (see on_delete=PROTECT on models.py).
        Used by the admin UI to show 'Delete' vs 'Deactivate' up front,
        instead of letting the user hit a blocked-delete error."""
        return not obj.activities.exists() and not obj.tasks.exists()


class ActivitySerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    employee_detail = EmployeeMiniSerializer(source="employee", read_only=True)
    service_detail = ServiceCatalogSerializer(source="service", read_only=True)
    # Preview field: what adjusted_swu WOULD be, without saving. Handy for the
    # "live SWU preview" required by ActivityForm.vue.
    preview_adjusted_swu = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id", "employee", "employee_detail", "service", "service_detail",
            "date_performed", "quantity", "base_swu_total",
            "complexity_coefficient", "is_complexity_approved", "approved_by",
            "adjusted_swu", "status", "audit_score", "quality_coefficient",
            "is_audit_selected", "preview_adjusted_swu", "created_at", "updated_at",
        ]
        read_only_fields = [
            "base_swu_total", "adjusted_swu", "is_complexity_approved",
            "approved_by", "status", "audit_score", "quality_coefficient",
            "is_audit_selected",
        ]

    def get_preview_adjusted_swu(self, obj):
        _, adjusted = obj.compute_adjusted_swu()
        return round(adjusted, 3)

    def create(self, validated_data):
        # employee defaults to the requesting user unless a supervisor is
        # logging on behalf of someone else (handled in the view).
        activity = Activity(**validated_data)
        activity.save()  # save() auto-computes base_swu_total / adjusted_swu
        return activity


class ActivityComplexityApprovalSerializer(serializers.Serializer):
    """Payload for the supervisor 'approve/reject complexity' action."""
    approve = serializers.BooleanField()
    complexity_coefficient = serializers.FloatField(required=False, min_value=1.0, max_value=3.0)


class ActivityAuditSerializer(serializers.Serializer):
    """Payload for submitting a quality-audit score for an activity."""
    audit_score = serializers.IntegerField(min_value=0, max_value=100)


class TaskAssignmentSerializer(serializers.ModelSerializer):
    assigned_to_detail = EmployeeMiniSerializer(source="assigned_to", read_only=True)
    assigned_by_detail = EmployeeMiniSerializer(source="assigned_by", read_only=True)
    service_detail = ServiceCatalogSerializer(source="service", read_only=True)

    class Meta:
        model = TaskAssignment
        fields = [
            "id", "assigned_by", "assigned_by_detail", "assigned_to", "assigned_to_detail",
            "service", "service_detail", "description", "priority", "deadline",
            "status", "linked_activity", "created_at", "updated_at",
        ]
        read_only_fields = ["assigned_by"]


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ["id", "title", "jalali_month", "jalali_day", "jalali_year", "is_day_off", "note"]


class WelfareYearlyBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelfareYearlyBudget
        fields = [
            "id", "year", "total_budget", "reserved_fund",
            "distributable_budget", "is_locked", "created_at",
        ]
        read_only_fields = ["distributable_budget", "is_locked"]


class WelfareDistributionSerializer(serializers.ModelSerializer):
    employee_detail = EmployeeMiniSerializer(source="employee", read_only=True)

    class Meta:
        model = WelfareDistribution
        fields = [
            "id", "employee", "employee_detail", "year", "annual_adjusted_swu",
            "distribution_share", "paid", "paid_date", "calculated_at",
        ]
