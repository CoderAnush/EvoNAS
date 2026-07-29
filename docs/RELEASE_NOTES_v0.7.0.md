# Release Notes — EvoNAS v0.7.0

**Date:** 2026-07-29  
**Codename:** Continuous Learning & Data Evolution  

## Highlights

EvoNAS can now **detect, version, and prepare evolving datasets**, compute drift with Phase 1 PSI/KS, and emit **recommendations only** (`HOLD` / `RETRAIN_SAME_ARCH` / `OPTIMIZE_ARCH`). The Phase 6 Decision Engine remains the sole authority for starting optimization.

## What you can do

```bash
# Simulate continuous learning cycles
evonas learn --config configs/continuous_learning/default.yaml --cycles 2

# Detect dataset changes
evonas detect-data --config configs/continuous_learning/default.yaml

# Replay a prior learning history
evonas replay-learning --history artifacts/continuous_learning/.../learning_history.json
```

## Included

- `ContinuousLearningEngine` + versioning / change detection / incremental builder
- Learning policy + lineage + retention + window cursors
- Replay support + history/plots
- CLI `learn` / `detect-data` / `replay-learning`
- Optional ClosedLoop observation mapping via published `to_observation()`

## Not included

Dashboard, FastAPI, cloud deploy, external DBs, notifications, auth, model registry (later phases).

## Upgrade notes

- Package version is **0.7.0**.
- Phase 1–6 behaviour preserved; CL does not modify PSO/SAPSO or DecisionEngine rules.
