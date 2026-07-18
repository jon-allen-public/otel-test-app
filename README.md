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

## Notes

- `flask-app` and `celery-worker` both depend on `redis`; if either `redis` or `celery-worker` isn't up, submitting a number will hang for ~30s and then fail (the request blocks waiting on the Celery task result).
- There is no local (non-Docker) dev setup — see `CLAUDE.md` for why (`PYTHONPATH` requirements, import quirks) if you need to run it outside Docker.
