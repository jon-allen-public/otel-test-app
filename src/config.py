# Flask configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# Celery hijacks (replaces) the root logger's handlers on worker startup by
# default, which would drop the OTel LoggingHandler opentelemetry-instrument
# attaches there.
CELERYD_HIJACK_ROOT_LOGGER = False

# Gunicorn configuration
GUNICORN_PROCESSES = 1
GUNICORN_THREADS = 2
GUNICORN_BIND = '0.0.0.0:8080'
GUNICORN_TIMEOUT = 120