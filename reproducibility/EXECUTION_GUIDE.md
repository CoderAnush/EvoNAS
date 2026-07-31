# Execution Guide — Reproduce EvoNAS v1.0.0

## A. Software smoke

```bash
git checkout v1.0.0
pip install -e ".[dev]"
evonas version
pytest -q
ruff check src tests
mypy src
```

## B. Mock optimize

```bash
evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run
```

## C. Phase 12A-style suite (small)

```bash
evonas benchmark --config configs/benchmarks/default.yaml
# Inspect artifacts/research/<experiment_id>/meta.json → config_hash
```

## D. Full Phase 12A campaign (optional, longer)

```bash
python scripts/run_phase12a_campaign.py
# Compare means to paper/ieee_manuscript.md / hypothesis_status.json
```

## E. API + dashboard

```bash
pip install -e ".[api,dashboard]"
evonas serve --demo
```
