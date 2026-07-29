# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EVONAS_ENV=production \
    EVONAS_ARTIFACTS_ROOT=/data/artifacts

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY configs ./configs
RUN pip install --no-cache-dir -e ".[api,dev]"

RUN mkdir -p /data/artifacts
VOLUME ["/data/artifacts"]

EXPOSE 8000
CMD ["uvicorn", "evonas.presentation.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
