# Installation — EvoNAS v1.0.0

## Requirements

- Python **3.10+** (3.10/3.11 recommended)
- OS: Windows / macOS / Linux
- Optional: Docker for compose deploy

## Core install

```bash
pip install -e .
```

## Extras

| Extra | Purpose |
|-------|---------|
| `dev` | pytest, ruff, mypy |
| `pytorch` | training backend |
| `dashboard` | Streamlit + Plotly |
| `api` | FastAPI + uvicorn |

```bash
pip install -e ".[dev,pytorch,api,dashboard]"
```

## Verify

```bash
evonas version
evonas doctor
python -c "import evonas; print(evonas.__version__)"
```

## Reproducibility lock

See `reproducibility/REQUIREMENTS_LOCK.md` and `reproducibility/environment.yml` for the v1.0.0 release environment snapshot.

## Troubleshooting

- **Command not found:** ensure venv activated and `pip install -e .` succeeded.
- **Dashboard blank:** start API first or use `evonas serve`.
- **Torch missing:** install `.[pytorch]` only when training (not needed for mock/dry-run).
