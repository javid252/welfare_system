"""
Django settings for the Performance Management and Fair Welfare Distribution System
(سامانه مدیریت عملکرد و توزیع عادلانه رفاهی).

Target environment: Python 3.8+, Django 4.2 LTS.
Works unchanged in two environments:
  * Local development -> SQLite, DEBUG=True by default.
  * Render (or any 12-factor host) -> reads DATABASE_URL (PostgreSQL),
    DJANGO_DEBUG=False, DJANGO_SECRET_KEY, etc. from environment variables.
"""

from pathlib import Path
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------
# SECURITY
# -----------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-THIS-KEY-BEFORE-DEPLOYMENT-xyz123",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Render provides this automatically for every web service, e.g.
# "welfare-system.onrender.com" — used below to build ALLOWED_HOSTS and
# CSRF_TRUSTED_ORIGINS without hardcoding a domain name.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Render's load balancer terminates TLS and forwards plain HTTP internally;
# this tells Django to trust the X-Forwarded-Proto header so request.is_secure()
# (and therefore secure cookies, CSRF, etc.) work correctly behind that proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -----------------------------------------------------------------------
# APPLICATIONS
# -----------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # for Persian-friendly number formatting in templates

    # Third-party
    "rest_framework",
    "django_filters",

    # Local apps
    "core",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files directly; no separate web server needed on Render
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # enables RTL/Persian locale switching
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "welfare_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "welfare_system.wsgi.application"

# -----------------------------------------------------------------------
# DATABASE
# -----------------------------------------------------------------------
# Local development (no DATABASE_URL set): SQLite, as before.
# On Render (or any host providing DATABASE_URL, e.g. its managed
# PostgreSQL add-on): automatically parsed and used instead — no code
# change needed when moving from a laptop to Render.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# -----------------------------------------------------------------------
# AUTH
# -----------------------------------------------------------------------
AUTH_USER_MODEL = "core.Employee"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:login"

# -----------------------------------------------------------------------
# INTERNATIONALIZATION — Persian / RTL
# -----------------------------------------------------------------------
LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fa", "فارسی"),
]

# -----------------------------------------------------------------------
# STATIC & MEDIA FILES
# -----------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Whitenoise: compresses + fingerprints static files at collectstatic time so
# Render (which has no separate nginx/static host) can serve them directly
# from the Django process efficiently and with far-future cache headers.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------
# DJANGO REST FRAMEWORK — Session-based authentication
# -----------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M",
}

# CSRF: the SPA-lite frontend (Vue components in Django templates) reads the
# CSRF token from the cookie and sends it back via the X-CSRFToken header.
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# In production (Render), cookies must only ever be sent over HTTPS.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# -----------------------------------------------------------------------
# WELFARE SYSTEM — business-rule constants
# (kept here so the national committee can tune them without touching code)
# -----------------------------------------------------------------------
QUALITY_AUDIT_SAMPLE_RATE = 0.05        # 5% of activities are audited
QUALITY_COEFFICIENT_MIN = 0.8
QUALITY_COEFFICIENT_MAX = 1.2
WELFARE_RESERVED_FUND_MAX_RATIO = 0.05  # max 5% reserved for special cases
