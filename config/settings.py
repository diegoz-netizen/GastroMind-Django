"""
Configuración de GastroMind-Django (backend analítico).

Toda credencial se lee del entorno o del archivo .env, que no se sube al repo
(igual que application-local.properties en Spring). Ver .env.example.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env(nombre, defecto=None):
    valor = os.environ.get(nombre, defecto)
    if valor is None:
        raise ImproperlyConfigured(f'Falta la variable de entorno {nombre} (ver .env.example)')
    return valor


SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [h.strip() for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'catalogo',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Misma BD PostgreSQL que Spring Boot. Las tablas de negocio las define docs/script_database.sql
# del repo principal y aquí se mapean con managed = False (nunca se migran desde Django).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', 'gastromind_db'),
        'USER': env('DB_USER', 'postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', 'localhost'),
        'PORT': env('DB_PORT', '5432'),
    }
}


# Login único: el JWT lo emite Spring Boot (POST /api/auth/login). Django lo valida con la MISMA clave
# que gastromind.jwt.secret de Spring.
JWT_SECRET = env('JWT_SECRET')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['catalogo.authentication.JWTSpringAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    # HL-014: errores como {error, mensaje, campos?}, igual que Spring
    'EXCEPTION_HANDLER': 'config.errores.manejador_errores',
}

CORS_ALLOWED_ORIGINS = [o.strip() for o in env(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174').split(',') if o.strip()]


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'es-pe'

# Hora local para mostrar (Perú). Con USE_TZ, Django lee y escribe la BD en UTC, igual que el backend
# de Spring desde el PR #8 (regla del equipo, 12/10: se guarda en UTC y se muestra en hora de Perú).
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
