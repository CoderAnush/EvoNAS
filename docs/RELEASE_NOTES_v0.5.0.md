# Release Notes — EvoNAS v0.5.0

**Date:** 2026-07-29  
**Codename:** Self-Adaptive Particle Swarm Optimization  

## Highlights

EvoNAS now runs **Self-Adaptive PSO (SAPSO)** with deterministic, explainable updates of \(w, c_1, c_2\) from swarm diversity, improvement rate, and stagnation. Standard PSO remains available for ablation under identical seeds.

## What you can do

```bash
# SAPSO on synthetic Sphere
evonas optimize --config configs/pso/adaptive_mock.yaml

# Compare Standard PSO vs SAPSO
evonas compare-optimizers --config configs/optimization/pso_vs_sapso.yaml
```

## Included

- `AdaptiveController`, `ParameterScheduler`, `AdaptiveStateMachine`
- `SelfAdaptivePSO` extending Phase 4 `StandardPSO` via coefficient hook
- Adaptive history + coefficient/diversity/phase plots
- Benchmark runner + optimizer comparison framework
- Configs under `configs/pso/` and `configs/optimization/`
- Phase 5 report and tests

## Not included

Closed-loop controller, continuous learning, decision engine, deployment, dashboard.

## Upgrade notes

- Package version is **0.5.0**.
- Phase 4 Standard PSO behaviour is preserved (regression-tested fixed coefficients).
