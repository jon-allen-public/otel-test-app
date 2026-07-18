# otel-test-app

A minimal Flask app that checks whether a number is prime, using a Celery worker (backed by Redis) to run the check asynchronously.

## Prerequisites

- Docker and Docker Compose

## Launching the app

```bash
docker compose up --build
```

This starts three services:

| Service        | Description                          | Port |
|----------------|---------------------------------------|------|
| `flask-app`    | Web UI (Gunicorn)                     | 8080 |
| `celery-worker`| Runs the prime-check task             | -    |
| `redis`        | Celery broker/result backend          | 6379 |

Once running, open **http://localhost:8080**.

To stop:

```bash
docker compose down
```

## Deploying to Kubernetes

A Helm chart is available at [`k8s/charts/otel-test-app`](k8s/charts/otel-test-app):

```bash
helm install otel-test-app ./k8s/charts/otel-test-app
```

See that chart's README for configuration details.

For a GitOps deployment, see [`k8s/argocd`](k8s/argocd) for an ArgoCD `Application` that auto-syncs this chart from `main` — including how to install ArgoCD itself on a fresh cluster like minikube and reach both the app and the ArgoCD UI locally.

## Notes

- `flask-app` and `celery-worker` both depend on `redis`; if either `redis` or `celery-worker` isn't up, submitting a number will hang for ~30s and then fail (the request blocks waiting on the Celery task result).
- There is no local (non-Docker) dev setup — see `CLAUDE.md` for why (`PYTHONPATH` requirements, import quirks) if you need to run it outside Docker.
