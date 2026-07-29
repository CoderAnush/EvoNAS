# Statistical Tests (Planned)

| Comparison | Test | Notes |
|---|---|---|
| SAPSO vs PSO final fitness | Paired Wilcoxon / paired t if normal | Identical seeds |
| Evaluations-to-target | Mann–Whitney U | Unpaired if budgets differ |
| Multiple landscapes | Holm–Bonferroni correction | Control FWER |
| Phase occupancy differences | χ² / Fisher | Categorical phases |
| Drift detection significance | Already KS p-values from Phase 1 | Report thresholds |

**Reporting:** median ± IQR, win rates, effect sizes (Cliff’s Δ / Cohen’s d) — choose one and stay consistent.
