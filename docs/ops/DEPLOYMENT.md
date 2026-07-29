# Deployment Guide (Phase 9 — local / Docker only)

## Local (developer)

```bash
pip install -e ".[api,dashboard,dev]"
cp .env.example .env
evonas serve --demo
```

- API: http://127.0.0.1:8000  (Swagger: `/docs`)
- Dashboard: http://127.0.0.1:8501
- Status: `evonas status`

API only:

```bash
evonas api --port 8000
# another terminal
set EVONAS_API_URL=http://127.0.0.1:8000
evonas dashboard --demo
```

## Docker Compose

```bash
docker compose up --build
```

Services:

| Service | Port | Image |
|---------|------|-------|
| `api` | 8000 | `Dockerfile` |
| `dashboard` | 8501 | `Dockerfile.dashboard` |

Artifacts persist in the `artifacts` volume (`/data/artifacts` in containers).

## Configuration

| Source | Purpose |
|--------|---------|
| `configs/api/default.yaml` | API host/port/CORS/jobs/logging |
| `configs/deploy/localhost.yaml` | Local topology |
| `configs/deploy/docker.yaml` | Compose topology |
| `.env` / `.env.example` | Ports, log level, API URL |

Environment overrides: `EVONAS_API_HOST`, `EVONAS_API_PORT`, `EVONAS_API_URL`, `EVONAS_LOG_LEVEL`, `EVONAS_JSON_LOGS`, `EVONAS_ARTIFACTS_ROOT`, `EVONAS_ENV`.

## Out of scope

Cloud providers, Kubernetes manifests, TLS termination, authentication proxies.
