# EvoNAS v0.7.0 RC1 — Integration Report

**Date:** 2026-07-30  
**Gates:** pytest · ruff · mypy · CLI E2E smoke

---

## Quality Gates

| Gate | Result |
|---|---|
| pytest | **117 passed** (~52s after warm cache) |
| Coverage (prior full run) | **~85%** line coverage on `evonas` |
| ruff | All checks passed |
| mypy | Success — 134 source files |

---

## End-to-End CLI Smoke (dry-run / simulation)

| Step | Command | Time | Result |
|---|---|---:|---|
| Version | `evonas version` | 0.81s | OK |
| Doctor | `evonas doctor` | 2.55s | OK |
| Dataset | `prepare-dataset --config configs/datasets/toy_quick.yaml` | 0.71s | OK |
| Standard PSO | `optimize --config configs/pso/mock_sphere.yaml --dry-run` | 3.71s | OK |
| SAPSO | `optimize --config configs/pso/adaptive_mock.yaml --dry-run` | 6.61s | OK |
| Compare | `compare-optimizers --config configs/optimization/pso_vs_sapso.yaml` | 2.83s | OK |
| Closed loop | `simulate-loop --config configs/closed_loop/simulate.yaml` | 7.44s | OK |
| Continuous learning | `learn --config configs/continuous_learning/default.yaml --cycles 2` | 1.66s | OK |
| Detect data | `detect-data --config configs/continuous_learning/default.yaml` | 0.70s | OK |

**Total smoke wall time (sequential):** ≈ **27s** (excluding pytest).

---

## Cross-Module Communication

| From → To | Mechanism | Status |
|---|---|---|
| CLI → Application use-cases | Direct imports | OK |
| Application → Domain engines | Service calls | OK |
| Application → Infrastructure | Adapters / ArtifactManager | OK |
| Continuous → ClosedLoop | `IContinuousLearningEngine.to_observation()` | OK |
| ClosedLoop → OptimizeUseCase | Existing Phase 4/5 API | OK |
| Drift | Phase 1 `detect_shift` / PSI+KS | OK — no duplicated math |

---

## Interface Respect

- Ports under `src/evonas/ports/` remain the DI surface.
- DecisionEngine still sole lifecycle authority.
- ContinuousLearningEngine emits recommendations only.
- Standard PSO / SAPSO equations unmodified in RC1 freeze polish.

---

## Artifact Generation

RC1 smoke wrote under `artifacts/rc1/` (~1.1 MB / 86 files): history JSON/CSV, summaries, plots where matplotlib available, lineage, decisions.

---

## Residual Risks

| Risk | Mitigation |
|---|---|
| Full NN training path slower / env-dependent | Covered by unit tests; smoke uses mock/dry-run |
| No GitHub Actions CI yet | Manual gates documented; add CI in GitHub prep |
| Torchvision loaders lightly covered | Optional extra; toy dataset is default demo path |
