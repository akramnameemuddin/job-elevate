from pathlib import Path
import os
import environ

# Set up environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, 'backend', '.env'))

# SECURITY
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = [
    'job-elevate-m96p.onrender.com',
    'jobelevates.akramnaeemuddin.me',
    'localhost',
    '127.0.0.1',
]

# EMAIL CONFIGURATION
# Use different backends for local vs production
if DEBUG:
    # Local development - Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default='')
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default='')
    EMAIL_TIMEOUT = 10
else:
    # Production - Console backend (or SendGrid when configured)
    # Render blocks SMTP ports, so we need alternative email service
    SENDGRID_API_KEY = env("SENDGRID_API_KEY", default='')
    
    if SENDGRID_API_KEY:
        # If SendGrid is configured
        EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
        SENDGRID_SANDBOX_MODE_IN_DEBUG = False
        DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER", default='noreply@jobelevates.com')
    else:
        # Fallback: Console backend (emails printed to logs)
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        EMAIL_HOST_USER = env("EMAIL_HOST_USER", default='')
        
DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER", default='noreply@jobelevates.com')

# APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Job Elevate Apps
    'accounts',
    'jobs',
    'assessments',
    'learning',
    'community',
    'dashboard',
    'recruiter',
    'resume_builder',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.context_processors.user_initials',
                'dashboard.context_processors.dashboard_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# DATABASE
DATABASES = {
    'default': env.db(),  # Uses DATABASE_URL from .env
}

# STATIC/MEDIA
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AUTH
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
