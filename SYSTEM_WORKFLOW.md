# SYSTEM_WORKFLOW.md

## Target Lifecycle (idea.md)

```text
Observe → Detect/Version Data (CL) → Decision Engine
  → Optimize (PSO|SAPSO) → Train → Evaluate → Validate
  → Promote|Reject (local) → Observe
```

## Implemented Through v0.7.0

```mermaid
flowchart TB
  DS[DatasetManager] --> ARCH[Architecture IR]
  ARCH --> TRAIN[Train/Eval]
  TRAIN --> PSO[Standard PSO]
  TRAIN --> SAPSO[SAPSO]
  CL[ContinuousLearningEngine] -->|to_observation| CLC[ClosedLoopController]
  CLC --> DE[DecisionEngine]
  DE -->|YES| OPT[OptimizeUseCase]
  OPT --> PSO
  OPT --> SAPSO
  CLC --> VAL[Validation/Promotion]
  CLC --> HIST[Artifacts/History]
```

## What Is Explicitly Out of Scope Now

Cloud deploy, FastAPI, dashboard UI, model registry, notifications.
