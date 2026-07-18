# ArgoCD

`application.yaml` is an ArgoCD `Application` that deploys the [`otel-test-app` Helm chart](../charts/otel-test-app) from this repo's `main` branch into the `otel-test-app` namespace, with automated sync (`prune` + `selfHeal`) enabled — any change merged to `main` under `k8s/charts/otel-test-app` is applied automatically, and manual cluster drift is reverted.

## Installing ArgoCD (e.g. on minikube)

If the target cluster doesn't have ArgoCD yet:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side --force-conflicts
kubectl -n argocd wait --for=condition=Available deployment --all --timeout=300s
```

`--server-side --force-conflicts` is required — a plain `kubectl apply` fails on the `applicationsets.argoproj.io` CRD with `metadata.annotations: Too long: may not be more than 262144 bytes` (the CRD is too large for the client-side `last-applied-configuration` annotation).

The app's images (`ghcr.io/jon-allen-public/otel-test-app*`) are public, so no image pull secret is needed even on a fresh cluster like minikube.

## Register the app

```bash
kubectl apply -n argocd -f k8s/argocd/application.yaml
```

ArgoCD will create the `otel-test-app` namespace and start syncing.

## Accessing things locally (minikube)

```bash
# The app itself
kubectl -n otel-test-app port-forward svc/otel-test-app-flask 8080:8080
# -> http://localhost:8080

# Grafana, for the metrics/traces/logs both apps emit via OpenTelemetry
kubectl -n otel-test-app port-forward svc/otel-test-app-otel-lgtm 3000:3000
# -> http://localhost:3000 (anonymous admin access)

# The ArgoCD UI
kubectl -n argocd port-forward svc/argocd-server 8081:443
# -> https://localhost:8081, user "admin", password:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

## Releasing a new version

Image versioning is git-driven, not auto-detected — cutting a release is two steps:

1. **Build the images**: push a semver tag to trigger `.github/workflows/build.yaml`, which publishes `ghcr.io/jon-allen-public/otel-test-app:X.Y.Z` and `-celery:X.Y.Z`:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```
2. **Deploy it**: set `image.tag: "1.2.3"` in [`k8s/charts/otel-test-app/values.yaml`](../charts/otel-test-app/values.yaml) and push that commit to `main`. ArgoCD picks up the change and syncs it automatically.
