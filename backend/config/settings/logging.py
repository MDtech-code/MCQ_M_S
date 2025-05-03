# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'content_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/content.log',
            'formatter': 'verbose',
        },
        'examination_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/examination.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',  # Use verbose format for console
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',  # Save logs to a file
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,  # Prevent logs from going to root logger
        },
        'apps.accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,  # Prevent logs from going to root logger
        },
        'apps.content': {
            'handlers': ['content_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.examination': {
            'handlers': ['examination_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # Less verbose for Django internals
            'propagate': False,
        },
        '': {  # Root logger as fallback
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Less noise for unconfigured loggers
        },
    },
}