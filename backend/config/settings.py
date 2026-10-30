"""Configurações do Comercializa para desenvolvimento local e deploy Render/Neon."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_csv(name):
    return [item.strip() for item in os.getenv(name, '').split(',') if item.strip()]


# Django local continua funcionando sem arquivo .env. Render define DEBUG=False.
DEBUG = env_bool('DEBUG', default=not env_bool('RENDER'))
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'chave-de-desenvolvimento-local-nao-utilizar-em-producao'
    else:
        raise ImproperlyConfigured('Defina SECRET_KEY nas variáveis de ambiente do Render.')

ALLOWED_HOSTS = list(dict.fromkeys([
    '127.0.0.1', 'localhost',
    *env_csv('ALLOWED_HOSTS'),
    *([os.environ['RENDER_EXTERNAL_HOSTNAME']] if os.getenv('RENDER_EXTERNAL_HOSTNAME') else []),
]))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

if not DEBUG:
    MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL and not DEBUG:
    raise ImproperlyConfigured('Configure DATABASE_URL (Neon). Não use SQLite efêmero no Render.')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=0,  # evita conexões ociosas mantidas em Neon Free
        conn_health_checks=True,
        ssl_require=not DEBUG,
    )}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    *env_csv('CORS_ALLOWED_ORIGINS'),
]
# A hospedagem do frontend fica em outro domínio (Cloudflare Pages).
# Não usar CORS_ALLOW_ALL_ORIGINS=True: explicitar o domínio do projeto.
CSRF_TRUSTED_ORIGINS = env_csv('CSRF_TRUSTED_ORIGINS')

# Acesso protegido em produção; compatibilidade com os testes e uso local legado.
REQUIRE_AUTH = not DEBUG
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'core.permissions.RequireAuthInProduction',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        *(['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
    ],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'login': '8/minute'},
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'
