# Release Notes — EvoNAS v0.1.0

**Tag:** `v0.1.0`  
**Codename:** Phase 1 — Data Pipeline Foundation  
**Date:** 2026-07-28  

## Summary

EvoNAS v0.1.0 freezes the **dataset management and data pipeline** milestone. The repository now provides a production-shaped, testable data plane that later phases (baseline models, SAPSO, closed loop) will consume.

## Highlights

- `IDatasetManager` + `DatasetManager` public facade
- Checksummed manifests and deterministic splits
- Statistics + PSI/KS drift utilities
- Config-driven dataset selection (`configs/default.yaml` → dataset YAML)
- 29 automated tests; ruff + mypy clean
- Quick Mode synthetic dataset ready for CI

## Install

```bash
git clone https://github.com/CoderAnush/EvoNAS.git
cd EvoNAS
git checkout v0.1.0
pip install -e ".[dev]"
evonas prepare-dataset --config configs/datasets/toy_quick.yaml
pytest -q
```

## Explicitly out of scope

- Neural network training / baselines (Phase 2)
- PSO / SAPSO (Phases 4–5)
- Closed-loop controller (Phase 6+)

## Documentation

- Engineering bible: [`idea.md`](idea.md)
- Phase report: [`docs/phase_reports/phase1.md`](docs/phase_reports/phase1.md)
- Changelog: [`CHANGELOG.md`](CHANGELOG.md)
