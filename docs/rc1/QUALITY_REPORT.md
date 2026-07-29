# EvoNAS v0.7.0 RC1 — Quality Report

**Date:** 2026-07-30

---

## Automated Gates

| Tool | Result |
|---|---|
| pytest | 117 passed |
| Coverage | ~85% lines (`evonas`) |
| ruff | Clean |
| mypy | Clean (134 files) |

---

## Coverage Hotspots (intentional / deferred)

| Module | Cover | Note |
|---|---:|---|
| `torchvision_loader.py` | 0% | Optional pytorch path |
| `baseline_cnn.py` | 0% | Historical reference (Phase 3 DynamicNetwork) |
| Ports (`*.py` Protocols) | 0% | Type-only surfaces |
| `architecture_fitness.py` | ~37% | Real NN eval; mock path dominates tests |
| `retention.py` / `windows.py` | mid | Exercised partially; expand in Phase 7+ follow-ups |

---

## Code Smells / Debt (tracked, not blocking RC1)

1. Dual continuous config directories (documented).
2. `run` / `replay` CLI aliases still redirect (full mode wiring later).
3. Deploy / rollback DecisionEngine paths gated until Phase 8.
4. No CI workflow yet.
5. Matplotlib optional — plots skipped gracefully without it.

---

## Complexity

Core risk areas (acceptable for research platform):

- `ClosedLoopController` — orchestrator; delegates to WorkflowExecutor
- `ContinuousLearningEngine` — data evolution; does not authorize optimization
- `SelfAdaptivePSO` / `AdaptiveController` — research core; frozen for RC1

---

## Freeze Polish Applied in RC1

- Domain hashing extracted to `domain/common/hashing.py` (layering)
- Continuous plots invoked from application layer (not domain)
- README extras aligned with `pyproject.toml`
- Stale application package docstring fixed
