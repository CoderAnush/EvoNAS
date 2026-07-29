# EvoNAS v0.7.0 RC1 — Performance Report

**Date:** 2026-07-30  
**Machine note:** Developer laptop (Windows); figures are indicative, not publication benchmarks.

---

## CLI Responsiveness

| Operation | Wall time |
|---|---:|
| `evonas version` | ~0.8s |
| `evonas doctor` | ~2.6s |
| Prepare toy dataset | ~0.7s |
| Mock Standard PSO | ~3.7s |
| Mock SAPSO | ~6.6s |
| Optimizer comparison (mock) | ~2.8s |
| Simulate closed-loop (1 cycle) | ~7.4s |
| Continuous learning (2 cycles) | ~1.7s |
| Detect-data | ~0.7s |

**Startup:** Import + argparse typically &lt; 1s for trivial commands; first torch-related path may be higher if pytorch installed.

---

## Test Suite

| Metric | Value |
|---|---|
| Full pytest | ~52–85s depending on cache/coverage |
| pytest + coverage | ~86s (prior RC1 run) |

---

## Artifact Footprint (RC1 smoke)

| Subsystem | Approx size | Files |
|---|---:|---:|
| Closed-loop simulate | ~417 KB | 30 |
| SAPSO mock | ~393 KB | 24 |
| Standard PSO mock | ~140 KB | 13 |
| Continuous learning | ~117 KB | 15 |
| Compare | ~6 KB | 3 |
| **Total RC1 smoke tree** | **~1.1 MB** | **86** |

History JSON/CSV remain small; plots dominate when matplotlib Agg is available.

---

## Memory / Training

| Path | Notes |
|---|---|
| Mock fitness | Negligible; CI-friendly |
| Toy dataset train | Phase 2 baseline tests; not timed in RC1 smoke |
| Architecture fitness (real NN) | Heavier; use Quick configs / subsets |

---

## Recommendations (no algorithm changes)

1. Keep demo / CI on mock fitness + toy dataset.
2. Document expected wall-clock for Research Mode separately before paper experiments.
3. Add optional CI job with timeout budgets matching Quick Mode (&lt; 10 minutes per idea.md).
