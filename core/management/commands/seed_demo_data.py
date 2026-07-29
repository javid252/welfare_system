"""
Management command to populate the database with demo/sample data so the
system can be explored immediately after installation:

    python manage.py seed_demo_data

Creates:
  - 1 admin (username: admin / password: admin12345)
  - 1 provincial manager, 2 supervisors, 6 employees
  - a small service catalog
  - randomized activities for the current year
  - a couple of tasks
  - a WelfareYearlyBudget row for the current year
"""

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ServiceCatalog, Activity, TaskAssignment, WelfareYearlyBudget, Role

Employee = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with demo data for exploring the system."

    def handle(self, *args, **options):
        self.stdout.write("در حال ایجاد داده‌های نمونه...")

        admin = self._get_or_create_employee(
            "admin", "ADM-000", Role.ADMIN, "تهران", "تهران", position="مدیر سامانه",
            is_superuser=True, is_staff=True, password="admin12345",
        )

        manager = self._get_or_create_employee(
            "manager1", "MGR-001", Role.PROVINCIAL_MANAGER, "تهران", "تهران",
            position="مدیر استانی", password="manager12345",
        )

        supervisor1 = self._get_or_create_employee(
            "sup1", "SUP-001", Role.SUPERVISOR, "تهران", "تهران",
            position="سرپرست شهرستان تهران", supervisor=manager, password="sup12345",
        )
        supervisor2 = self._get_or_create_employee(
            "sup2", "SUP-002", Role.SUPERVISOR, "کرج", "البرز",
            position="سرپرست شهرستان کرج", supervisor=manager, password="sup12345",
        )

        employees = []
        first_names = ["علی", "رضا", "مریم", "زهرا", "حسین", "فاطمه", "محمد", "سارا"]
        for i in range(1, 7):
            supervisor = supervisor1 if i <= 3 else supervisor2
            emp = self._get_or_create_employee(
                f"emp{i}", f"EMP-{i:03d}", Role.EMPLOYEE,
                supervisor.region_code, supervisor.province_code,
                position="کارشناس رفاه اجتماعی", supervisor=supervisor,
                is_multitasking=(i % 3 == 0),
                first_name=random.choice(first_names),
                password="emp12345",
            )
            employees.append(emp)

        services_data = [
            ("INS-001", "بازدید و بازرسی کارگاه", 2.0),
            ("INS-002", "رسیدگی به شکایت کارگری", 3.5),
            ("WLF-001", "بررسی پرونده رفاهی خانوار", 1.5),
            ("WLF-002", "صدور دفترچه بیمه تکمیلی", 1.0),
            ("EDU-001", "برگزاری کارگاه آموزشی ایمنی", 5.0),
            ("ADM-001", "پیگیری مکاتبات اداری", 0.5),
        ]
        services = []
        for code, name, base_swu in services_data:
            svc, _ = ServiceCatalog.objects.get_or_create(
                service_code=code, defaults={"name": name, "base_swu": base_swu}
            )
            services.append(svc)

        year = timezone.localdate().year
        today = timezone.localdate()
        for emp in employees:
            for _ in range(random.randint(15, 30)):
                service = random.choice(services)
                day_offset = random.randint(0, 200)
                performed = today - timedelta(days=day_offset)
                if performed.year != year:
                    performed = today.replace(month=random.randint(1, today.month or 1), day=1)
                activity = Activity(
                    employee=emp,
                    service=service,
                    date_performed=performed,
                    quantity=random.randint(1, 5),
                    complexity_coefficient=random.choice([1.0, 1.0, 1.2, 1.5]),
                    is_complexity_approved=random.choice([True, False]),
                    status=Activity.Status.APPROVED,
                )
                activity.save()

        TaskAssignment.objects.get_or_create(
            assigned_by=supervisor1, assigned_to=employees[0], service=services[0],
            description="بازرسی فوری از کارگاه شماره ۱۲ منطقه ۴",
            defaults={"priority": "HIGH", "deadline": today + timedelta(days=5)},
        )
        TaskAssignment.objects.get_or_create(
            assigned_by=supervisor2, assigned_to=employees[4], service=services[2],
            description="بررسی پرونده رفاهی خانواده آقای محمدی",
            defaults={"priority": "MEDIUM", "deadline": today + timedelta(days=10)},
        )

        WelfareYearlyBudget.objects.get_or_create(
            year=year, defaults={"total_budget": 50_000_000_000, "reserved_fund": 2_000_000_000}
        )

        self.stdout.write(self.style.SUCCESS(
            "داده‌های نمونه با موفقیت ایجاد شد.\n"
            "ورود ادمین: admin / admin12345\n"
            "ورود سرپرست: sup1 / sup12345 یا sup2 / sup12345\n"
            "ورود کارمند: emp1 تا emp6 / emp12345"
        ))

    def _get_or_create_employee(self, username, employee_code, role, region_code,
                                  province_code, position="", supervisor=None,
                                  is_multitasking=False, first_name="", password="changeme123",
                                  is_superuser=False, is_staff=False):
        emp, created = Employee.objects.get_or_create(
            username=username,
            defaults={
                "employee_code": employee_code,
                "role": role,
                "region_code": region_code,
                "province_code": province_code,
                "position": position,
                "supervisor": supervisor,
                "is_multitasking": is_multitasking,
                "multitasking_coefficient": 1.1 if is_multitasking else 1.0,
                "region_coefficient": round(random.uniform(0.9, 1.3), 2),
                "first_name": first_name,
                "appointed_date": date(2020, 1, 1),
                "is_superuser": is_superuser,
                "is_staff": is_staff,
            },
        )
        if created:
            emp.set_password(password)
            emp.save()
        return emp
