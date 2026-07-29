"""
Custom management command:

    python manage.py distribute_welfare --year 2026
    python manage.py distribute_welfare --year 2026 --select-audit-sample

Runs the annual "fair welfare distribution" calculation described in the
project spec. Delegates all actual logic to core.services so the exact same
code path is used by the API's "run distribution" admin action.
"""

from django.core.management.base import BaseCommand, CommandError

from core.services import distribute_welfare, select_quality_audit_sample


class Command(BaseCommand):
    help = "Runs the annual welfare distribution calculation for a given year."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year", type=int, required=True, help="سالی که محاسبه توزیع برای آن اجرا می‌شود."
        )
        parser.add_argument(
            "--select-audit-sample",
            action="store_true",
            help="پیش از محاسبه، ابتدا نمونه ۵٪ ممیزی کیفیت را برای این سال انتخاب می‌کند.",
        )

    def handle(self, *args, **options):
        year = options["year"]

        if options["select_audit_sample"]:
            flagged = select_quality_audit_sample(year)
            self.stdout.write(self.style.SUCCESS(
                f"{flagged} فعالیت برای ممیزی کیفیت سال {year} انتخاب شد."
            ))

        try:
            budget, results = distribute_welfare(year)
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(
            f"توزیع رفاهی سال {year} برای {len(results)} کارمند با موفقیت محاسبه شد."
        ))
        self.stdout.write(
            f"بودجه قابل توزیع: {budget.distributable_budget:,.0f} | بودجه قفل شد: {budget.is_locked}"
        )
        for dist in sorted(results, key=lambda d: d.distribution_share, reverse=True)[:10]:
            self.stdout.write(
                f"  - {dist.employee.employee_code}: SWU={dist.annual_adjusted_swu:.2f} "
                f"=> سهم={dist.distribution_share:,.0f}"
            )
