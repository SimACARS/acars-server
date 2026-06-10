# docker/otel.Dockerfile
FROM otel/opentelemetry-collector:0.153.0

COPY docker/otel.yml /etc/otelcol/config.yaml