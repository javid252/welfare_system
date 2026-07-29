"""
Business-logic services shared between the management command
(`distribute_welfare`), the DRF API, and the admin site. Keeping this logic
out of views/commands means there is exactly one implementation of the
welfare-distribution algorithm and the quality-audit sampling algorithm.
"""

import random
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from .models import Employee, Activity, WelfareYearlyBudget, WelfareDistribution


def recalculate_quality_coefficients(year):
    """
    Recomputes each employee's annual quality_coefficient from the average of
    their audited activity scores in `year`, then re-applies it (and
    recalculates adjusted_swu) to every APPROVED activity of that employee in
    that year.

    quality_coefficient = (average_audit_score / 100) * 0.4 + 0.8
    -> ranges from 0.8 (score 0) to 1.2 (score 100).
    Employees with no audited activities keep a neutral coefficient of 1.0.
    """
    q_min = settings.QUALITY_COEFFICIENT_MIN
    q_max = settings.QUALITY_COEFFICIENT_MAX
    q_span = q_max - q_min

    updated_employees = []
    for employee in Employee.objects.all():
        audited_qs = Activity.objects.filter(
            employee=employee,
            date_performed__year=year,
            audit_score__isnull=False,
        )
        if not audited_qs.exists():
            coefficient = 1.0
        else:
            avg_score = audited_qs.aggregate(avg=Avg("audit_score"))["avg"]
            coefficient = (avg_score / 100.0) * q_span + q_min

        activities = Activity.objects.filter(
            employee=employee, date_performed__year=year, status=Activity.Status.APPROVED
        )
        for activity in activities:
            activity.quality_coefficient = coefficient
            activity.recalculate_and_save(save=True)
        updated_employees.append((employee, coefficient))

    return updated_employees


def select_quality_audit_sample(year, sample_rate=None):
    """
    Randomly flags ~sample_rate (default settings.QUALITY_AUDIT_SAMPLE_RATE,
    i.e. 5%) of each employee's APPROVED activities in `year` for audit, by
    setting is_audit_selected=True. Returns the number of activities flagged.
    """
    sample_rate = sample_rate or settings.QUALITY_AUDIT_SAMPLE_RATE
    flagged_count = 0

    for employee in Employee.objects.all():
        activity_ids = list(
            Activity.objects.filter(
                employee=employee, date_performed__year=year, status=Activity.Status.APPROVED
            ).values_list("id", flat=True)
        )
        if not activity_ids:
            continue
        sample_size = max(1, round(len(activity_ids) * sample_rate)) if activity_ids else 0
        sample_size = min(sample_size, len(activity_ids))
        chosen = set(random.sample(activity_ids, sample_size))
        Activity.objects.filter(id__in=chosen).update(is_audit_selected=True)
        flagged_count += len(chosen)

    return flagged_count


@transaction.atomic
def distribute_welfare(year):
    """
    Runs the full annual welfare distribution for `year`:

    1. Requires a WelfareYearlyBudget row for that year.
    2. Recomputes quality coefficients from audit scores (best-effort; skips
       employees without audits, who keep coefficient 1.0).
    3. For every employee, sums their APPROVED, adjusted SWU for the year.
    4. Employee Share = (employee_adjusted_swu / total_adjusted_swu) * distributable_budget
    5. Persists one WelfareDistribution row per employee and locks the budget.

    Returns the WelfareYearlyBudget instance and a list of WelfareDistribution
    instances created/updated.
    """
    try:
        budget = WelfareYearlyBudget.objects.get(year=year)
    except WelfareYearlyBudget.DoesNotExist:
        raise ValueError(
            f"بودجه سالانه برای سال {year} تعریف نشده است. ابتدا یک WelfareYearlyBudget بسازید."
        )

    recalculate_quality_coefficients(year)

    employee_totals = {}
    total_adjusted_swu = 0.0
    for employee in Employee.objects.all():
        annual_swu = employee.annual_adjusted_swu(year)
        if annual_swu > 0:
            employee_totals[employee.id] = annual_swu
            total_adjusted_swu += annual_swu

    distributable = budget.distributable_budget
    results = []

    if total_adjusted_swu <= 0:
        # No approved activity anywhere this year: nothing to distribute.
        budget.is_locked = True
        budget.save(update_fields=["is_locked"])
        return budget, results

    for employee_id, annual_swu in employee_totals.items():
        raw_share = (Decimal(annual_swu) / Decimal(total_adjusted_swu)) * distributable
        share = raw_share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        distribution, _created = WelfareDistribution.objects.update_or_create(
            employee_id=employee_id,
            year=year,
            defaults={
                "annual_adjusted_swu": annual_swu,
                "distribution_share": share,
            },
        )
        results.append(distribution)

    budget.is_locked = True
    budget.save(update_fields=["is_locked"])
    return budget, results
