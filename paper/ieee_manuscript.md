# EvoNAS: An Autonomous Closed-Loop Neural Architecture Search Platform with Self-Adaptive Particle Swarm Optimization

**IEEE-oriented manuscript draft (Phase 12B)**  
**Software version cited:** EvoNAS `v1.0.0-rc2`  
**Empirical campaign:** Phase 12A (mock Sphere / Rastrigin)  
**Status:** Draft for internal review — not camera-ready

> **Integrity statement.** All numeric experimental results below are copied from Phase 12A artifacts under `artifacts/research/`. Claims without Phase 12A evidence are marked `[PLACEHOLDER]`. Negative or null SAPSO advantages are reported honestly.

---

## Abstract

Continuous operation of neural models requires not only one-shot Neural Architecture Search (NAS) but also governed redesign, evaluation, and lifecycle control. EvoNAS is an open, Clean-Architecture AutoML platform that couples Self-Adaptive Particle Swarm Optimization (SAPSO) with a closed-loop controller, continuous-learning recommendations, experiment registry, and research benchmarking. This paper presents the system architecture and reports a fair multi-seed comparison of Standard PSO, SAPSO, and Random Search on Sphere and Rastrigin mock landscapes under matched evaluation budgets (Phase 12A). Across all suites, the mean-fitness rank order was Standard PSO ≻ SAPSO ≻ Random Search; swarm methods substantially outperformed Random Search, while SAPSO did not dominate Standard PSO on these 2D controls. Bit-exact reproducibility of Standard PSO re-runs was confirmed. Neural-image NAS results and closed-loop drift case studies are deferred `[PLACEHOLDER: neural campaign]`.

**Index Terms**—Neural Architecture Search, Particle Swarm Optimization, Self-Adaptive PSO, AutoML, Closed-Loop Systems, Reproducibility.

---

## I. Introduction

Neural Architecture Search (NAS) and AutoML have reduced manual model design cost, yet many research prototypes stop at offline search. Production-facing systems additionally require monitoring, decision policies, rollback, auditability, and reproducible experiment packages. EvoNAS addresses this gap by treating **continuous, policy-governed architecture evolution** as the product thesis, with SAPSO as the production search engine and Standard PSO / Random Search retained as research baselines only.

### Contributions

1. A Clean-Architecture reference implementation of an autonomous NAS/AutoML lifecycle (dataset plane through governance registry).
2. Self-Adaptive PSO with explicit coefficient adaptation and diversity-aware phase control, isolated from research baselines.
3. A fair scientific evaluation framework (Phase 10) and executed Phase 12A campaign with multi-seed statistics, figures, and registry metadata.
4. Honest reporting: on Phase 12A mock landscapes, SAPSO did **not** outperform Standard PSO; both beat Random Search; ranks were stable across landscapes and budgets.

### Research questions (Phase 12A)

- **RQ1:** Does SAPSO achieve higher mean best fitness than Standard PSO under identical seeds and budgets?
- **RQ2:** How do swarm methods compare to Random Search at matched evaluations?
- **RQ3:** Are ranks stable across Sphere vs Rastrigin and compact vs extended budgets?
- **RQ4:** Do SAPSO coefficient/diversity trajectories exhibit intended explore→exploit dynamics (descriptive)?

---

## II. Related Work

### A. Neural Architecture Search and AutoML

NAS surveys and platforms emphasize search-space design, weight sharing, and Bayesian / evolutionary / RL searchers `[PLACEHOLDER: cite Elsken et al.; White et al.; Auto-Keras; NASLib]`. EvoNAS positions NAS as a subsystem inside a broader autonomous loop rather than as a standalone optimizer paper.

### B. Particle Swarm Optimization and Adaptive Variants

Classical PSO uses fixed inertia and acceleration coefficients `[PLACEHOLDER: cite Kennedy & Eberhart 1995]`. Adaptive PSO variants schedule \(w,c_1,c_2\) from progress or diversity signals `[PLACEHOLDER: cite Zhan et al.; Clerc & Kennedy]`. EvoNAS SAPSO implements rule-based adaptation with an explicit phase state machine.

### C. Closed-Loop and Continual AutoML

MLOps and continual learning literature discuss drift detection, retraining triggers, and deployment gates `[PLACEHOLDER: cite Sculley et al.; Lu et al. drift survey]`. EvoNAS separates **recommendations** (continuous learning) from **decisions** (closed-loop controller) under audited policies.

### D. Research Integrity in Optimizer Comparisons

Fair NAS/optimizer comparisons require matched budgets, shared seeds, and unbiased reporting `[PLACEHOLDER: cite Lindauer & Hutter; Eggensperger et al.]`. Phase 12A follows a pre-registered protocol (`docs/research/experimental_protocol.md`).

---

## III. Methodology

### A. Fairness rules

1. Identical search space per landscape cell.
2. Matched evaluation budget: Random Search `n_trials = swarm_size × max_iterations`.
3. Identical seed lists for paired comparisons.
4. Frozen configuration snapshots and SHA-256 config hashes.
5. Winner by mean fitness under configured sense only (maximize).

### B. Statistics

Descriptive: mean, median, variance, std, min/max.  
CI: normal approximation \(\bar{x} \pm z\cdot s/\sqrt{n}\) (not a normality claim).  
Optional: paired Wilcoxon signed-rank; Cliff’s \(\delta\) effect size.

### C. Execution stack

ExperimentOrchestrator expands algorithm × dataset × seed matrices, invokes `BenchmarkRunner` over `ISearchAlgorithm`, and exports tables (CSV/Markdown/LaTeX), figures (PNG/SVG/PDF), and research registry entries. Governance registry sync is metadata-only.

---

## IV. Architecture

EvoNAS follows Clean Architecture under `src/evonas/`:

- **Domain:** search space, PSO/SAPSO, fitness, closed-loop policies, registry types.
- **Application:** use-cases (optimize, train, benchmark, governance).
- **Infrastructure:** PyTorch trainer, file artifacts, mock fitness, file registry.
- **Presentation:** CLI, FastAPI, Streamlit dashboard.
- **Ports:** `ISearchAlgorithm`, `IFitnessEvaluator`, registry ports.
- **Benchmarks quarantine:** `evonas.benchmarks` (Random Search) is never the production closed-loop engine.

`[PLACEHOLDER: insert system architecture figure from docs]`

---

## V. Self-Adaptive PSO (SAPSO)

SAPSO extends Standard PSO by adapting \((w,c_1,c_2)\) each iteration via an `AdaptiveController` driven by improvement rate, normalized diversity, and phase transitions (exploration / balanced / stagnation recovery). The velocity update retains the classical form; only coefficients change. Adaptive history is exportable for coefficient and diversity plots (Phase 12A instrumentation).

Production closed-loop wiring binds SAPSO exclusively; Standard PSO remains an ablation/research engine.

---

## VI. Closed Loop

The closed-loop controller observes metrics/drift signals, consults decision policies, may trigger SAPSO search, evaluates candidates, and records DecisionRecords for audit and rollback metadata. Continuous learning may **recommend** actions but does not silently authorize deployment. Phase 12A did **not** re-execute closed-loop drift scenarios; those remain `[PLACEHOLDER: closed-loop empirical case study]`.

---

## VII. Experimental Setup

**Platform:** EvoNAS `v1.0.0-rc2`, git commit recorded in campaign manifest (`1f6848c…`).  
**Fitness:** Mock Sphere / Rastrigin, sense = maximize (proxy; neural accuracy N/A).  
**Space:** `configs/search_spaces/sphere_2d.yaml` (2 continuous genes).  
**Algorithms:** `standard_pso`, `sapso`, `random_search`.

| Suite | Landscapes | Seeds | Swarm × Iters | RS trials |
|-------|------------|------:|--------------:|----------:|
| `phase12a_sphere_paper` | Sphere | 15 | 12×25 | 300 |
| `phase12a_multi_landscape` | Sphere, Rastrigin | 12 | 12×25 | 300 |
| `phase12a_budget_compact` | Sphere, Rastrigin | 10 | 8×15 | 120 |
| `phase12a_budget_extended` | Sphere, Rastrigin | 10 | 16×40 | 640 |

**Deferred:** MNIST/CIFAR neural evaluation `[PLACEHOLDER]`; camera-ready 30–50 seeds `[PLACEHOLDER]`.

---

## VIII. Results

All values from `artifacts/research/phase12a_campaign/` and suite tables. Fitness sense: maximize (less negative is better).

### A. Sphere paper suite (15 seeds)

| Algorithm | Mean fitness | Std | Median | Mean seconds | Mean evals |
|-----------|-------------:|----:|-------:|-------------:|-----------:|
| standard_pso | −0.00022277 | 0.000293845 | −6.50474×10⁻⁵ | 0.0451932 | 312 |
| sapso | −0.000350268 | 0.000413311 | −0.000191076 | 0.0671088 | 312 |
| random_search | −0.135848 | 0.176789 | −0.0464136 | 0.0158034 | 300 |

Suite winner (mean fitness): **standard_pso**.

### B. Multi-landscape (12 seeds)

| Landscape | Algorithm | Mean fitness |
|-----------|-----------|-------------:|
| sphere | standard_pso | −0.000145599 |
| sphere | sapso | −0.000155578 |
| sphere | random_search | −0.126546 |
| rastrigin | standard_pso | −0.47678 |
| rastrigin | sapso | −0.701546 |
| rastrigin | random_search | −4.40123 |

### C. Budget ablation ranks

Identical rank order on Sphere and Rastrigin for both compact and extended budgets:

**standard_pso ≻ sapso ≻ random_search**

### D. Hypothesis outcomes

| ID | Statement | Outcome |
|----|-----------|---------|
| H1 | SAPSO ≥ PSO on Sphere | **Not supported** |
| H2 | SAPSO ≥ PSO on Rastrigin | **Not supported** |
| H3 | Swarm ≻ Random Search | **Supported** |
| H4 | Rank consistency | **Supported** |

### E. Reproducibility smoke

Standard PSO re-run means matched bit-exactly: −0.03588300969384031 (validation cell).  
`[PLACEHOLDER: full Wilcoxon p-values table — see suite statistics.json for pairwise payloads]`

### F. Instrumentation (descriptive)

SAPSO coefficient evolution and diversity curves generated under `artifacts/research/phase12a_campaign/figures/` (representative seed 42). Training time / inference cost / memory RSS: **null** in Phase 12A (not applicable to mock campaign).

Figures: see `paper/figures_list.md`. Tables: see `paper/tables_list.md`.

---

## IX. Discussion

Phase 12A supports the platform’s **evaluation integrity** claim more strongly than a “SAPSO always wins” claim. On smooth/multimodal 2D mock landscapes with paper-draft budgets, classical PSO was slightly better on mean fitness; adaptation overhead did not yield an advantage. Both swarm methods dominated Random Search by a large margin, validating budgeted search versus uninformed sampling. Rank stability across landscapes and budgets strengthens confidence in comparative ordering under this protocol.

These results **do not** imply SAPSO underperforms on high-dimensional discrete CNN spaces; that remains `[PLACEHOLDER: neural campaign]`. Wall-clock on mock fitness is dominated by Python overhead and should not be over-interpreted as GPU training cost.

---

## X. Threats to Validity

- **Internal:** Seed bases and budgets are researcher-chosen.
- **External:** Sphere/Rastrigin may not transfer to CNN NAS.
- **Construct:** Mock fitness is a proxy, not validation accuracy; training/inference metrics are null.
- **Conclusion:** Normal-approx CIs are descriptive; multiple pairwise tests risk family-wise error without correction `[PLACEHOLDER: apply Holm/Bonferroni in camera-ready]`.

---

## XI. Conclusion

EvoNAS provides a reproducible, governed AutoML/NAS platform with SAPSO as the production engine and fair research baselines. Phase 12A shows honest multi-seed evidence: swarm search beats Random Search; Standard PSO edged SAPSO on 2D mock controls; ranks were consistent. The contribution of this work at the present evidence level is the **integrated system plus rigorous evaluation practice**, not an unqualified claim of SAPSO superiority on all landscapes.

---

## XII. Future Work

1. Neural evaluation on `cnn_quick` / MNIST / CIFAR with frozen engines `[PLACEHOLDER]`.
2. Camera-ready seed counts (30–50) `[PLACEHOLDER]`.
3. Closed-loop drift→decision→search case studies with DecisionRecord timelines `[PLACEHOLDER]`.
4. Optional Grid Search baseline for discrete spaces (research package only).
5. Family-wise error correction and full Replay supplements for paper camera-ready.

---

## References

See [`references.bib`](references.bib). Entries marked `@misc{placeholder...}` must be replaced with verified bibliographic records before submission.

---

## Appendix Pointer

Extended tables, config hashes, artifact paths, and CLI reproduction commands: [`appendix.md`](appendix.md).
