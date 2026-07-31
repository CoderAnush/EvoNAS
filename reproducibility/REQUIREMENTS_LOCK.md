# Requirements Lock — EvoNAS v1.0.0

Pinned lockfiles are environment-specific. Generate on the release machine:

```bash
python -m venv .venv
source .venv/bin/activate  # or Windows Scripts\activate
pip install -e ".[dev,api,dashboard]"
pip freeze > reproducibility/requirements-lock.txt
```

Commit `requirements-lock.txt` only if the team wants a frozen CI snapshot for this OS/Python.

**Minimum declared deps** live in `pyproject.toml` (`numpy`, `pydantic`, `PyYAML`, `scipy` + extras).

## Verify

```bash
pip check
evonas version   # 1.0.0
pytest -q
```
