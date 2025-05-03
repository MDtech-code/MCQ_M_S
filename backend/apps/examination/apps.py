# apps/examination/apps.py
from django.apps import AppConfig

class ExaminationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.examination'
    verbose_name = 'Examination'

    def ready(self):
        import apps.examination.signals  # Connect signals