"""
Seeds the well-known official Iranian holidays that are FIXED on the Jalali
calendar (i.e. fall on the same Jalali month/day every year). These are the
easy, unambiguous ones.

Lunar-Hijri-based religious holidays (Eid al-Fitr, Eid al-Adha, Ashura,
Tasu'a, Arbaeen, Mab'ath, etc.) shift every Jalali year and are NOT included
here — the national committee/admin should add those manually, per year,
from the Django admin panel (core.Holiday, leaving is_recurring off i.e.
setting an explicit jalali_year) once the official lunar calendar for that
year is published.

    python manage.py seed_holidays
"""

from django.core.management.base import BaseCommand

from core.models import Holiday

FIXED_HOLIDAYS = [
    # (month, day, title, is_day_off)
    (1, 1, "نوروز", True),
    (1, 2, "نوروز", True),
    (1, 3, "نوروز", True),
    (1, 4, "نوروز", True),
    (1, 12, "روز جمهوری اسلامی ایران", True),
    (1, 13, "روز طبیعت (سیزده‌بدر)", True),
    (3, 14, "رحلت امام خمینی (ره)", True),
    (3, 15, "قیام ۱۵ خرداد", True),
    (11, 22, "پیروزی انقلاب اسلامی", True),
    (12, 29, "روز ملی‌شدن صنعت نفت", True),
    # Occasions (not official days off) — examples, extend as needed:
    (2, 25, "روز بزرگداشت فردوسی", False),
    (7, 13, "روز دانش‌آموز", False),
]


class Command(BaseCommand):
    help = "Seeds fixed (Jalali-recurring) official Iranian holidays."

    def handle(self, *args, **options):
        created = 0
        for month, day, title, is_day_off in FIXED_HOLIDAYS:
            _, was_created = Holiday.objects.get_or_create(
                jalali_month=month, jalali_day=day, jalali_year=None,
                defaults={"title": title, "is_day_off": is_day_off},
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"{created} تعطیلی/مناسبت ثابت شمسی ثبت شد "
            f"(مناسبت‌های قمری را باید سالانه از پنل ادمین اضافه کنید)."
        ))
