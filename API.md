# API.md — Programmatic Surfaces (v0.7.0)

EvoNAS has **no FastAPI server in v0.7.0**. This document lists **library APIs** for embedding.

## Entry Points

```python
from evonas.application.train_baseline import TrainBaselineUseCase
from evonas.application.optimize import OptimizeUseCase
from evonas.application.compare_optimizers import CompareOptimizersUseCase
from evonas.application.closed_loop.use_cases import RunClosedLoopUseCase
from evonas.application.continuous.use_cases import ContinuousLearningUseCase
```

## Ports (Protocols)

See `src/evonas/ports/`:

- `IDatasetManager`, `IDriftDetector`
- `ISearchAlgorithm`, `IAdaptiveController`
- `IClosedLoopController`, `IDecisionEngine`, …
- `IContinuousLearningEngine`, …

## Observation Bridge (Phase 6 ← Phase 7)

```python
obs = continuous_engine.to_observation()
# merge into ClosedLoopController observation / inject engine via constructor
```

## Stability

Frozen surfaces are listed in `docs/rc1/ARCHITECTURE_FREEZE.md`.
