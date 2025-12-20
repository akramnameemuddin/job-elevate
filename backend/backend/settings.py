from pathlib import Path
import os
import environ
from dotenv import load_dotenv

# --------------------------------------------------
# BASE SETUP
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, 'backend', '.env'))

# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "jobelevates.akramnaeemuddin.me",
]

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third-party
    "storages",

    # Job Elevate Apps
    "accounts",
    "jobs",
    "assessments",
    "learning",
    "community",
    "dashboard",
    "recruiter",
    "resume_builder",
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# URL / WSGI
# --------------------------------------------------
ROOT_URLCONF = "backend.urls"

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
                "backend.context_processors.user_initials",
                "dashboard.context_processors.dashboard_context",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# --------------------------------------------------
# DATABASE (PostgreSQL)
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# --------------------------------------------------
# AWS S3 CONFIGURATION
# --------------------------------------------------
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")

AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False

# --------------------------------------------------
# STATIC FILES (S3)
# --------------------------------------------------
STATIC_ROOT = BASE_DIR / "staticfiles"  # REQUIRED by Django
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
STATICFILES_STORAGE = "backend.storages.StaticStorage"

# --------------------------------------------------
# MEDIA FILES (S3)
# --------------------------------------------------
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
DEFAULT_FILE_STORAGE = "backend.storages.MediaStorage"

# --------------------------------------------------
# AUTH
# --------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------
# EMAIL (UNCHANGED LOGIC)
# --------------------------------------------------
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
else:
    SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
    if SENDGRID_API_KEY:
        EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
        EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="noreply@jobelevates.com")
        DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    else:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        DEFAULT_FROM_EMAIL = "noreply@jobelevates.com"
