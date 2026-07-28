# Release Notes — EvoNAS v0.4.0

**Date:** 2026-07-28  
**Codename:** Standard Particle Swarm Optimization  

## Highlights

EvoNAS can now run classical PSO over architecture genotypes: swarm → decode → train → fitness → velocity/position updates → best architecture + reproducible history. Coefficients are fixed (not self-adaptive).

## What you can do

```bash
# Synthetic Sphere smoke (no neural training)
evonas optimize --config configs/pso/mock_sphere.yaml --dry-run

# Quick Mode architecture search (trains tiny nets)
evonas optimize --config configs/pso/standard.yaml --out artifacts/optimization
```

## Included

- `Particle`, `Swarm`, `StandardPSO` (fixed \(w, c_1, c_2\))
- `ISearchAlgorithm` / `IFitnessEvaluator` ports
- Mock + architecture fitness evaluators with evaluation cache
- SearchSpace adapter, stopping criteria, history export, plots
- CLI `evonas optimize`
- Phase 4 report and tests

## Not included

SAPSO, adaptive inertia/acceleration, closed-loop control, continuous learning, deployment, dashboards.

## Upgrade notes

- Package version is **0.4.0**.
- Phases 1–3 APIs remain backward compatible.
