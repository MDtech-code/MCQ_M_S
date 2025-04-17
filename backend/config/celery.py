from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')


app = Celery('config')


app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks in all installed apps.
app.autodiscover_tasks()

