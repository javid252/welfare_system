# سامانه مدیریت عملکرد و توزیع عادلانه رفاهی (SWU System)

سامانه‌ای برای وزارت تعاون، کار و رفاه اجتماعی جهت توزیع عادلانهٔ بودجهٔ رفاهی سالانه بر
اساس مدل **"واحد کار استاندارد" (Standard Work Unit / SWU)**، به‌جای رتبه‌بندی سنتی.

## فناوری‌های استفاده‌شده

| لایه | فناوری |
|---|---|
| بک‌اند | Django 4.2 (LTS) + Python 3.8+ |
| API | Django REST Framework (احراز هویت Session-based) |
| پایگاه داده | SQLite (پیش‌فرض توسعه) — به‌سادگی قابل تعویض با PostgreSQL |
| فرانت‌اند | Vue.js 2 (از CDN، بدون build step) درون قالب‌های Django + Bootstrap 5 RTL |
| نمودارها | Chart.js |

> **نکتهٔ سازگاری:** درخواست اولیهٔ پروژه «پایتون ۳.۲» را ذکر کرده بود که با جنگو ۴.۲
> سازگار نیست (جنگو ۴.۲ حداقل به پایتون ۳.۸ نیاز دارد). طبق تایید شما، پروژه برای
> **پایتون ۳.۸ به بالا** پیاده‌سازی شده است.

## فرمول محاسبه (منطق اصلی سامانه)

```
واحد کار پایه فعالیت = base_swu خدمت × تعداد (quantity)

واحد کار تعدیل‌شده فعالیت =
    واحد کار پایه
    × ضریب پیچیدگی تاییدشده (پیش‌فرض ۱٫۰، فقط با تایید سرپرست اعمال می‌شود)
    × ضریب منطقه کارمند
    × ضریب چندوظیفگی کارمند (در صورت فعال بودن پرچم is_multitasking)
    × ضریب کیفیت سالانه کارمند (بین ۰٫۸ تا ۱٫۲، برگرفته از میانگین امتیاز ممیزی‌ها)

سهم رفاهی کارمند =
    (مجموع واحد کار تعدیل‌شده سالانه کارمند ÷ مجموع واحد کار تعدیل‌شده کل کارمندان)
    × بودجهٔ قابل توزیع سالانه (بودجه کل − ذخیره موارد خاص)
```

تمام این منطق در یک‌جا و به‌صورت متمرکز در `core/services.py` پیاده‌سازی شده تا هم از
مدیریت (`manage.py distribute_welfare`) و هم از API (`/api/distribution/run/`) به یک
شکل و بدون تکرار کد فراخوانی شود.

## ساختار پوشه‌ها

```
welfare_system/
├── manage.py
├── requirements.txt
├── welfare_system/          # تنظیمات پروژه (settings, urls, wsgi/asgi)
├── core/                    # اپ اصلی: مدل‌ها، منطق کسب‌وکار، صفحات HTML
│   ├── models.py            # Employee, ServiceCatalog, Activity, TaskAssignment,
│   │                        # WelfareYearlyBudget, WelfareDistribution
│   ├── services.py          # منطق مشترک توزیع رفاهی و نمونه‌گیری ممیزی کیفیت
│   ├── permissions.py       # کمک‌تابع‌های RBAC (سلسله‌مراتب سازمانی)
│   ├── admin.py              # پنل ادمین جنگو برای همهٔ مدل‌ها
│   ├── views.py / urls.py    # صفحات HTML (لاگین، پوستهٔ داشبورد)
│   └── management/commands/
│       ├── distribute_welfare.py   # python manage.py distribute_welfare --year YYYY
│       └── seed_demo_data.py       # داده‌های نمونه برای تست سریع
├── api/                      # اپ REST API (Django REST Framework)
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py               # ViewSetها + Endpointهای داشبورد
│   └── urls.py
├── templates/                 # base.html, login.html, dashboard.html
└── static/
    ├── css/                    # style.css, rtl.css
    └── js/
        ├── api.js              # نمونهٔ axios با هدر CSRF
        ├── app.js              # Vue Router اصلی
        └── components/         # کامپوننت‌های Vue 2 (بدون build، مستقیماً از CDN)
            ├── EmployeeSummary.js   (خلاصه عملکرد شخصی + نمودار روند ماهانه)
            ├── ActivityForm.js      (ثبت فعالیت + پیش‌نمایش زنده SWU + تاریخچه)
            ├── TaskList.js          (وظایف من)
            ├── TeamPerformance.js   (عملکرد تیم، هیستوگرام، وضعیت وظایف)
            ├── Approvals.js         (تایید ضریب پیچیدگی)
            ├── AuditQueue.js        (صف ممیزی کیفیت)
            ├── AssignTask.js        (تخصیص وظیفه)
            ├── Heatmap.js           (نقشهٔ حرارتی استانی)
            ├── AdminServices.js     (CRUD کاتالوگ خدمات)
            ├── AdminEmployees.js    (CRUD کارمندان و ضرایب)
            └── AdminDistribution.js (اجرای توزیع رفاهی سالانه)
```

## نصب و راه‌اندازی

```bash
# ۱) ساخت و فعال‌سازی محیط مجازی
python3 -m venv venv
source venv/bin/activate      # ویندوز: venv\Scripts\activate

# ۲) نصب وابستگی‌ها
pip install -r requirements.txt

# ۳) اجرای migrationها
python manage.py migrate

# ۴) (اختیاری اما پیشنهادی) ساخت داده‌های نمونه برای تست سریع
python manage.py seed_demo_data
python manage.py seed_holidays

# ۵) اجرای سرور توسعه
python manage.py runserver
```

سپس به آدرس `http://127.0.0.1:8000/login/` مراجعه کنید.

### کاربران نمونه (پس از اجرای seed_demo_data)

| نقش | نام کاربری | رمز عبور |
|---|---|---|
| ادمین (کمیته ملی) | `admin` | `admin12345` |
| مدیر استانی | `manager1` | `manager12345` |
| سرپرست شهرستان | `sup1` / `sup2` | `sup12345` |
| کارمند | `emp1` تا `emp6` | `emp12345` |

پنل مدیریت جنگو نیز در آدرس `/admin/` با کاربر `admin` در دسترس است.

## اجرای توزیع رفاهی سالانه

از طریق خط فرمان:
```bash
python manage.py distribute_welfare --year 2026 --select-audit-sample
```

یا از طریق رابط کاربری (نقش ادمین → «اجرای توزیع رفاهی» در سایدبار)، که همان منطق را
از طریق endpoint زیر فراخوانی می‌کند:
```
POST /api/distribution/run/     body: {"year": 2026}
POST /api/distribution/select-audit-sample/     body: {"year": 2026}
```

> **پیش‌نیاز:** پیش از اجرای توزیع، باید یک رکورد `WelfareYearlyBudget` برای همان سال
> (بودجه کل و ذخیرهٔ موارد خاص) از طریق پنل ادمین یا صفحهٔ «اجرای توزیع رفاهی» ثبت شود.

## تقویم شمسی مستقل سامانه

سامانه از یک **موتور تبدیل تقویم میلادی↔شمسی کاملاً مستقل** استفاده می‌کند (بدون
وابستگی به `Intl` مرورگر یا کتابخانهٔ خارجی)، که هم در بک‌اند (`core/jalali_utils.py`)
و هم در فرانت‌اند (`static/js/jalali.js`) به‌صورت یکسان پیاده‌سازی شده تا همیشه با هم
هماهنگ باشند.

- **نمایش تاریخ‌ها:** همه‌جای رابط کاربری (تاریخچهٔ فعالیت، مهلت وظایف، نمودارها و...)
  با تاریخ و اعداد شمسی/فارسی نمایش داده می‌شود (`static/js/persian.js`).
- **انتخاب‌گر تاریخ شمسی:** کامپوننت `<jalali-date-picker>` یک تقویم کامل شمسی با
  ناوبری ماه/سال است که در فرم ثبت فعالیت و تخصیص وظیفه استفاده شده. مقدار انتخاب‌شده
  را به‌صورت تاریخ میلادی ISO (`YYYY-MM-DD`) برمی‌گرداند تا با بک‌اند سازگار بماند.
- **تعطیلات و مناسبت‌ها:** مدل `core.Holiday` امکان تعریف دو نوع مناسبت را می‌دهد:
  - **تکرارشونده (`jalali_year` خالی):** مناسبت‌های ثابت شمسی مثل نوروز که هرساله در
    همان ماه/روز شمسی تکرار می‌شوند.
  - **غیرتکرارشونده (`jalali_year` مشخص):** مناسبت‌های قمری (مثل عید فطر، عاشورا) که
    هرسال جابه‌جا می‌شوند و باید سالانه و دستی وارد شوند.

  برای افزودن/ویرایش تعطیلات، از پنل ادمین جنگو (`/admin/core/holiday/`) استفاده کنید.
  دستور `python manage.py seed_holidays` مجموعه‌ای از تعطیلات رسمی ثابت (نوروز، ۲۲
  بهمن و...) را از پیش ثبت می‌کند. تعطیلات در تقویم انتخاب‌گر با رنگ قرمز (تعطیل رسمی)
  یا نارنجی (فقط مناسبت) مشخص می‌شوند و با نگه‌داشتن نشانگر روی روز، عنوان دیده می‌شود.

## دیپلوی روی Render

پروژه برای دیپلوی مستقیم روی [Render](https://render.com) آماده است — هم از طریق
GitHub و هم با آپلود مستقیم به Render. برای پایداری داده‌ها (پلن رایگان Render فضای
دیسک سرویس وب را در هر دیپلوی پاک می‌کند)، از **PostgreSQL رایگان Render** استفاده
می‌شود؛ کد به‌طور خودکار بین SQLite (لوکال) و PostgreSQL (روی Render) سوییچ می‌کند —
هیچ تغییر دستی لازم نیست.

### روش ۱: دیپلوی یک‌کلیکی با Blueprint (پیشنهادی)

1. این پروژه را در یک ریپازیتوری روی **GitHub** قرار دهید (خالی از `venv/`, `db.sqlite3`
   و `staticfiles/` — که در `.gitignore` از قبل مستثنا شده‌اند).
2. در داشبورد Render: **New → Blueprint** را بزنید و ریپازیتوری خود را انتخاب کنید.
3. Render فایل `render.yaml` را می‌خواند و به‌صورت خودکار می‌سازد:
   - یک **PostgreSQL** رایگان (`welfare-system-db`)
   - یک **Web Service** پایتون که به همان دیتابیس وصل است (`DATABASE_URL` خودکار تزریق
     می‌شود)، به‌همراه یک `DJANGO_SECRET_KEY` تصادفی امن
4. روی **Apply** کلیک کنید. Render به‌صورت خودکار `build.sh` (نصب وابستگی‌ها،
   `collectstatic`، `migrate`) و سپس `gunicorn` را اجرا می‌کند.
5. چون `SEED_DEMO_DATA=true` در `render.yaml` تنظیم شده، بعد از اولین دیپلوی سامانه با
   داده‌های نمونه (همان کاربران `admin`, `sup1`, `emp1` و...) از پیش پر شده و آماده
   بازدید است — آدرس نهایی چیزی شبیه `https://welfare-system.onrender.com/login/`
   خواهد بود.

### روش ۲: ساخت دستی از داشبورد Render (بدون Blueprint)

اگر ترجیح می‌دهید سرویس‌ها را تک‌به‌تک بسازید:

1. **New → PostgreSQL** → یک دیتابیس رایگان بسازید و مقدار **Internal Database URL**
   را کپی کنید.
2. **New → Web Service** → ریپازیتوری گیت‌هاب (یا آپلود مستقیم پوشه) را انتخاب کنید:
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn welfare_system.wsgi:application`
   - **Environment Variables:**
     | کلید | مقدار |
     |---|---|
     | `DJANGO_SECRET_KEY` | یک رشتهٔ تصادفی طولانی |
     | `DJANGO_DEBUG` | `False` |
     | `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
     | `DATABASE_URL` | همان Internal Database URL مرحلهٔ قبل |
     | `SEED_DEMO_DATA` | `true` (برای دادهٔ نمونه) یا `false` |
3. **Create Web Service** را بزنید.

### بعد از دیپلوی

- برای اجرای دستورات مدیریتی (مثل `distribute_welfare` یا ساخت یک ادمین دلخواه)، از
  تب **Shell** همان سرویس در داشبورد Render استفاده کنید:
  ```bash
  python manage.py distribute_welfare --year 1405
  ```
- اگر `SEED_DEMO_DATA=false` بگذارید و بخواهید یک ادمین دلخواه بسازید، ساده‌ترین راه
  از همان Shell است:
  ```bash
  python manage.py shell -c "
  from django.contrib.auth import get_user_model
  U = get_user_model()
  U.objects.create_superuser(username='admin', password='YOUR_PASSWORD', employee_code='ADM-000', region_code='تهران')
  "
  ```
  (چون `Employee` فیلدهای اجباری اضافه‌ای دارد، دستور استاندارد
  `createsuperuser --noinput` به‌تنهایی کافی نیست.)

## نکات توسعهٔ آینده

- **وضعیت فعلی فعالیت‌ها:** فعالیت‌های ثبت‌شده توسط کارمند به‌صورت پیش‌فرض با وضعیت
  `APPROVED` ذخیره می‌شوند تا واحد کار بلافاصله در نمودارها منعکس شود؛ اگر فرایند
  تایید مدیریتی جداگانه‌ای برای خودِ فعالیت (نه فقط ضریب پیچیدگی) نیاز است، به‌سادگی
  می‌توان `perform_create` در `ActivityViewSet` را برای شروع با وضعیت `PENDING`
  تغییر داد.
- **سوئیچ به PostgreSQL:** بلوک کامنت‌شده در `welfare_system/settings.py` را از
  حالت کامنت خارج کنید و متغیرهای محیطی `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
  `DB_HOST`, `DB_PORT` را تنظیم نمایید.
- **افزودن JWT:** در صورت نیاز به اپلیکیشن موبایل/SPA جداگانه، کتابخانهٔ
  `djangorestframework-simplejwt` قابل افزودن به `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`
  است، بدون نیاز به تغییر در منطق ViewSetها.
- **ماژول‌های آتی:** Replay (بازپخش تاریخچهٔ فعالیت) و Marketplace طبق نیاز پروژه، هنوز
  پیاده‌سازی نشده‌اند و می‌توانند به‌صورت اپ‌های جنگوی جداگانه اضافه شوند.
- **مقیاس‌پذیری:** برای حجم داده و کاربران بالا، اجرای `distribute_welfare` را به یک
  Celery task منتقل کنید تا محاسبات سنگین، درخواست HTTP را مسدود نکند.

## تست سریع API با curl

```bash
# لاگین و ذخیرهٔ کوکی سشن
curl -c cookies.txt -b cookies.txt http://127.0.0.1:8000/login/ -o /dev/null
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/login/ \
     -d "username=admin&password=admin12345&csrfmiddlewaretoken=$CSRF" \
     -H "Referer: http://127.0.0.1:8000/login/"

# فراخوانی API
curl -b cookies.txt http://127.0.0.1:8000/api/dashboard/employee-summary/
```
#   w e l f a r e _ s y s t e m  
 