# Experimental Protocol (Phase 10)

This document operationalizes `REQ-RES-010` for EvoNAS scientific runs.

## Fairness rules

1. Identical search space YAML across methods in a cell.
2. Identical evaluation budget (PSO: swarm_size × iterations; Random Search: `n_trials`).
3. Identical seed list for paired comparisons.
4. Mock fitness landscapes for CI / Quick Mode; neural eval only when explicitly configured later.
5. Resolved configs copied into the run directory; SHA-256 recorded.

## Recommended seed counts

| Mode | Seeds |
|------|------:|
| Smoke / CI | 3–5 |
| Paper draft | 10–20 |
| Camera-ready | 30–50 |

Configure via:

```yaml
seeds:
  n: 20
  base: 42
```

## Statistics

- Descriptive: mean, median, variance, std, min/max
- CI: normal approximation `mean ± z·s/√n` (documented; not a normality claim)
- Optional: paired Wilcoxon signed-rank (SciPy), Cliff’s δ effect size

## Artifacts

```text
artifacts/research/{experiment_id}/
  meta.json
  config.resolved.yaml
  results.json
  statistics.json
  comparison.json
  checksums.json
  tables/
  figures/
  reports/experiment_report.md
```

## Isolation

`evonas.benchmarks.RandomSearch` is for research only and is never the closed-loop production optimizer (SAPSO remains exclusive in the controller).
