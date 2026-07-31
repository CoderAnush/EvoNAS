# Tables List — EvoNAS Publication Package (Phase 12B)

Authoritative numeric tables are in Phase 12A artifacts. Paper drafts should cite these paths.

---

## Generated tables (Phase 12A)

| ID | Title | Path |
|----|-------|------|
| Table I | Sphere paper summary | `artifacts/research/phase12a_sphere_paper/tables/summary.{csv,md,tex}` |
| Table II | Multi-landscape summary | `artifacts/research/phase12a_multi_landscape/tables/summary.*` |
| Table III | Compact budget summary | `artifacts/research/phase12a_budget_compact/tables/summary.*` |
| Table IV | Extended budget summary | `artifacts/research/phase12a_budget_extended/tables/summary.*` |
| Table V | Campaign summary (all suites) | `artifacts/research/phase12a_campaign/tables/campaign_summary.*` |
| Table VI | Rank tables | `artifacts/research/phase12a_campaign/tables/rank_tables.*` |
| Table VII | Full metrics (incl. null fields) | `artifacts/research/phase12a_campaign/tables/metrics_full.*` |
| Table VIII | Pairwise stats rollup | `artifacts/research/phase12a_campaign/tables/pairwise_stats.*` |
| Table IX | Architecture complexity proxy | `artifacts/research/phase12a_campaign/tables/architecture_complexity.*` |
| Table X | Gene bounds | `artifacts/research/phase12a_campaign/tables/gene_bounds.*` |

LaTeX snippets are already emitted as `.tex` beside CSV/MD.

---

## Planned paper tables (editorial)

| ID | Content | Data source |
|----|---------|-------------|
| Table A | Hyperparameters (swarm, w/c, seeds) | Suite YAMLs + protocol |
| Table B | Hypothesis outcomes | `hypothesis_status.json` |
| Table C | Config hashes | `manifest.json` |
| Table D | Neural results | `[PLACEHOLDER]` |
| Table E | Closed-loop decision rates | `[PLACEHOLDER]` |
| Table F | Multiplicity-corrected p-values | `[PLACEHOLDER: derive from statistics.json]` |

---

## Copy rule

When pasting into the manuscript, round for readability in prose but keep full precision in appendix or supplementary CSV.
