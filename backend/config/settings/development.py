from .base import *
from decouple import config
from .logging import LOGGING 

DEBUG = True

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']
import socket

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]

# Development-specific database
DATABASES['default']['HOST'] = config('DB_HOST', default='localhost')

# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# Disable SSL in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



