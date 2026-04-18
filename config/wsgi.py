"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import environ
from django.core.wsgi import get_wsgi_application
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

environ.Env.read_env(BASE_DIR / ".env")

env("DJANGO_SETTINGS_MODULE", default="config.settings.prod")

application = get_wsgi_application()
