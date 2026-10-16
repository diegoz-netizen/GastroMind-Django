"""
Settings para los tests: SQLite en memoria, sin depender de PostgreSQL ni de un .env.
Uso: python manage.py test --settings=config.settings_test
"""

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'solo-para-tests')
os.environ.setdefault('DB_PASSWORD', 'no-se-usa-en-tests')
os.environ.setdefault('JWT_SECRET', 'GastroMindTestSecretKeyForJWTTokenGeneration2026')
# Los tests no dependen del .env de cada uno: mismo origen que el valor por defecto
os.environ.setdefault('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')

from .settings import *  # noqa: E402,F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
TEST_RUNNER = 'config.test_runner.UnmanagedModelsTestRunner'
# Sin migraciones para catalogo en los tests: las tablas se crean desde los modelos (ya en managed = True)
MIGRATION_MODULES = {'catalogo': None}
