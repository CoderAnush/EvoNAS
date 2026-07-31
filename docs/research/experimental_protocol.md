# Experimental Protocol — Phase 12A

**Campaign:** Experimental Campaign & Scientific Validation  
**Platform baseline:** EvoNAS `v1.0.0-rc2` (frozen engines)  
**Authority:** `idea.md` REQ-RES fairness rules; Phase 10 orchestrator; Phase 11 registry (metadata only)  
**Status:** Binding for all Phase 12A runs

This document defines the scientific plan. It does **not** authorize changes to PSO, SAPSO, Dataset Manager, Trainer, Dynamic Builder, ClosedLoop, Continuous Learning, Dashboard, API, Registry internals, or CLI.

---

## 1. Research Questions

| ID | Question |
|----|----------|
| **RQ1** | Under identical search space, seed list, and evaluation budget, does Self-Adaptive PSO (SAPSO) achieve higher mean best fitness than Standard PSO on Sphere and Rastrigin mock landscapes? |
| **RQ2** | How do Standard PSO and SAPSO compare to Random Search under the same evaluation budget? |
| **RQ3** | Are relative rankings stable across landscapes (Sphere vs Rastrigin) and across compact vs extended budgets? |
| **RQ4** | Do SAPSO adaptive coefficient and diversity trajectories exhibit the intended explore→exploit dynamics (descriptive, not causal proof)? |

---

## 2. Hypotheses

| ID | Hypothesis | Related RQ |
|----|------------|------------|
| **H1** | Mean best fitness(SAPSO) ≥ mean best fitness(Standard PSO) on Sphere under maximize sense (α = 0.05, paired Wilcoxon when applicable). | RQ1 |
| **H2** | Mean best fitness(SAPSO) ≥ mean best fitness(Standard PSO) on Rastrigin under the same protocol. | RQ1 |
| **H3** | Both swarm methods outperform Random Search in mean best fitness at matched evaluation budgets. | RQ2 |
| **H4** | Algorithm rank order by mean fitness is consistent across landscapes for the paper-draft seed count (≥10). | RQ3 |

**Reporting rule:** Hypotheses may be supported, partially supported, or not supported. Negative or null SAPSO deltas are preserved verbatim. Winner declaration uses mean fitness only under the configured sense (`maximize`).

---

## 3. Evaluation Metrics

| Metric | Definition in this campaign | Notes |
|--------|----------------------------|-------|
| **Fitness** | Best fitness at stop (mock landscape) | Primary endpoint |
| **Accuracy** | Same as fitness for mock maximize landscapes (proxy) | Neural accuracy deferred |
| **Training time** | N/A (no NN training in Phase 12A mock campaign) | Recorded as `null` |
| **Optimization time** | Wall-clock seconds per seeded run | Primary runtime metric |
| **Model complexity** | Search-space dimensionality / gene count | Proxy; no CNN graphs on Sphere |
| **Inference cost** | N/A for continuous mock vectors | Recorded as `null` |
| **Memory usage** | Optional process RSS snapshot during instrumentation runs | Descriptive only |
| **Evaluations** | Fitness calls per run | Budget fairness check |
| **Iterations** | Optimizer iterations / trials | Reported |

Descriptive aggregates: mean, median, variance, std, min, max.  
CI: normal approximation `mean ± z · s/√n` (documented; not a normality claim).  
Significance: paired Wilcoxon signed-rank when SciPy available and n ≥ 3.  
Effect size: Cliff’s δ.

---

## 4. Datasets / Landscapes

Phase 12A uses **mock fitness landscapes** for reproducibility and CI-safe full campaigns (Phase 10 design). Neural datasets (MNIST/CIFAR) remain available in the platform but are **out of scope** for this campaign’s primary tables.

| ID | Landscape | Search space | Role |
|----|-----------|--------------|------|
| `sphere` | Sphere | `configs/search_spaces/sphere_2d.yaml` | Smooth unimodal control |
| `rastrigin` | Rastrigin | same 2D box | Multimodal stress test |

Fitness sense: **maximize** (MockFitnessEvaluator convention).

---

## 5. Optimizers & Budget

| Algorithm | Implementation | Production use |
|-----------|----------------|----------------|
| `standard_pso` | `StandardPSO` | Ablation / baseline |
| `sapso` | `SelfAdaptivePSO` | Production closed-loop engine |
| `random_search` | `evonas.benchmarks.RandomSearch` | Research baseline only |

**Budget fairness:** Random Search `n_trials = swarm_size × max_iterations` for the suite (matched evaluation count).

### Suite budgets

| Suite config | Swarm | Iterations | RS trials | Seeds |
|--------------|------:|-----------:|----------:|------:|
| `phase12a_sphere_paper` | 12 | 25 | 300 | 15 (base 42) |
| `phase12a_multi_landscape` | 12 | 25 | 300 | 12 (base 7) |
| `phase12a_budget_compact` | 8 | 15 | 120 | 10 (base 11) |
| `phase12a_budget_extended` | 16 | 40 | 640 | 10 (base 101) |

Stopping: optimizer-native stopping (max iterations / trials). No asymmetric early-stopping patience across methods.

---

## 6. Random Seed Policy

1. Seeds are generated as `base + i` for `i ∈ [0, n)` unless an explicit list is provided.
2. The same seed list is applied to every algorithm within a suite (paired comparisons).
3. Suite YAMLs freeze `seeds.n` and `seeds.base`; resolved configs are copied into each run directory.
4. Reproducibility requires matching `config_hash`, `git_commit`, and package version in `meta.json`.

---

## 7. Statistical Analysis Plan

1. Per (algorithm, dataset, config): summarize fitness, seconds, evaluations.
2. Pairwise: all algorithm×dataset cells with overlapping seed counts.
3. Rank tables: mean fitness rank within each landscape (1 = best under maximize).
4. Cross-suite consistency: compare winners / ranks between compact and extended budgets.
5. No post-hoc budget retuning after seeing results without a new experiment id.

---

## 8. Figures & Tables

Generated under each suite’s `figures/` and `tables/`, plus campaign-level instrumentation:

- Fitness comparison bars (± std)
- Runtime comparison
- Per-seed / convergence-style series
- SAPSO coefficient evolution (w, c1, c2)
- Swarm diversity curves
- Architecture / search-space complexity table (gene count, bounds)
- Summary tables: CSV, Markdown, LaTeX

---

## 9. Registry

1. Phase 10 `ExperimentRegistry` records each suite under `artifacts/research/`.
2. Phase 11 governance sync (`evonas registry sync`) indexes research experiments as metadata (never mutates result files).

---

## 10. Validation Checklist

- [ ] Identical space path per landscape cell across algorithms
- [ ] Matched evaluation budgets (PSO vs RS trials)
- [ ] Identical seed lists
- [ ] `checksums.json` present for key artifacts
- [ ] Re-run smoke cell reproduces mean fitness within floating tolerance
- [ ] Quality gates: `pytest`, `ruff`, `mypy` on frozen codebase

---

## 11. Threats to Validity (a priori)

- **Internal:** Seed and budget choices may favor some methods.
- **External:** Sphere/Rastrigin results may not transfer to CNN NAS spaces.
- **Construct:** Mock fitness is a proxy, not validation accuracy.
- **Conclusion:** Normal-approx CIs do not imply normality; Wilcoxon requires paired identical seeds.

---

## 12. Explicit non-goals (Phase 12A)

- No new algorithms, features, or architecture changes
- No paper drafting, website, auth, cloud, or K8s
- No modification of frozen optimizer / training / closed-loop / dashboard / API / registry / CLI code
