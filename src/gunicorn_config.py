from config import GUNICORN_PROCESSES, GUNICORN_THREADS, GUNICORN_BIND

workers = GUNICORN_PROCESSES
threads = GUNICORN_THREADS
bind = GUNICORN_BIND

# Optional settings
# timeout = GUNICORN_TIMEOUT

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

# gunicorn's default logging config sets propagate=False on its own loggers,
# which stops their records from reaching the OTel LoggingHandler attached to
# the root logger by opentelemetry-instrument. Let them propagate instead.
accesslog = '-'
logconfig_dict = {
    'loggers': {
        'gunicorn.error': {'propagate': True},
        'gunicorn.access': {'propagate': True},
    }
}