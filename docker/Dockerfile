FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements-dev.txt pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt && \
    pip install opentelemetry-distro && \
    opentelemetry-bootstrap -a install && \
    pip install opentelemetry-exporter-otlp

COPY . .

CMD ["pytest", "tests/", "-v"]