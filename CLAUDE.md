# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A minimal Flask web app that checks whether a number is prime. The check runs as an asynchronous Celery task (Redis as broker/backend) rather than inline in the request handler — this app exists to exercise that async request/worker pattern as an OpenTelemetry instrumentation test target (per the repo name), not for the prime-checking logic itself. Both the Flask app and the Celery worker are instrumented and emit metrics, traces, and logs (see Observability below).

## Running locally

No local dev-server tooling (venv setup, Makefile, test runner) is defined in the repo — the only supported way to run the stack is Docker Compose:

```bash
docker compose up --build
```

This starts three services: `flask-app` (port 8080), `celery-worker`, and `redis` (port 6379). The Flask app depends on `redis` and `celery-worker` for the prime-check task to ever complete — `POST /` blocks on `task.get(timeout=30)`, so if the worker or Redis isn't running, requests will hang for 30s and then fail.

There are no automated tests or linter. `.github/workflows/build.yaml` builds and pushes both images: a push to `main` refreshes the `latest` tag, and pushing a `vX.Y.Z` git tag additionally publishes a semver-tagged release (`X.Y.Z`) — that's what the Helm chart below pins to.

## Observability (OpenTelemetry metrics, traces, logs)

Both images install `opentelemetry-distro` + `opentelemetry-exporter-otlp`, then run `opentelemetry-bootstrap -a install` at build time — this detects the libraries actually present (Flask, Celery, Redis) and installs matching auto-instrumentation packages, so `src/main.py` itself has zero OTel API calls. Both `CMD`s are wrapped with `opentelemetry-instrument` (see `Dockerfile`/`Dockerfile.celery`), which reads standard `OTEL_*` env vars from the process environment at startup — those are set by whatever's deploying the containers (docker-compose, the Helm chart), not baked into the images, since `config.py`'s `app.config` is never consulted for them.

All three signals export via OTLP to `grafana/otel-lgtm` — an all-in-one image bundling an OTel Collector (OTLP on 4317/4318) with Grafana + Mimir (metrics) + Tempo (traces) + Loki (logs), so there's somewhere to view everything with zero extra setup. `docker-compose.yml` runs it as a fourth service (`otel-lgtm`, port 3000 for Grafana); the Helm chart deploys the same image as its own component (see Kubernetes deployment below). Look for `http_server_duration_milliseconds_*` (Flask, from WSGI auto-instrumentation) and `flower_task_runtime_seconds_*` (the `check_prime` Celery task, from Celery auto-instrumentation) as metric names; traces are searchable by `service.name` = `otel-test-app-flask`/`otel-test-app-celery` in Tempo.

**Logging gotcha**: getting actual application logs into Loki (not just metrics/traces) needed two more things beyond `OTEL_LOGS_EXPORTER=otlp`:
- `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true` — without it, `opentelemetry-instrumentation-logging` only adds trace/span-ID correlation to log records, it doesn't actually attach the handler that forwards them to the OTLP exporter.
- Both gunicorn and Celery configure their own loggers in ways that stop records from ever reaching the root logger where that OTel handler lives: gunicorn's default logging config sets `propagate: False` on `gunicorn.error`/`gunicorn.access` (fixed via `logconfig_dict` in `src/gunicorn_config.py`), and Celery replaces the root logger's handlers outright on worker startup unless `worker_hijack_root_logger` is disabled (fixed via `CELERYD_HIJACK_ROOT_LOGGER = False` in `src/config.py` — the old-style key name, since setting the new-style `worker_hijack_root_logger` directly conflicts with the old-style `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` keys already in use and Celery refuses to start with mixed key styles).

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

## Kubernetes deployment

`k8s/charts/otel-test-app` is a Helm chart deploying the same components (Flask app, Celery worker, Redis, and by default `otel-lgtm`) as separate Deployments/Services, wiring `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` and the `OTEL_*` env vars (see Observability above) to their respective in-cluster services automatically. Both app images share a single `image.tag` value (default `latest`) since CI always builds them from the same commit under the same tag — pin a specific release with `--set image.tag=<X.Y.Z>` (see Versioning above). Set `otel.exporterEndpoint`/`otelLgtm.enabled=false` to point at an external collector instead of the bundled one. See that chart's `README.md` for full values and usage.

A pre-built Grafana dashboard lives at `k8s/charts/otel-test-app/dashboards/otel-test-app.json` — it's the single source of truth for both `docker-compose.yml` (bind-mounted directly) and the Helm chart (embedded in a ConfigMap via `.Files.Get`), auto-provisioned into the bundled `otel-lgtm` Grafana on startup. Its `grafana-dashboards.yaml` sibling fully replaces the image's own dashboard-provisioning config (not a merge), so it re-declares the image's built-in dashboards by path alongside the new one — a purely additive-looking change there can silently drop the built-ins if it doesn't.

Chart-only changes (like the dashboard) don't need a new app image release — just commit to `main` and let ArgoCD auto-sync; only bump `image.tag` when `src/` actually changed.

`k8s/argocd/application.yaml` is an ArgoCD `Application` that deploys that chart from `main` with automated sync (`prune` + `selfHeal`) — image versioning stays git-driven (no Image Updater), so a release is two commits: tag `vX.Y.Z` to build the images, then bump `image.tag` in `values.yaml` on `main` to actually deploy it. See `k8s/argocd/README.md`, which also covers installing ArgoCD itself and reaching the app/ArgoCD UI on a local cluster like minikube (images are public on ghcr.io, so no pull secret is needed there).

**ArgoCD install gotcha**: installing ArgoCD's stock manifests requires `kubectl apply --server-side --force-conflicts` — a plain `kubectl apply` fails on the `applicationsets.argoproj.io` CRD (`metadata.annotations: Too long`) because the CRD is too large for the client-side `last-applied-configuration` annotation.
