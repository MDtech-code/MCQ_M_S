
import os
from decouple import config
from django.core.asgi import get_asgi_application
environment = config('DJANGO_ENV', default='development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f"config.settings.{environment}")

application = get_asgi_application()
