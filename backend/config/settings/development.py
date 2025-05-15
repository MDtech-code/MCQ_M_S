from .base import *
from decouple import config
from .logging import LOGGING 
import socket
import os

DEBUG = True
print("SUCCESS: config.settings.development.py is NOW being loaded!") 
# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Dynamically determine INTERNAL_IPS for Docker and local environments
def get_internal_ips():
    try:
        # Get host IPs dynamically
        hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
        internal_ips = [ip[:ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]
        # Add Docker-specific IPs or custom IPs from environment
        custom_ips = config('DEBUG_TOOLBAR_IPS', default='', cast=lambda v: [x.strip() for x in v.split(',') if x])
        internal_ips.extend(custom_ips)
        return internal_ips
    except socket.gaierror:
        # Fallback for environments where hostname resolution fails
        return ['127.0.0.1', '172.17.0.1']  # Common Docker bridge gateway

INTERNAL_IPS = get_internal_ips()

# Development-specific database
DATABASES['default']['HOST'] = config('DB_HOST', default='localhost')
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}
print("DEBUG_TOOLBAR_CONFIG in developments.py:", DEBUG_TOOLBAR_CONFIG)
# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# Disable SSL in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



