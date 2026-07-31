# Deployment Diagram — EvoNAS v1.0.0

```mermaid
flowchart TB
  subgraph Host["Developer / Lab Host"]
    PY[Python 3.10+]
    PIP[pip install -e .]
    CFG[configs/]
    ART[(artifacts/)]
    PY --> API[uvicorn FastAPI :8000]
    PY --> DASH[streamlit :8501]
    PY --> CLI[evonas CLI]
    API --> ART
    API --> CFG
    DASH --> API
    CLI --> ART
    CLI --> API
  end
  subgraph Docker["Optional Compose"]
    CAPI[evonas-api]
    CDASH[evonas-dashboard]
    CDASH --> CAPI
  end
  Browser((Browser)) --> DASH
  Browser --> API
  Browser --> CDASH
```

## Profiles

| Profile | Command | Notes |
|---------|---------|-------|
| CLI-only | `evonas …` | No servers |
| Local serve | `evonas serve --demo` | API + dashboard |
| Docker | `docker compose up` | See `docs/ops/DEPLOYMENT.md` |
| Research | `evonas benchmark` / `python scripts/run_phase12a_campaign.py` | Writes `artifacts/research/` |

Cloud / K8s / auth: **out of scope for v1.0.0**.
