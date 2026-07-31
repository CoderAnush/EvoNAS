# Phase 12A Report — Experimental Campaign & Scientific Validation

**Status:** Complete  
**Platform baseline:** v1.0.0-rc2 (`1.0.0rc2`) — **frozen**  
**Date:** 2026-07-31  
**Commit at run:** recorded in `artifacts/research/phase12a_campaign/manifest.json`

## Summary

Phase 12A executes a full scientific campaign using the existing Phase 10 orchestrator and Phase 11 registry sync. **No optimizer, trainer, closed-loop, dashboard, API, registry, or CLI code was modified.** Deliverables are protocol documentation, benchmark YAML suites, a campaign runner script, and `artifacts/research/` evidence.

## What was produced

| Deliverable | Location |
|-------------|----------|
| Experimental protocol | `docs/research/experimental_protocol.md` |
| Suite configs | `configs/benchmarks/phase12a_*.yaml` |
| Campaign runner | `scripts/run_phase12a_campaign.py` |
| Suite outputs | `artifacts/research/phase12a_{sphere_paper,multi_landscape,budget_compact,budget_extended}/` |
| Campaign index | `artifacts/research/phase12a_campaign/` |
| Governance sync | via `GovernanceService.sync()` (metadata only) |

## Suites

| Experiment ID | Landscapes | Seeds | Budget |
|---------------|------------|------:|--------|
| `phase12a_sphere_paper` | Sphere | 15 | 12×25 / RS 300 |
| `phase12a_multi_landscape` | Sphere + Rastrigin | 12 | 12×25 / RS 300 |
| `phase12a_budget_compact` | Sphere + Rastrigin | 10 | 8×15 / RS 120 |
| `phase12a_budget_extended` | Sphere + Rastrigin | 10 | 16×40 / RS 640 |

Algorithms: Standard PSO, SAPSO, Random Search (matched evaluation budgets).

## Headline scientific outcomes (honest)

From `hypothesis_status.json` (maximize sense; higher / less-negative fitness is better):

| Hypothesis | Result |
|------------|--------|
| H1 SAPSO ≥ PSO on Sphere | **Not supported** (PSO edged SAPSO) |
| H2 SAPSO ≥ PSO on Rastrigin | **Not supported** |
| H3 Swarm methods beat Random Search | **Supported** (both landscapes) |
| H4 Rank consistency across budgets/landscapes | **Supported** (identical order: PSO > SAPSO > RS) |

Bit-exact reproducibility smoke (PSO re-run): **passed**.

## Integrity note

Negative SAPSO deltas are preserved. The framework does not favor SAPSO. On these 2D mock landscapes with the declared budgets, Standard PSO ranked first; both swarm methods substantially outperformed Random Search.

## Explicit non-changes

PSO, SAPSO, Dataset Manager, Trainer, Dynamic Builder, ClosedLoop, Continuous Learning, Dashboard, API, Registry, CLI — untouched.

## Deferred

Neural (MNIST/CIFAR) campaigns, paper drafting, camera-ready 30–50 seeds, website, auth, cloud.
