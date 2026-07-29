# Release Notes — EvoNAS v0.6.0

**Date:** 2026-07-29  
**Codename:** Closed-Loop Autonomous Optimization Controller  

## Highlights

EvoNAS becomes an **autonomous lifecycle orchestrator**: observe system state, evaluate configurable policies, run Standard PSO or SAPSO when authorized, validate candidates, and locally accept or reject them — with full decision and transition audit trails. Optimization engines from Phases 4–5 are unchanged.

## What you can do

```bash
# Deterministic simulation (mock fitness, no deployment)
evonas simulate-loop --config configs/closed_loop/simulate.yaml

# Closed-loop cycle (dry-run uses mock fitness)
evonas run-loop --config configs/closed_loop/default.yaml --dry-run

# Inspect artifacts from a prior run
evonas inspect-loop --run-dir artifacts/closed_loop/<run_id>
```

## Included

- `ClosedLoopController` + `WorkflowExecutor`
- `DecisionContext`, `DecisionEngine`, `DecisionPolicy`
- `OptimizationTrigger`, lifecycle state machine, history recorder
- `ValidationEngine`, `PromotionManager` (local only)
- Failure recovery → safe monitoring
- Lifecycle plots (timeline, decisions, transitions, acceptance)
- Ports under `evonas.ports.closed_loop`
- Phase 6 report and tests

## Not included

Continuous learning windows, cloud deploy, FastAPI, dashboard, model registry, production monitoring, notifications, rollback infrastructure (later phases).

## Upgrade notes

- Package version is **0.6.0**.
- Standard PSO and SAPSO behaviour preserved; controller only calls `OptimizeUseCase`.
- Default closed-loop algorithm is **SAPSO** (`optimization.algorithm: sapso`).
