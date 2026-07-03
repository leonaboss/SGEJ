"""
SGEJ - Sistema de Gestor de Expedientes Jurídicos
Configuración principal de Django.
"""
import os
from pathlib import Path
import environ

# ============================================
# Paths & Environment
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    ENTORNO=(str, 'localhost'),
    FRASE_SEGURIDAD_MAESTRA=(str, 'ConsultoriaJuridicaUPTAG2026'),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
ENTORNO = env('ENTORNO')
FERNET_MASTER_KEY = env('FERNET_MASTER_KEY')
FRASE_SEGURIDAD_MAESTRA = env('FRASE_SEGURIDAD_MAESTRA', default='ConsultoriaJuridicaUPTAG2026')

# ============================================
# Installed Apps (SoC: cada app = un dominio)
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'django_filters',
    'django_otp',
    'django_otp.plugins.otp_totp',
    # Domain Apps
    'apps.usuarios',
    'apps.expedientes',
    'apps.documentos',
    'apps.biblioteca',
    'apps.infraestructura',
]

# ============================================
# Middleware
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.infraestructura.middleware.RateLimitMiddleware',
    'apps.infraestructura.middleware.SessionControlMiddleware',
    'apps.infraestructura.middleware.AuditoriaInmutableMiddleware',
]

ROOT_URLCONF = 'sgej_config.urls'

# ============================================
# Templates
# ============================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.infraestructura.context_processors.notificaciones_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'sgej_config.wsgi.application'

# ============================================
# Database (MySQL via .env)
# ============================================
import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME', default='sgej_juridico'),
            'USER': env('DB_USER', default='root'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# ============================================
# Auth
# ============================================
AUTH_USER_MODEL = 'usuarios.Usuario'

# Argon2 como hasher primario de contraseñas (OWASP compliant)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 16}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# Internationalization
# ============================================
LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# ============================================
# Static & Media
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================
# Security (OWASP compliance)
# ============================================
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# ============================================
# REST Framework
# ============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ============================================
# Defaults
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout redirects
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Cache
# - default: LocMemCache para rate limiting (rápido, por proceso)
# - session_control: LocMemCache para desarrollo; en producción multi-worker
#   cambiar a DatabaseCache (ejecutar: python manage.py createcachetable sgej_cache_table)
#   o Redis: pip install redis y usar django.core.cache.backends.redis.RedisCache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sgej-cache',
    },
    'session_control': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sgej-session-control',
    },
}

# Email config
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'sgej@uptag.edu.ve'
