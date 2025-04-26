# Flask configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Gunicorn configuration
GUNICORN_PROCESSES = 1
GUNICORN_THREADS = 2
GUNICORN_BIND = '0.0.0.0:8080'
GUNICORN_TIMEOUT = 120