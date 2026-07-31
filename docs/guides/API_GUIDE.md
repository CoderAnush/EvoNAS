# API Guide — EvoNAS v1.0.0

Full route table: [`docs/ops/API_REFERENCE.md`](../ops/API_REFERENCE.md).

## Start

```bash
pip install -e ".[api]"
evonas api --host 127.0.0.1 --port 8000
# Swagger: http://127.0.0.1:8000/docs
```

## Minimal checks

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/version
```

## Design contract

Handlers call **application use cases only** — no duplicated PSO/SAPSO math in routes. Dashboard consumes API JSON (no direct artifact IO in UI paths).

## Jobs

Submit async jobs under `/api/v1/.../jobs`, poll `/api/v1/jobs/{id}`, stream events on `WS /api/v1/ws/events`.

## Registry (Phase 11)

Additive routes: `/api/v1/registry/*`, `/api/v1/models/*` — metadata lifecycle only.
