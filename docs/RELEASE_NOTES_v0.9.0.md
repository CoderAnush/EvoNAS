# Release Notes — v0.9.0

**EvoNAS Platform Services & Deployment Layer (Phase 9)**

## Highlights

- FastAPI control plane on port **8000** with OpenAPI (`/docs`, `/redoc`)
- Application platform services + FastAPI dependency injection
- Background **JobManager** for optimization, training, closed-loop, CL, benchmarks, replay
- **WebSocket** `/api/v1/ws/events` for live job updates
- Dashboard is **API-backed only** (no direct artifact filesystem access from Streamlit)
- Docker images + `docker-compose.yml` (api + dashboard)
- CLI: `evonas api`, `evonas serve`, `evonas status`

## Install

```bash
pip install -e ".[api,dashboard,dev]"
cp .env.example .env
evonas serve --demo
```

## Compatibility

- Existing domain / PSO / SAPSO / ClosedLoop / Continuous Learning / trainers **unchanged**
- Artifact layouts from Phases 1–8 remain valid
- Optional extra: `evonas[api]`

## Not in this release

Auth, cloud, Kubernetes, external databases, enterprise security.
