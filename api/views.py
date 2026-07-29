"""
DRF API views.

Grouped into:
  * Auth endpoints            (/api/auth/...)
  * CRUD viewsets              (/api/employees/, /api/services/, /api/tasks/, ...)
  * Activity actions           (approve-complexity, submit-audit)
  * Dashboard aggregation      (/api/dashboard/...)
  * Welfare distribution       (/api/distribution/...)
"""

from datetime import date

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db.models import Sum, Avg, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models.deletion import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend

from core.models import (
    ServiceCatalog, Activity, TaskAssignment, WelfareYearlyBudget, WelfareDistribution, Holiday,
)
from core.jalali_utils import jalali_to_date
from core.permissions import is_admin, is_supervisor_or_above, get_subordinate_ids
from core.services import distribute_welfare, select_quality_audit_sample

from .serializers import (
    EmployeeSerializer, ServiceCatalogSerializer, ActivitySerializer,
    ActivityComplexityApprovalSerializer, ActivityAuditSerializer,
    TaskAssignmentSerializer, WelfareYearlyBudgetSerializer, WelfareDistributionSerializer,
    HolidaySerializer,
)
from .permissions import IsAdmin, IsAdminOrReadOnly, IsSupervisorOrAbove, IsOwnerOrSupervisor

Employee = get_user_model()


# =========================================================================
# AUTH  — /api/auth/
# =========================================================================

class LoginAPIView(APIView):
    """AJAX-friendly login endpoint (in addition to the HTML login page)."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "نام کاربری یا رمز عبور نادرست است."}, status=400)
        login(request, user)
        return Response(EmployeeSerializer(user).data)


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=204)


class ProfileAPIView(APIView):
    def get(self, request):
        return Response(EmployeeSerializer(request.user).data)


# =========================================================================
# CRUD VIEWSETS
# =========================================================================

class EmployeeViewSet(viewsets.ModelViewSet):
    """Full CRUD restricted to admins; supervisors+ get read access to their scope."""
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["role", "region_code", "province_code", "supervisor"]
    search_fields = ["employee_code", "username", "first_name", "last_name"]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        user = self.request.user
        if is_admin(user):
            return Employee.objects.all().order_by("employee_code")
        if is_supervisor_or_above(user):
            return Employee.objects.filter(id__in=get_subordinate_ids(user)).order_by("employee_code")
        return Employee.objects.filter(id=user.id)


class ServiceCatalogViewSet(viewsets.ModelViewSet):
    """Read for everyone authenticated; write (CRUD) restricted to admins/committee."""
    queryset = ServiceCatalog.objects.all().order_by("service_code")
    serializer_class = ServiceCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active"]
    search_fields = ["service_code", "name"]

    def destroy(self, request, *args, **kwargs):
        """
        ServiceCatalog is protected (on_delete=PROTECT) from Activity/TaskAssignment
        so historical work-unit records are never silently orphaned. If a service
        has any linked activities or tasks, deleting it is blocked; the admin is
        told to deactivate it (is_active=False) instead, which hides it from new
        registrations while preserving all historical calculations.
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "این خدمت در فعالیت‌ها یا وظایف ثبت‌شده استفاده شده و برای حفظ "
                        "صحت سوابق محاسباتی قابل حذف نیست. به‌جای حذف، می‌توانید آن را "
                        "«غیرفعال» کنید تا از فهرست انتخاب خدمات جدید حذف شود، بدون آنکه "
                        "سوابق قبلی خراب شوند."
                    ),
                    "code": "protected",
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActivityViewSet(viewsets.ModelViewSet):
    """
    List/create/update activities, plus custom actions for the supervisor
    workflows: approving a complexity coefficient and submitting an audit
    score.
    """
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSupervisor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "service", "status", "date_performed", "is_audit_selected"]

    def get_queryset(self):
        user = self.request.user
        qs = Activity.objects.select_related("employee", "service")
        if is_supervisor_or_above(user):
            return qs.filter(employee_id__in=get_subordinate_ids(user))
        return qs.filter(employee=user)

    def perform_create(self, serializer):
        # Employees register their own activities; supervisors may register
        # on behalf of a subordinate by passing `employee` explicitly.
        employee = serializer.validated_data.get("employee") or self.request.user
        if employee != self.request.user and not is_supervisor_or_above(self.request.user):
            employee = self.request.user
        serializer.save(employee=employee, status=Activity.Status.APPROVED)

    @action(detail=True, methods=["post"], url_path="approve-complexity")
    def approve_complexity(self, request, pk=None):
        """Supervisor approves/rejects the employee's requested complexity coefficient."""
        activity = self.get_object()
        if not is_supervisor_or_above(request.user):
            return Response({"detail": "فقط سرپرست مجاز به تایید ضریب پیچیدگی است."}, status=403)

        serializer = ActivityComplexityApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        coefficient = serializer.validated_data.get("complexity_coefficient")

        activity.is_complexity_approved = approve
        if approve:
            # Supervisor may correct the employee's requested value before approving.
            if coefficient is not None:
                activity.complexity_coefficient = coefficient
        else:
            # Rejection resets the coefficient to neutral (1.0): it both removes
            # the activity from the pending queue (queue filters on
            # complexity_coefficient__gt=1.0) and guarantees no bonus is ever
            # applied for a rejected request, regardless of is_complexity_approved.
            activity.complexity_coefficient = 1.0
        activity.approved_by = request.user
        activity.recalculate_and_save(save=False)
        activity.save()

        return Response(ActivitySerializer(activity).data)

    @action(detail=True, methods=["post"], url_path="submit-audit")
    def submit_audit(self, request, pk=None):
        """Auditor/supervisor submits a quality score (0-100) for a flagged activity."""
        activity = self.get_object()
        if not is_supervisor_or_above(request.user):
            return Response({"detail": "فقط سرپرست/ممیز مجاز به ثبت امتیاز ممیزی است."}, status=403)

        serializer = ActivityAuditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity.audit_score = serializer.validated_data["audit_score"]
        activity.save(update_fields=["audit_score"])
        return Response(ActivitySerializer(activity).data)

    @action(detail=False, methods=["get"], url_path="audit-queue")
    def audit_queue(self, request):
        """Activities flagged for quality audit that don't have a score yet."""
        qs = self.get_queryset().filter(is_audit_selected=True, audit_score__isnull=True)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="pending-complexity")
    def pending_complexity(self, request):
        """Activities with a requested (not-yet-approved) complexity coefficient > 1.0."""
        qs = self.get_queryset().filter(is_complexity_approved=False, complexity_coefficient__gt=1.0)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSupervisor]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["assigned_to", "assigned_by", "status", "priority"]

    def get_queryset(self):
        user = self.request.user
        qs = TaskAssignment.objects.select_related("assigned_to", "assigned_by", "service")
        if is_supervisor_or_above(user):
            return qs.filter(
                Q(assigned_to_id__in=get_subordinate_ids(user)) | Q(assigned_by=user)
            )
        return qs.filter(assigned_to=user)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class HolidayViewSet(viewsets.ModelViewSet):
    """
    CRUD for official holidays/occasions on the system's own Jalali calendar.
    Read access for any authenticated user (the date-picker needs it to
    highlight days); write access restricted to admins.
    """
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"], url_path="resolved")
    def resolved(self, request):
        """
        Expands every holiday (recurring or year-specific) into a concrete
        Gregorian date for the requested Jalali year, e.g.:
            GET /api/holidays/resolved/?jalali_year=1405
        Recurring holidays (jalali_year is null) are repeated for every year
        requested; year-specific ones only appear for their exact year.
        Used by the Jalali date-picker widget to shade holidays on the grid.
        """
        jalali_year = request.query_params.get("jalali_year")
        if not jalali_year:
            return Response({"detail": "پارامتر jalali_year الزامی است."}, status=400)
        jalali_year = int(jalali_year)

        results = []
        for holiday in Holiday.objects.filter(
            Q(jalali_year=jalali_year) | Q(jalali_year__isnull=True)
        ):
            try:
                gdate = jalali_to_date(jalali_year, holiday.jalali_month, holiday.jalali_day)
            except ValueError:
                continue  # e.g. 30 Esfand on a non-leap year
            results.append({
                "id": holiday.id,
                "title": holiday.title,
                "jalali_year": jalali_year,
                "jalali_month": holiday.jalali_month,
                "jalali_day": holiday.jalali_day,
                "is_day_off": holiday.is_day_off,
                "gregorian_date": gdate.isoformat(),
                "note": holiday.note,
            })
        return Response(results)


class WelfareYearlyBudgetViewSet(viewsets.ModelViewSet):
    queryset = WelfareYearlyBudget.objects.all()
    serializer_class = WelfareYearlyBudgetSerializer
    permission_classes = [IsAdmin]


class WelfareDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WelfareDistributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year", "paid"]

    def get_queryset(self):
        user = self.request.user
        qs = WelfareDistribution.objects.select_related("employee")
        if is_supervisor_or_above(user):
            return qs.filter(employee_id__in=get_subordinate_ids(user))
        return qs.filter(employee=user)

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin], url_path="run")
    def run_distribution(self, request):
        """Admin-triggered: python manage.py distribute_welfare --year YYYY, via API."""
        year = request.data.get("year")
        if not year:
            return Response({"detail": "سال الزامی است."}, status=400)
        try:
            budget, results = distribute_welfare(int(year))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({
            "year": int(year),
            "employees_paid_count": len(results),
            "distributable_budget": budget.distributable_budget,
            "is_locked": budget.is_locked,
        })

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin], url_path="select-audit-sample")
    def run_audit_sampling(self, request):
        year = request.data.get("year")
        if not year:
            return Response({"detail": "سال الزامی است."}, status=400)
        flagged = select_quality_audit_sample(int(year))
        return Response({"year": int(year), "flagged_count": flagged})


# =========================================================================
# DASHBOARD AGGREGATION — /api/dashboard/
# =========================================================================

class EmployeeSummaryView(APIView):
    """
    Employee dashboard: total raw SWU, adjusted SWU, activity count,
    estimated welfare share, and average quality score for a given year.
    """

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        employee_id = request.query_params.get("employee_id")

        target = request.user
        if employee_id and (is_supervisor_or_above(request.user) or is_admin(request.user)):
            allowed_ids = get_subordinate_ids(request.user)
            if int(employee_id) in allowed_ids:
                target = Employee.objects.get(id=employee_id)

        activities = Activity.objects.filter(employee=target, date_performed__year=year)
        approved = activities.filter(status=Activity.Status.APPROVED)

        raw_swu = approved.aggregate(total=Sum("base_swu_total"))["total"] or 0
        adjusted_swu = approved.aggregate(total=Sum("adjusted_swu"))["total"] or 0
        avg_quality_score = approved.filter(audit_score__isnull=False).aggregate(
            avg=Avg("audit_score")
        )["avg"]

        try:
            distribution = WelfareDistribution.objects.get(employee=target, year=year)
            estimated_share = distribution.distribution_share
        except WelfareDistribution.DoesNotExist:
            estimated_share = None

        return Response({
            "employee": EmployeeSerializer(target).data,
            "year": year,
            "raw_swu_total": raw_swu,
            "adjusted_swu_total": adjusted_swu,
            "activity_count": approved.count(),
            "pending_activity_count": activities.filter(status=Activity.Status.PENDING).count(),
            "average_quality_score": avg_quality_score,
            "estimated_welfare_share": estimated_share,
        })


class TeamPerformanceView(APIView):
    """
    Supervisor dashboard: metrics for every subordinate, plus a histogram
    (bucketed) of adjusted-SWU distribution, and task status counts.
    """
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        subordinate_ids = [
            eid for eid in get_subordinate_ids(request.user) if eid != request.user.id
        ] or get_subordinate_ids(request.user)

        rows = []
        swu_values = []
        for employee in Employee.objects.filter(id__in=subordinate_ids):
            adjusted = employee.annual_adjusted_swu(year)
            swu_values.append(adjusted)
            rows.append({
                "employee": EmployeeSerializer(employee).data,
                "adjusted_swu": adjusted,
                "activity_count": employee.activities.filter(
                    date_performed__year=year, status=Activity.Status.APPROVED
                ).count(),
            })

        histogram = _build_histogram(swu_values, bucket_count=6)

        task_status_counts = list(
            TaskAssignment.objects.filter(assigned_to_id__in=subordinate_ids)
            .values("status").annotate(count=Count("id"))
        )

        return Response({
            "year": year,
            "team": rows,
            "histogram": histogram,
            "task_status_counts": task_status_counts,
        })


class ProvinceHeatmapView(APIView):
    """
    Provincial/national dashboard: average adjusted SWU per employee grouped
    by region (city) and province, for heatmap visualization.
    """
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        activities = Activity.objects.filter(
            date_performed__year=year, status=Activity.Status.APPROVED
        )

        by_region = (
            activities.values("employee__region_code", "employee__province_code")
            .annotate(
                total_adjusted_swu=Sum("adjusted_swu"),
                employee_count=Count("employee", distinct=True),
            )
            .order_by("employee__province_code", "employee__region_code")
        )

        heatmap = [
            {
                "region_code": row["employee__region_code"],
                "province_code": row["employee__province_code"],
                "average_adjusted_swu": (
                    row["total_adjusted_swu"] / row["employee_count"]
                    if row["employee_count"] else 0
                ),
                "employee_count": row["employee_count"],
            }
            for row in by_region
        ]
        return Response({"year": year, "heatmap": heatmap})


class TrendsView(APIView):
    """Monthly trend of total adjusted SWU (for line charts), scoped to the
    requester's authority (own team, province, or everyone for admins)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        allowed_ids = get_subordinate_ids(request.user)

        monthly = (
            Activity.objects.filter(
                employee_id__in=allowed_ids,
                date_performed__year=year,
                status=Activity.Status.APPROVED,
            )
            .annotate(month=TruncMonth("date_performed"))
            .values("month")
            .annotate(total_adjusted_swu=Sum("adjusted_swu"), activity_count=Count("id"))
            .order_by("month")
        )
        return Response({"year": year, "monthly": list(monthly)})


def _build_histogram(values, bucket_count=6):
    """Small helper: bucket a list of floats into `bucket_count` equal-width
    ranges and return [{range, count}], used for Chart.js bar charts."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [{"range_low": lo, "range_high": lo, "count": len(values)}]
    width = (hi - lo) / bucket_count
    buckets = [0] * bucket_count
    for v in values:
        idx = min(int((v - lo) / width), bucket_count - 1)
        buckets[idx] += 1
    return [
        {"range_low": round(lo + i * width, 1), "range_high": round(lo + (i + 1) * width, 1), "count": buckets[i]}
        for i in range(bucket_count)
    ]
