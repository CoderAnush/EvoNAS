# EvoNAS Thesis Report (Phase 12B Draft)

**Title:** Autonomous Closed-Loop Neural Architecture Search with Self-Adaptive Particle Swarm Optimization: Design, Implementation, and Experimental Validation of EvoNAS  
**Software baseline:** `v1.0.0-rc2`  
**Empirical chapter data:** Phase 12A only  
**Document type:** Thesis-oriented narrative (documentation package)

---

## Chapter 1 — Introduction

### 1.1 Motivation

Modern ML systems degrade under distribution shift and evolving requirements. One-shot NAS does not by itself provide continuous redesign with audit and rollback. EvoNAS targets **policy-governed continuous architecture evolution**.

### 1.2 Problem statement

Design and validate an open platform that (i) searches architectures with SAPSO, (ii) decides under closed-loop policies, (iii) records reproducible artifacts, and (iv) reports optimizer comparisons without favoritism.

### 1.3 Objectives

1. Implement Clean-Architecture AutoML/NAS stack through governance (Phases 0–11).
2. Define and execute a fair experimental protocol (Phase 12A).
3. Produce a publication package with honest results (Phase 12B).

### 1.4 Research questions

Identical to Phase 12A RQ1–RQ4 (see `docs/research/experimental_protocol.md`).

### 1.5 Thesis contributions

System contribution (architecture + lifecycle) and methodological contribution (fair multi-seed campaign with registry). Empirical chapter does **not** claim SAPSO superiority on Phase 12A mock landscapes.

### 1.6 Organization

Ch.2 related work; Ch.3 architecture; Ch.4 SAPSO; Ch.5 closed loop & CL; Ch.6 experiments; Ch.7 results; Ch.8 discussion; Ch.9 conclusion.

---

## Chapter 2 — Related Work

Summarize NAS, adaptive PSO, MLOps/closed-loop AutoML, and reproducibility standards. Full citations: `paper/references.bib` (many placeholders pending librarian pass).

---

## Chapter 3 — System Architecture

Layers: domain / application / infrastructure / presentation / ports. Isolation of `benchmarks/` from production DI. Artifact layout under `artifacts/`. Dashboard and API are additive operational surfaces (Phases 8–9). Registry is metadata-only (Phase 11).

`[PLACEHOLDER: thesis figure — clean architecture diagram]`

---

## Chapter 4 — Self-Adaptive PSO

Classical velocity update; adaptive \((w,c_1,c_2)\); diversity and improvement statistics; phase machine. Determinism via seeds. Instrumentation figures: `artifacts/research/phase12a_campaign/figures/coefficient_evolution.*`, `diversity_evolution.*`.

---

## Chapter 5 — Closed Loop and Continuous Learning

DecisionEngine gates; DecisionRecords; CL recommendations ≠ authorization.  
**Empirical note:** Phase 12A did not measure closed-loop YES rates under drift. `[PLACEHOLDER: Ch.5 empirical subsection]`

---

## Chapter 6 — Experimental Methodology

Protocol binding: `docs/research/experimental_protocol.md`. Suites, seeds, budgets, metrics, and fairness rules as in Phase 12A. Neural metrics (accuracy, train time, inference) recorded as null for mock campaign.

---

## Chapter 7 — Results

### 7.1 Headline

| Hypothesis | Result (Phase 12A) |
|------------|--------------------|
| H1 SAPSO ≥ PSO (Sphere) | Not supported |
| H2 SAPSO ≥ PSO (Rastrigin) | Not supported |
| H3 Swarm ≻ RS | Supported |
| H4 Rank consistency | Supported |

### 7.2 Sphere paper means (15 seeds)

- PSO: −0.00022277 ± 0.000293845  
- SAPSO: −0.000350268 ± 0.000413311  
- RS: −0.135848 ± 0.176789  

### 7.3 Multi-landscape and budget suites

See `artifacts/research/phase12a_campaign/tables/campaign_summary.md` (authoritative). Rank order always **PSO > SAPSO > RS**.

### 7.4 Reproducibility

Bit-exact PSO validation re-run: **true** (manifest validation block).

### 7.5 Unavailable metrics

Training time, inference cost, neural accuracy, memory RSS: `[PLACEHOLDER / null in Phase 12A]`.

---

## Chapter 8 — Discussion and Threats

Honest interpretation: platform integrity demonstrated; SAPSO advantage not shown on 2D mocks; external validity to CNN NAS unproven. Threats: internal/external/construct/conclusion (see manuscript §X).

---

## Chapter 9 — Conclusion and Future Work

EvoNAS delivers an integrated, reproducible autonomous NAS platform. Future: neural campaigns, larger seeds, closed-loop case studies, camera-ready statistics corrections.

---

## Thesis Appendix

Config hashes, CLI commands, full tables: `paper/appendix.md`.
