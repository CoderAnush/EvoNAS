# EvoNAS v0.7.0 RC1 — Architecture Freeze Report

**Date:** 2026-07-30  
**Authority:** `idea.md`  
**Frozen version:** **v0.7.0**

---

## Freeze Statement

Phases **1–7** are **API-frozen** for Release Candidate 1. Downstream phases (8+) must extend via ports and configs — not by rewriting frozen engines.

---

## Stable APIs (Do Not Break)

| Surface | Package / Symbol |
|---|---|
| Dataset plane | `IDatasetManager`, `IDriftDetector`, `DatasetManager` |
| Architecture IR | `ArchitectureSpec`, `SearchSpace`, `ArchitectureGenerator` |
| Training | `ITrainingEngine`, `IEvaluationEngine`, `TrainBaselineUseCase` |
| Standard PSO | `StandardPSO`, `StandardPSOConfig`, fixed \(w,c_1,c_2\) |
| SAPSO | `SelfAdaptivePSO`, `AdaptiveController` (hook-only extension) |
| Closed loop | `IClosedLoopController`, `IDecisionEngine`, `DecisionContext` |
| Continuous learning | `IContinuousLearningEngine`, `LearningResult.to_observation()` |
| CLI entry | `evonas` console script |

---

## Extension Points (Preferred)

1. New search spaces via YAML + gene schema  
2. New fitness evaluators implementing evaluator protocols  
3. Inject `continuous_learning` into ClosedLoopController  
4. Policy YAML for DecisionEngine / LearningPolicy  
5. Future deploy adapters behind ports (Phase 8) — **do not** embed in SAPSO

---

## Do Not Modify (without major version)

- Standard PSO velocity / position equations  
- SAPSO adaptive math without research ablation + version bump  
- Phase 1 checksum / split determinism contracts  
- DecisionEngine as sole lifecycle authority  
- ContinuousLearningEngine authorizing optimization directly  

---

## Configuration Contracts

| Path | Role |
|---|---|
| `configs/datasets/*` | Dataset prepare |
| `configs/training/*` | Baseline train |
| `configs/pso/*` | PSO / SAPSO |
| `configs/closed_loop/*` | Lifecycle |
| `configs/continuous_learning/*` | CL (canonical) |
| `configs/continuous/*` | CL alias (idea.md) |
| `configs/policies/*` | Decision policies |

---

## Known Non-Goals Until Later Phases

Deployment, rollback infra, FastAPI, dashboard, model registry, notifications, external DBs.
