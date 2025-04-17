

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# application = get_wsgi_application()


import os
from decouple import config
from django.core.wsgi import get_wsgi_application

environment = config('DJANGO_ENV', default='development')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{environment}")

application = get_wsgi_application()