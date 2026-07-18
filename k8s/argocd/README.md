# ArgoCD

`application.yaml` is an ArgoCD `Application` that deploys the [`otel-test-app` Helm chart](../charts/otel-test-app) from this repo's `main` branch into the `otel-test-app` namespace, with automated sync (`prune` + `selfHeal`) enabled — any change merged to `main` under `k8s/charts/otel-test-app` is applied automatically, and manual cluster drift is reverted.

## Prerequisites

- ArgoCD already installed in the target cluster, in the `argocd` namespace.

## Register the app

```bash
kubectl apply -n argocd -f k8s/argocd/application.yaml
```

ArgoCD will create the `otel-test-app` namespace and start syncing.

## Releasing a new version

Image versioning is git-driven, not auto-detected — cutting a release is two steps:

1. **Build the images**: push a semver tag to trigger `.github/workflows/build.yaml`, which publishes `ghcr.io/jon-allen-public/otel-test-app:X.Y.Z` and `-celery:X.Y.Z`:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```
2. **Deploy it**: set `image.tag: "1.2.3"` in [`k8s/charts/otel-test-app/values.yaml`](../charts/otel-test-app/values.yaml) and push that commit to `main`. ArgoCD picks up the change and syncs it automatically.
