# otel-test-app Helm chart

Deploys the Flask app, Celery worker, and a Redis broker/backend as three separate Deployments/Services in one release.

## Install

```bash
helm install otel-test-app ./k8s/charts/otel-test-app
```

## Reach the app

By default `flaskApp.service.type` is `ClusterIP`:

```bash
kubectl port-forward svc/otel-test-app-flask 8080:8080
```

Then visit http://localhost:8080. Set `flaskApp.service.type=LoadBalancer` or enable `ingress.enabled=true` (with `ingress.hosts`) for other access patterns.

## Key values

| Key | Default | Description |
|---|---|---|
| `image.tag` | `latest` | Tag applied to **both** `flaskApp` and `celeryWorker` images (see Versioning below) |
| `flaskApp.image.repository` | `ghcr.io/jon-allen-public/otel-test-app` | Flask app image |
| `celeryWorker.image.repository` | `ghcr.io/jon-allen-public/otel-test-app-celery` | Celery worker image |
| `redis.image.repository`/`tag` | `redis`/`alpine` | Redis broker/result backend |
| `flaskApp.service.type` | `ClusterIP` | How the Flask service is exposed |
| `ingress.enabled` | `false` | Enable an Ingress in front of the Flask service |

The chart wires `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` on both the Flask app and the Celery worker to the in-cluster Redis service automatically — no values needed for that.

## Versioning

Releases are cut by pushing a semver git tag (`vX.Y.Z`). `.github/workflows/build.yaml` builds both images from that commit and pushes each under two tags: the version number without the `v` prefix (e.g. `1.2.3`) and `latest`. A plain push to `main` (no tag) only refreshes `latest`. Since both images always come from the same commit, the chart exposes a single `image.tag` value shared by both, instead of separate per-component tags that could drift out of sync.

To cut a release:

```bash
git tag v1.2.3
git push origin v1.2.3
```

To deploy that specific release rather than whatever `latest` currently points to:

```bash
helm upgrade --install otel-test-app ./k8s/charts/otel-test-app --set image.tag=1.2.3
```
