# Conference Abstract — EvoNAS (Phase 12B Draft)

**Title:** EvoNAS: Fair Evaluation of Self-Adaptive PSO within an Autonomous Neural Architecture Search Platform

**Authors:** `[PLACEHOLDER: author list and affiliations]`

**Keywords:** Neural Architecture Search; Particle Swarm Optimization; Self-Adaptive PSO; AutoML; Reproducibility

## Abstract (≈200–250 words)

EvoNAS is an open Clean-Architecture platform for autonomous neural architecture search that combines Self-Adaptive Particle Swarm Optimization (SAPSO) with closed-loop decision policies, continuous-learning recommendations, and a metadata-only experiment/model registry. Beyond system design, scientific credibility requires fair, multi-seed comparisons that do not privilege the production optimizer. We report Phase 12A results from a pre-registered protocol comparing Standard PSO, SAPSO, and Random Search on Sphere and Rastrigin mock landscapes under matched evaluation budgets and identical seeds (paper-draft seed counts of 10–15). Across all suites, mean best-fitness ranks followed Standard PSO ≻ SAPSO ≻ Random Search. Swarm methods substantially outperformed Random Search, while SAPSO did not dominate Standard PSO on these 2D controls; negative SAPSO deltas are reported explicitly. A reproducibility smoke test confirmed bit-exact Standard PSO re-runs. Neural-image NAS campaigns and closed-loop drift case studies remain future work. The present contribution emphasizes an integrated, reproducible AutoML/NAS platform and honest evaluation practice rather than an unqualified claim of SAPSO superiority on synthetic landscapes.

**Word count:** ~180 (expand with venue-specific limits if needed)

**Preferred track:** `[PLACEHOLDER: AutoML / NAS / Evolutionary Computation / SE4AI]`

**Presentation preference:** Oral / Poster `[PLACEHOLDER]`
