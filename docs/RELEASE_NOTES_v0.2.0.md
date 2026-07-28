# Release Notes — EvoNAS v0.2.0

**Tag:** `v0.2.0` (prepare locally when releasing)  
**Codename:** Phase 2 — Baseline Learning System  
**Date:** 2026-07-28  

## Summary

v0.2.0 adds a complete baseline training pipeline on top of the Phase 1 data plane. You can load a dataset, build a fixed baseline CNN, train/validate/evaluate on CPU, save checkpoints, and record reproducible experiment artifacts — without any architecture search.

## Highlights

- `ArchitectureSpec` + `ModelFactory` + `BaselineCNN`
- `PyTorchTrainingEngine` / `PyTorchEvaluationEngine`
- Classification metrics: accuracy, precision, recall, F1, confusion matrix
- Checkpoints (`best` / `latest`) + experiment recorder
- CLI: `evonas train --config configs/training/baseline.yaml`
- 40 tests; ruff + mypy clean

## Install / run

```bash
pip install -e ".[dev,pytorch]"
evonas train --config configs/training/baseline.yaml
pytest -q
```

## Out of scope

PSO, SAPSO, NAS, closed-loop control, deployment, dashboard (later phases).

## Docs

- [`docs/phase_reports/phase2.md`](phase_reports/phase2.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
