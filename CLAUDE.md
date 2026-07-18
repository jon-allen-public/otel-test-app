# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A minimal Flask web app that checks whether a number is prime. The check runs as an asynchronous Celery task (Redis as broker/backend) rather than inline in the request handler — this app exists to exercise that async request/worker pattern (likely as an OpenTelemetry instrumentation test target, per the repo name), not for the prime-checking logic itself.

## Running locally

No local dev-server tooling (venv setup, Makefile, test runner) is defined in the repo — the only supported way to run the stack is Docker Compose:

```bash
docker compose up --build
```

This starts three services: `flask-app` (port 8080), `celery-worker`, and `redis` (port 6379). The Flask app depends on `redis` and `celery-worker` for the prime-check task to ever complete — `POST /` blocks on `task.get(timeout=30)`, so if the worker or Redis isn't running, requests will hang for 30s and then fail.

There are no automated tests, linter, or CI checks beyond building/pushing Docker images (`.github/workflows/build.yaml`, triggered on push to `main`).

## Architecture

- `src/main.py` — the entire Flask app: routes, Flask config loading, and the Celery app/task definition all live in one file.
  - `GET/POST /` — form-based UI; POST submits a number, synchronously waits on the Celery result, and re-renders `index.html`.
  - `GET /result/<task_id>` — polls a task's state as JSON (defined but not used by the current template/JS — no polling JS exists in `index.html`).
  - `check_prime` — the Celery task; trial division, no external calls.
- `src/config.py` — flat module-level config (not a class), read via `app.config.from_object('config')`. Also holds the Gunicorn settings (`GUNICORN_*`), which `gunicorn_config.py` imports from directly.
- `src/celery_worker.py` — alternate entrypoint (`from main import celery; celery.start()`); the Docker image instead runs `celery -A src.main.celery worker` directly, so this file's `__main__` path isn't exercised by the current Docker setup.
- `src/gunicorn_config.py` — used via `gunicorn -c src/gunicorn_config.py src.main:app` (see `Dockerfile`).

**Import path quirk**: `src/main.py` does `app.config.from_object('config')` (not `'src.config'`), and `celery_worker.py` does `from main import celery` (not `from src.main`). Both only resolve because `PYTHONPATH=/app/src` is set in both Dockerfiles, making `src/` itself the import root rather than the repo root. Anything run outside Docker needs the same `PYTHONPATH` set, or these imports will fail.

**Two separate images, one codebase**: `Dockerfile` (Flask/Gunicorn) and `Dockerfile.celery` (Celery worker) both `COPY . /app/` — the entire repo — and differ only in the run command and in the worker image dropping to a non-root user. There's no separate requirements split between web and worker.

- `src/templates/index.html` — single Jinja2 template, renders the form and result inline (`is_prime`/`number`/`error` passed from the view).
- `src/static/css/styles.css` — styling for that template.
