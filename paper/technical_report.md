# EvoNAS Technical Report — Phase 12B

**TR-EvoNAS-12B**  
**Audience:** Engineers, reviewers, reproducibility auditors  
**Evidence:** Phase 12A artifacts only  
**Software:** `v1.0.0-rc2` (frozen for campaign)

---

## 1. Scope

This technical report documents (a) how Phase 12A was executed, (b) exact numeric outcomes, (c) artifact layout, and (d) how to reproduce. It does not modify software.

---

## 2. Campaign inventory

| Experiment ID | Config | Config hash (SHA-256 prefix) | Winner |
|---------------|--------|------------------------------|--------|
| phase12a_sphere_paper | configs/benchmarks/phase12a_sphere_paper.yaml | a63013bb… | standard_pso |
| phase12a_multi_landscape | configs/benchmarks/phase12a_multi_landscape.yaml | e6d3225a… | standard_pso |
| phase12a_budget_compact | configs/benchmarks/phase12a_budget_compact.yaml | f22f25c4… | standard_pso |
| phase12a_budget_extended | configs/benchmarks/phase12a_budget_extended.yaml | dca47824… | standard_pso |

Full hashes: `artifacts/research/phase12a_campaign/manifest.json`.  
Git commit at run: `1f6848c65b18b5c4d12a0c49988c726ce5c9a389`.

---

## 3. Reproduction commands

```bash
# Requires installed EvoNAS v1.0.0rc2 at recorded commit
python scripts/run_phase12a_campaign.py

# Or single suite
evonas benchmark --config configs/benchmarks/phase12a_sphere_paper.yaml
```

Expected outputs under `artifacts/research/<experiment_id>/`:
`meta.json`, `results.json`, `statistics.json`, `comparison.json`, `checksums.json`, `tables/`, `figures/`, `reports/`.

---

## 4. Metric dictionary

| Field | Phase 12A status |
|-------|------------------|
| best fitness | Recorded |
| accuracy proxy | = fitness (mock) |
| optimization seconds | Recorded |
| evaluations | Recorded |
| model complexity | Proxy dim=2 |
| training time | null |
| inference cost | null |
| memory RSS | null (Windows) |

---

## 5. Results tables (authoritative excerpts)

### 5.1 Sphere paper

| Algo | mean | std | median | sec | evals | n |
|------|-----:|----:|-------:|----:|------:|--:|
| standard_pso | −2.2277e-4 | 2.93845e-4 | −6.50474e-5 | 0.04519 | 312 | 15 |
| sapso | −3.50268e-4 | 4.13311e-4 | −1.91076e-4 | 0.06711 | 312 | 15 |
| random_search | −0.135848 | 0.176789 | −0.0464136 | 0.01580 | 300 | 15 |

### 5.2 Multi-landscape means

| Landscape | PSO | SAPSO | RS |
|-----------|----:|------:|---:|
| sphere | −1.45599e-4 | −1.55578e-4 | −0.126546 |
| rastrigin | −0.47678 | −0.701546 | −4.40123 |

### 5.3 Compact vs extended (Sphere means)

| Budget | PSO | SAPSO | RS |
|--------|----:|------:|---:|
| compact (8×15) | −0.00304017 | −0.0104378 | −0.188763 |
| extended (16×40) | −2.20151e-6 | −7.37294e-5 | −0.042989 |

Ranks identical in all cells: PSO > SAPSO > RS.

---

## 6. Statistical artifacts

Per-suite `statistics.json` contains summaries and pairwise Wilcoxon / Cliff’s δ payloads when available. Campaign rollup: `phase12a_campaign/tables/pairwise_stats.*`.

`[PLACEHOLDER: camera-ready formatted significance table with multiplicity correction]`

---

## 7. Figures generated

Suite-level: fitness comparison, runtime comparison, per-seed series.  
Campaign-level: coefficient evolution, diversity (SAPSO), diversity (PSO copy).  
Paths listed in `paper/figures_list.md`.

---

## 8. Registry

Phase 10 research index + Phase 11 governance sync recorded experiments/artifacts as metadata (manifest `governance_sync` block). Results files were not rewritten.

---

## 9. Limitations (technical)

Mock-only; 2D space; paper-draft seeds; no neural training; RSS unavailable on this host; orchestrator suite “winner” aggregates across cells by mean fitness (multi-landscape winner reflects best cell).

---

## 10. Change control

Phase 12B adds documentation under `paper/` only. No source changes authorized by this report.
