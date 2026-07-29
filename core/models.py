"""
Core data models for the Performance Management and Fair Welfare Distribution
System (سامانه مدیریت عملکرد و توزیع عادلانه رفاهی).

Design notes
------------
* ``Employee`` extends Django's ``AbstractUser`` and is set as
  ``AUTH_USER_MODEL``. Organizational hierarchy (employee -> supervisor ->
  provincial manager -> admin) is modelled with a self-referencing FK plus a
  ``role`` field used for RBAC via Django Groups/permissions.
* All monetary values use ``DecimalField`` to avoid floating point rounding
  errors in the welfare distribution calculation. Work-unit coefficients use
  ``FloatField`` since they are ratios, not currency.
* Every model that participates in the SWU calculation exposes a
  ``recalculate_adjusted_swu`` helper so the same logic is reused by the API,
  the admin, and the management command (single source of truth).
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    """Organizational role used for RBAC decisions across the system."""
    EMPLOYEE = "EMPLOYEE", "کارمند"
    SUPERVISOR = "SUPERVISOR", "سرپرست شهرستان"
    PROVINCIAL_MANAGER = "PROVINCIAL_MANAGER", "مدیر استانی"
    ADMIN = "ADMIN", "کمیته ملی (ادمین)"


class Employee(AbstractUser):
    """
    Extends Django's built-in user model with organizational and
    welfare-calculation attributes.
    """

    employee_code = models.CharField(
        "کد پرسنلی", max_length=20, unique=True, db_index=True
    )
    role = models.CharField(
        "نقش سازمانی", max_length=20, choices=Role.choices, default=Role.EMPLOYEE
    )
    region_code = models.CharField("کد منطقه/شهرستان", max_length=20, db_index=True)
    province_code = models.CharField(
        "کد استان", max_length=20, db_index=True, blank=True
    )
    region_coefficient = models.FloatField(
        "ضریب منطقه",
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="ضریب ثابت منطقه که توسط کمیته ملی تعیین می‌شود.",
    )
    is_multitasking = models.BooleanField("چندوظیفه‌ای", default=False)
    multitasking_coefficient = models.FloatField(
        "ضریب چندوظیفگی",
        default=1.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(2.0)],
    )
    supervisor = models.ForeignKey(
        "self",
        verbose_name="سرپرست مستقیم",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subordinates",
    )
    position = models.CharField("سمت سازمانی", max_length=100, blank=True)
    appointed_date = models.DateField("تاریخ انتصاب", null=True, blank=True)

    class Meta:
        verbose_name = "کارمند"
        verbose_name_plural = "کارمندان"
        ordering = ["employee_code"]

    def __str__(self):
        full_name = self.get_full_name() or self.username
        return f"{full_name} ({self.employee_code})"

    @property
    def effective_multitasking_coefficient(self):
        """Multitasking coefficient only applies if the flag is set."""
        return self.multitasking_coefficient if self.is_multitasking else 1.0

    def annual_adjusted_swu(self, year):
        """
        Sum of adjusted SWU for all APPROVED activities of this employee in a
        given year, after the annual quality coefficient has been applied.
        Mirrors the formula documented in WelfareDistribution.
        """
        total = self.activities.filter(
            date_performed__year=year, status=Activity.Status.APPROVED
        ).aggregate(total=models.Sum("adjusted_swu"))["total"]
        return total or 0.0


class ServiceCatalog(models.Model):
    """A catalog of billable/measurable services, each with a base SWU."""

    service_code = models.CharField("کد خدمت", max_length=20, unique=True)
    name = models.CharField("نام خدمت", max_length=255)
    description = models.TextField("شرح خدمت", blank=True)
    base_swu = models.FloatField(
        "واحد کار استاندارد پایه", validators=[MinValueValidator(0.0)]
    )
    is_active = models.BooleanField("فعال", default=True)
    updated_at = models.DateTimeField("آخرین به‌روزرسانی", auto_now=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "خدمت (کاتالوگ)"
        verbose_name_plural = "کاتالوگ خدمات"
        ordering = ["service_code"]

    def __str__(self):
        return f"{self.service_code} — {self.name}"


class Activity(models.Model):
    """
    A single logged unit of completed work by an employee, tied to a service
    from the catalog. This is where the core SWU calculation happens.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار تایید"
        APPROVED = "APPROVED", "تایید شده"
        REJECTED = "REJECTED", "رد شده"

    employee = models.ForeignKey(
        Employee, verbose_name="کارمند", on_delete=models.CASCADE, related_name="activities"
    )
    service = models.ForeignKey(
        ServiceCatalog, verbose_name="خدمت", on_delete=models.PROTECT, related_name="activities"
    )
    date_performed = models.DateField("تاریخ انجام", default=timezone.localdate)
    quantity = models.PositiveIntegerField("تعداد", default=1)

    base_swu_total = models.FloatField("مجموع واحد کار پایه", default=0.0, editable=False)
    complexity_coefficient = models.FloatField(
        "ضریب پیچیدگی درخواستی",
        default=1.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(3.0)],
    )
    is_complexity_approved = models.BooleanField("ضریب پیچیدگی تایید شده", default=False)
    approved_by = models.ForeignKey(
        Employee,
        verbose_name="تاییدکننده",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_activities",
    )

    adjusted_swu = models.FloatField("واحد کار تعدیل‌شده", default=0.0, editable=False)
    status = models.CharField(
        "وضعیت", max_length=10, choices=Status.choices, default=Status.PENDING
    )

    audit_score = models.PositiveSmallIntegerField(
        "امتیاز ممیزی کیفیت",
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    quality_coefficient = models.FloatField(
        "ضریب کیفیت اعمال‌شده",
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(1.5)],
    )
    is_audit_selected = models.BooleanField("انتخاب‌شده برای ممیزی", default=False)

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "فعالیت ثبت‌شده"
        verbose_name_plural = "فعالیت‌های ثبت‌شده"
        ordering = ["-date_performed", "-created_at"]
        indexes = [
            models.Index(fields=["employee", "date_performed"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.employee.employee_code} - {self.service.service_code} - {self.date_performed}"

    def compute_adjusted_swu(self):
        """
        Applies the fair-distribution SWU formula:

            base_swu_total   = service.base_swu * quantity
            complexity_factor = complexity_coefficient (only if approved, else 1.0)
            Adjusted SWU = base_swu_total
                           * complexity_factor
                           * employee.region_coefficient
                           * employee.effective_multitasking_coefficient
                           * quality_coefficient

        Returns the computed value without saving (pure function), so callers
        (API, admin, management command) decide when to persist it.
        """
        base_total = self.service.base_swu * self.quantity
        complexity_factor = self.complexity_coefficient if self.is_complexity_approved else 1.0
        adjusted = (
            base_total
            * complexity_factor
            * self.employee.region_coefficient
            * self.employee.effective_multitasking_coefficient
            * self.quality_coefficient
        )
        return base_total, adjusted

    def recalculate_and_save(self, save=True):
        """Recomputes base_swu_total and adjusted_swu, optionally persisting."""
        self.base_swu_total, self.adjusted_swu = self.compute_adjusted_swu()
        if save:
            self.save(update_fields=["base_swu_total", "adjusted_swu"])
        return self.adjusted_swu

    def save(self, *args, **kwargs):
        # Always keep the calculated fields consistent before saving,
        # EXCEPT when the caller explicitly restricts update_fields to avoid
        # infinite recursion from recalculate_and_save().
        update_fields = kwargs.get("update_fields")
        if not update_fields:
            self.base_swu_total, self.adjusted_swu = self.compute_adjusted_swu()
        super().save(*args, **kwargs)


class TaskAssignment(models.Model):
    """A task assigned by a supervisor to a subordinate (or self-assigned)."""

    class Priority(models.TextChoices):
        LOW = "LOW", "کم"
        MEDIUM = "MEDIUM", "متوسط"
        HIGH = "HIGH", "بالا"

    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار"
        IN_PROGRESS = "IN_PROGRESS", "در حال انجام"
        COMPLETED = "COMPLETED", "تکمیل‌شده"
        REJECTED = "REJECTED", "رد شده"

    assigned_by = models.ForeignKey(
        Employee, verbose_name="محول‌کننده", on_delete=models.CASCADE, related_name="tasks_assigned"
    )
    assigned_to = models.ForeignKey(
        Employee, verbose_name="مسئول انجام", on_delete=models.CASCADE, related_name="tasks_received"
    )
    service = models.ForeignKey(
        ServiceCatalog, verbose_name="خدمت مرتبط", on_delete=models.PROTECT, related_name="tasks"
    )
    description = models.TextField("شرح وظیفه", blank=True)
    priority = models.CharField(
        "اولویت", max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    deadline = models.DateField("مهلت انجام")
    status = models.CharField(
        "وضعیت", max_length=15, choices=Status.choices, default=Status.PENDING
    )
    linked_activity = models.ForeignKey(
        Activity,
        verbose_name="فعالیت ثبت‌شده مرتبط",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_task",
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین به‌روزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تخصیص وظیفه"
        verbose_name_plural = "تخصیص وظایف"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.description[:30]} -> {self.assigned_to.employee_code}"


class WelfareYearlyBudget(models.Model):
    """The annual welfare budget pool set by the national committee."""

    year = models.PositiveIntegerField("سال", unique=True)
    total_budget = models.DecimalField("بودجه کل رفاهی", max_digits=18, decimal_places=2)
    reserved_fund = models.DecimalField(
        "ذخیره موارد خاص", max_digits=18, decimal_places=2, default=0
    )
    distributable_budget = models.DecimalField(
        "بودجه قابل توزیع", max_digits=18, decimal_places=2, editable=False, default=0
    )
    is_locked = models.BooleanField(
        "قفل‌شده (پس از محاسبه نهایی)", default=False,
        help_text="پس از اجرای محاسبه توزیع، این بودجه قفل می‌شود.",
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "بودجه سالانه رفاهی"
        verbose_name_plural = "بودجه‌های سالانه رفاهی"
        ordering = ["-year"]

    def __str__(self):
        return f"بودجه رفاهی سال {self.year}"

    def save(self, *args, **kwargs):
        self.distributable_budget = self.total_budget - self.reserved_fund
        super().save(*args, **kwargs)


class Holiday(models.Model):
    """
    An official holiday or commemorative occasion on the system's own,
    independent Jalali calendar (see core/jalali_utils.py).

    Two kinds of entries are supported:
      * Yearly-recurring, Jalali-calendar-fixed days (the vast majority of
        Iran's civil holidays, e.g. Nowruz on 1 Farvardin): set
        `jalali_month` + `jalali_day` and leave `jalali_year` empty.
      * One-off, year-specific days (needed for the Hijri-lunar-based
        religious holidays, whose Jalali date shifts every year and must be
        entered manually for each year): set `jalali_year` as well.
    """

    title = models.CharField("عنوان مناسبت/تعطیلی", max_length=200)
    jalali_month = models.PositiveSmallIntegerField(
        "ماه (شمسی)", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    jalali_day = models.PositiveSmallIntegerField(
        "روز (شمسی)", validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    jalali_year = models.PositiveIntegerField(
        "سال شمسی (خالی = هرساله تکرار می‌شود)", null=True, blank=True
    )
    is_day_off = models.BooleanField("تعطیل رسمی (نه فقط مناسبت)", default=True)
    note = models.TextField("توضیحات", blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "تعطیلات و مناسبت‌ها"
        verbose_name_plural = "تعطیلات و مناسبت‌ها"
        unique_together = ("jalali_month", "jalali_day", "jalali_year")
        ordering = ["jalali_month", "jalali_day"]

    def __str__(self):
        year_part = f"/{self.jalali_year}" if self.jalali_year else " (هرساله)"
        return f"{self.jalali_month:02d}/{self.jalali_day:02d}{year_part} — {self.title}"


class WelfareDistribution(models.Model):
    """
    The calculated welfare share of a single employee for a given year.
    One row is (re)created per employee each time
    `manage.py distribute_welfare --year YYYY` is run.
    """

    employee = models.ForeignKey(
        Employee, verbose_name="کارمند", on_delete=models.CASCADE, related_name="welfare_shares"
    )
    year = models.PositiveIntegerField("سال")
    annual_adjusted_swu = models.FloatField("مجموع واحد کار تعدیل‌شده سالانه", default=0.0)
    distribution_share = models.DecimalField(
        "سهم محاسبه‌شده", max_digits=18, decimal_places=2, default=0
    )
    paid = models.BooleanField("پرداخت‌شده", default=False)
    paid_date = models.DateField("تاریخ پرداخت", null=True, blank=True)
    calculated_at = models.DateTimeField("تاریخ محاسبه", auto_now=True)

    class Meta:
        verbose_name = "سهم توزیع رفاهی"
        verbose_name_plural = "سهم‌های توزیع رفاهی"
        unique_together = ("employee", "year")
        ordering = ["-year", "-distribution_share"]

    def __str__(self):
        return f"{self.employee.employee_code} - {self.year}: {self.distribution_share}"



