from config import GUNICORN_PROCESSES, GUNICORN_THREADS, GUNICORN_BIND

workers = GUNICORN_PROCESSES
threads = GUNICORN_THREADS
bind = GUNICORN_BIND

# Optional settings
# timeout = GUNICORN_TIMEOUT

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}