{{/*
Base name for chart resources.
*/}}
{{- define "otel-test-app.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Fully qualified app name, respecting .Release.Name.
*/}}
{{- define "otel-test-app.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "otel-test-app.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Redis connection URL used by both the Flask app and the Celery worker.
*/}}
{{- define "otel-test-app.redisUrl" -}}
redis://{{ include "otel-test-app.fullname" . }}-redis:{{ .Values.redis.service.port }}/0
{{- end -}}

{{/*
OTLP gRPC endpoint used by both the Flask app and the Celery worker.
*/}}
{{- define "otel-test-app.otlpEndpoint" -}}
{{- if .Values.otel.exporterEndpoint -}}
{{ .Values.otel.exporterEndpoint }}
{{- else -}}
http://{{ include "otel-test-app.fullname" . }}-otel-lgtm:{{ .Values.otelLgtm.service.otlpGrpcPort }}
{{- end -}}
{{- end -}}
