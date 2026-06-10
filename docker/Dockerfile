FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements-dev.txt pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt && \
    pip install opentelemetry-distro && \
    opentelemetry-bootstrap -a install && \
    pip install opentelemetry-exporter-otlp && \
    python -c "from cryptography.fernet import Fernet; open('master.key', 'wb').write(Fernet.generate_key())" && \
    python -c "import secrets; open('auth.key', 'wb').write(secrets.token_bytes(32))"

COPY . .

CMD ["pytest", "tests/", "-v", "--cov=acars_server", "--cov-report=html", "--cov-report=term-missing"]