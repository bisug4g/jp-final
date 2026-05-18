"""
Django settings for jaytipargal project.
Jayti Pargal - Personal Life Companion Website
"""
from pathlib import Path
import os
from urllib.parse import urlparse
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / 'backend' / '.env')
load_dotenv()

_INSECURE_SECRET = 'dev-only-insecure-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', _INSECURE_SECRET if DEBUG else '')

# Fail fast if running production without a proper SECRET_KEY.
# collectstatic during docker build is allowed to use a build-time placeholder
# (DJANGO_COLLECTSTATIC=1) so images can be built without leaking real secrets.
if not DEBUG and (not SECRET_KEY or SECRET_KEY == _INSECURE_SECRET):
    if os.environ.get('DJANGO_COLLECTSTATIC') == '1':
        SECRET_KEY = 'build-time-placeholder-not-used-at-runtime'
    else:
        raise ImproperlyConfigured(
            'SECRET_KEY environment variable is required when DEBUG=False.'
        )

import os as _os


def _split_env_list(value):
    if not value:
        return []
    normalized = value.replace(';', ',')
    return [item.strip() for item in normalized.split(',') if item.strip()]


def _normalize_host(value):
    if not value:
        return ''
    candidate = value.strip()
    if not candidate:
        return ''
    if candidate.startswith('.'):
        return candidate
    if '://' not in candidate:
        candidate = f'https://{candidate}'
    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    if not host:
        return ''
    return host.split('@')[-1].split(':')[0].strip().strip('/')


def _append_unique(items, value):
    if value and value not in items:
        items.append(value)


_default_allowed_hosts = [
    'localhost',
    '127.0.0.1',
    '[::1]',
    'jaytibirthday.in',
    'www.jaytibirthday.in',
    '.railway.app',
    # Google Cloud Run — auto-generated service URLs + custom mapped domain
    '.run.app',
    # Firebase Hosting preview / live channels
    '.web.app',
    '.firebaseapp.com',
]

# Cloud Run injects K_SERVICE; use it to detect the platform automatically.
if _os.environ.get('K_SERVICE'):
    _default_allowed_hosts.extend([
        '.run.app',
        '.web.app',
        '.firebaseapp.com',
    ])

# Opt-in additions for the Emergent hosting platform.
if _os.environ.get('EMERGENT_PLATFORM', '').lower() in ('1', 'true', 'yes'):
    _default_allowed_hosts.extend([
        '.emergentagent.com',
        '.emergentcf.cloud',
        '.emergent.host',
    ])
_allowed_hosts = []
for host in _default_allowed_hosts:
    _append_unique(_allowed_hosts, host)
for env_name in ('ALLOWED_HOSTS', 'DEPLOYMENT_URL', 'HOST', 'RAILWAY_PUBLIC_DOMAIN'):
    for raw_value in _split_env_list(_os.environ.get(env_name, '')):
        _append_unique(_allowed_hosts, _normalize_host(raw_value))
ALLOWED_HOSTS = _allowed_hosts

# CSRF Trusted Origins — computed once at startup from env + known defaults.
# (Do NOT mutate this list at request time; that's racy and defeats Django's origin check.)
_csrf_origins = [
    'https://jaytibirthday.in',
    'https://www.jaytibirthday.in',
    'https://*.railway.app',
    # Cloud Run service URLs and Firebase Hosting
    'https://*.run.app',
    'https://*.web.app',
    'https://*.firebaseapp.com',
    'http://localhost:3000',
    'http://localhost:8001',
    'http://localhost:8080',
]
if _os.environ.get('EMERGENT_PLATFORM', '').lower() in ('1', 'true', 'yes'):
    _csrf_origins.extend([
        'https://*.emergentagent.com',
        'https://*.emergentcf.cloud',
        'https://*.emergent.host',
        'https://*.stage-preview.emergentagent.com',
    ])


def _csrf_candidates(raw):
    """Turn a host/URL into acceptable CSRF origin entries."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith('http://') or raw.startswith('https://'):
        return [raw]
    return [f'https://{raw}']


for env_name in ('CSRF_TRUSTED_ORIGIN', 'CSRF_TRUSTED_ORIGINS', 'DEPLOYMENT_URL',
                 'RAILWAY_PUBLIC_DOMAIN', 'HOST'):
    for raw_value in _split_env_list(_os.environ.get(env_name, '')):
        for candidate in _csrf_candidates(raw_value):
            if candidate not in _csrf_origins:
                _csrf_origins.append(candidate)

CSRF_TRUSTED_ORIGINS = _csrf_origins

# CSRF Cookie settings for production
CSRF_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for CSRF
CSRF_COOKIE_SAMESITE = 'Lax'  # Allows form submissions from same site

# Session settings
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'

# Trust X-Forwarded headers from reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Custom apps
    'core',
    'notes',
    'diary',
    'goals',
    'astro',
    'ai_chat',
    'tangred',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files on cloud
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.UserSessionTrackingMiddleware',  # Track IP and device info
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jaytipargal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_profile',
                'core.context_processors.birthday_check',
                'core.context_processors.daily_inspiration',
                'core.context_processors.firebase_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'jaytipargal.wsgi.application'

# Database Configuration
# Uses PostgreSQL in production (via DATABASE_URL), SQLite for local development
# Railway deployment: DATABASE_URL is auto-injected when PostgreSQL is provisioned

def get_database_config():
    """
    Get database configuration with proper SSL handling for Railway/Supabase.
    Returns a dict compatible with Django DATABASES setting.
    CRITICAL: Connection settings optimized to prevent blocking during health checks.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production: Use PostgreSQL with Supabase/Railway
        # Parse the URL and handle SSL properly
        config = dj_database_url.parse(
            database_url,
            conn_max_age=600,
        )
        
        # Add SSL mode and connection timeouts for Supabase PostgreSQL
        if 'OPTIONS' not in config:
            config['OPTIONS'] = {}
        
        # Handle sslmode properly for psycopg2
        config['OPTIONS']['sslmode'] = 'require'
        
        # Connection timeout settings to prevent blocking during startup
        config['OPTIONS']['connect_timeout'] = 10  # 10 seconds max for connection
        
        # Add CONN_HEALTH_CHECKS to prevent stale connections
        config['CONN_HEALTH_CHECKS'] = True
        
        return config
    else:
        # Emergent/Development: Use SQLite (file-based, no external DB needed)
        # Use /tmp for writable storage in containerized environments
        default_db_path = '/tmp/jayti_db.sqlite3' if os.path.exists('/tmp') else str(BASE_DIR / 'db.sqlite3')
        db_path = os.environ.get('SQLITE_PATH', default_db_path)
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }

DATABASES = {
    'default': get_database_config()
}

# Cache configuration for performance
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'jayti-cache',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('TIME_ZONE', 'Asia/Kolkata')  # Delhi timezone for Jayti
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for serving static files in production. The manifest variant
# requires ``collectstatic`` to have run; in DEBUG/test mode we fall back to the
# plain compressed storage so developers and the pytest-django ``live_server``
# fixture don't need a prior collectstatic step.
#
# Using the STORAGES dict API (Django 4.2+) so we stay compatible with Django 5.x
# which removes the deprecated STATICFILES_STORAGE setting.
_whitenoise_backend = (
    'whitenoise.storage.CompressedStaticFilesStorage'
    if DEBUG
    else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': _whitenoise_backend,
    },
}

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout redirects
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Jayti's birthday configuration
JAYTI_BIRTH_DATE = int(os.environ.get('BIRTH_DATE_DAY', 6))
JAYTI_BIRTH_MONTH = int(os.environ.get('BIRTH_DATE_MONTH', 2))  # February

# Astrology settings
JAYTI_BIRTH_DETAILS = {
    'year': 1997,
    'month': 2,
    'day': 6,
    'hour': 22,
    'minute': 30,
    'latitude': 28.61,
    'longitude': 77.21,
    'location': 'Delhi, India',
    'timezone': 'Asia/Kolkata'
}

# Emergent AI API Configuration (OpenAI-compatible, primary)
EMERGENT_API_KEY = os.environ.get('EMERGENT_API_KEY', '')
EMERGENT_BASE_URL = os.environ.get('EMERGENT_BASE_URL', 'https://api.emergent.sh/v1')
EMERGENT_MODEL = os.environ.get('EMERGENT_MODEL', 'claude-opus-4-6')

# GitHub Models configuration (OpenAI-compatible)
GITHUB_MODELS_TOKEN = os.environ.get('GITHUB_MODELS_TOKEN', '')
GITHUB_MODELS_BASE_URL = os.environ.get('GITHUB_MODELS_BASE_URL', 'https://models.github.ai/inference')
GITHUB_MODELS_MODEL = os.environ.get('GITHUB_MODELS_MODEL', 'openai/gpt-4.1-mini')

# Google Gemini API Configuration (fallback)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro')

# Vertex AI / Firebase-backed Gemini configuration
VERTEX_AI_LOCATION = os.environ.get('VERTEX_AI_LOCATION', 'us-central1')
VERTEX_GEMINI_MODEL = os.environ.get('VERTEX_GEMINI_MODEL', 'gemini-2.0-flash')

# Google Stitch MCP configuration for Tan Studio
STITCH_API_KEY = os.environ.get('STITCH_API_KEY', '')
STITCH_MCP_URL = os.environ.get('STITCH_MCP_URL', 'https://stitch.googleapis.com/mcp')
STITCH_TIMEOUT_SEC = int(os.environ.get('STITCH_TIMEOUT_SEC', '240'))

# OpenRouter prompt optimization for Tan Studio
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free')
OPENROUTER_TIMEOUT_SEC = int(os.environ.get('OPENROUTER_TIMEOUT_SEC', '90'))

# Tangred private media storage
TANGRED_PRIVATE_MEDIA_BACKEND = os.environ.get('TANGRED_PRIVATE_MEDIA_BACKEND', 'auto').lower()

# Logging configuration
# On Railway / container environments the filesystem is ephemeral; default to console
# logging and only enable a file handler when explicitly requested (dev or mounted volume).
_LOG_TO_FILE = os.environ.get('LOG_TO_FILE', '1' if DEBUG else '0').lower() in ('1', 'true', 'yes')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'goals': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

if _LOG_TO_FILE:
    LOGS_DIR = BASE_DIR / 'logs'
    try:
        LOGS_DIR.mkdir(exist_ok=True)
    except OSError:
        LOGS_DIR = Path('/tmp') / 'jaytipargal' / 'logs'
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': str(LOGS_DIR / 'django.log'),
        'formatter': 'verbose',
    }
    for _logger in LOGGING['loggers'].values():
        _logger['handlers'] = list(_logger['handlers']) + ['file']

# Railway-specific settings
RAILWAY_DEBUG = os.environ.get('RAILWAY_DEBUG', 'false').lower() == 'true'
if RAILWAY_DEBUG:
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    LOGGING['handlers']['console']['level'] = 'DEBUG'

# VAPID keys for web push notifications
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_ADMIN_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'admin@jaytibirthday.in')

# ── Firebase (project: jpfinal-c9340) ────────────────────────────────────────
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', 'jpfinal-c9340.firebaseapp.com')
FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'jpfinal-c9340')
FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'jpfinal-c9340.firebasestorage.app')
FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '588713240952')
FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '1:588713240952:web:a6bfb6013e3eea6efe008d')
FIREBASE_MEASUREMENT_ID = os.environ.get('FIREBASE_MEASUREMENT_ID', '')
FIREBASE_ENABLED = all([
    FIREBASE_API_KEY,
    FIREBASE_PROJECT_ID,
    FIREBASE_APP_ID,
])

# Firebase Admin configuration for Railway-hosted backend integrations
FIREBASE_PRIVATE_KEY_ID = os.environ.get('FIREBASE_PRIVATE_KEY_ID', '')
FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL', '')
FIREBASE_CLIENT_ID = os.environ.get('FIREBASE_CLIENT_ID', '')
FIREBASE_AUTH_URI = os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
FIREBASE_TOKEN_URI = os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token')
FIREBASE_AUTH_PROVIDER_CERT_URL = os.environ.get(
    'FIREBASE_AUTH_PROVIDER_CERT_URL',
    'https://www.googleapis.com/oauth2/v1/certs',
)
FIREBASE_CLIENT_CERT_URL = os.environ.get('FIREBASE_CLIENT_CERT_URL', '')

# SSL/HTTPS settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r'^health/?$']  # Allow plain HTTP health checks
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ─── Google Cloud Run ─────────────────────────────────────────────────────────
# Cloud Run injects K_SERVICE into every container at runtime.
# When present we know we're running on Cloud Run and can apply platform-specific
# settings (e.g. trust the X-Forwarded-Proto header injected by the Firebase
# Hosting / Cloud Run load balancer).
_CLOUD_RUN = bool(_os.environ.get('K_SERVICE'))

if _CLOUD_RUN:
    # Cloud Run always terminates TLS at the load balancer and forwards plain
    # HTTP to the container. SECURE_SSL_REDIRECT must be off (we already got
    # HTTPS) and we must trust the proxy header so Django sees the request as
    # secure (cookies, CSRF, session all need this).
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cloud Run containers are ephemeral — never log to a file.
    LOG_TO_FILE_OVERRIDE = False
    _LOG_TO_FILE = False

    # Gunicorn on Cloud Run uses PORT=8080 by default; no changes needed here
    # but documenting for clarity.  PORT is consumed by entrypoint.sh.

