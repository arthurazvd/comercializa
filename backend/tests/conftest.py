import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def pytest_configure():
    """Configurar Django antes de rodar os testes"""
    django.setup()
