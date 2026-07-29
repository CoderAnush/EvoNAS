# API Reference (Phase 9)

Base URL: `http://127.0.0.1:8000`

Interactive docs: `/docs` (Swagger) · `/redoc`

## Core

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Liveness `{status, version}` |
| GET | `/api/v1/status` | Health + job queue |
| GET | `/api/v1/system` | CPU/memory/artifacts/lifecycle |
| GET | `/api/v1/version` | Package version |
| GET | `/api/v1/config` | Resolved API + dashboard settings |

## Dashboard payloads

All under `/api/v1/dashboard/*` — `landing`, `overview`, `optimization`, `sapso`, `lifecycle`, `continuous`, `training`, `architecture`, `experiments`, `comparison`, `health`, `settings`.

`POST /api/v1/dashboard/demo` with `{"demo": true}` enables presentation mode.

## Jobs

`POST /api/v1/{optimization|training|closed-loop|continuous-learning|benchmarks}/jobs`

Body example:

```json
{"config_path": "configs/pso/adaptive_mock.yaml", "dry_run": true}
```

Track: `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `POST /api/v1/jobs/{id}/cancel`

## Artifacts / replay / experiments

- `GET /api/v1/artifacts?root=artifacts`
- `POST /api/v1/artifacts/preview` `{"path": "..."}`
- `GET /api/v1/artifacts/download?path=...`
- `GET /api/v1/replay/{source}`
- `GET /api/v1/experiments?kind=&q=`

## WebSocket

`WS /api/v1/ws/events` — JSON messages `{type: "job"|"ping", ...}`

## Contract

API handlers call **application services / use cases only** — no duplicated PSO/SAPSO/training logic (`REQ-API-001`).
