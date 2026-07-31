# Appendix — EvoNAS Publication Package (Phase 12B)

## A. Artifact directory map

```text
artifacts/research/
  phase12a_sphere_paper/
  phase12a_multi_landscape/
  phase12a_budget_compact/
  phase12a_budget_extended/
  phase12a_campaign/
    manifest.json
    hypothesis_status.json
    figures/
    tables/
    reports/
    instrumentation/
    validation/
  index.jsonl
```

## B. Config hashes (full)

From `phase12a_campaign/manifest.json`:

| Suite | SHA-256 |
|-------|---------|
| phase12a_sphere_paper | `a63013bb79cce74a0be5b79f76fd4bca859b6b37153e47ad642ef67249490897` |
| phase12a_multi_landscape | `e6d3225aef4354dc7baa9b1d10f27c03ed3e569943c62ec6308ff4b9d9881d96` |
| phase12a_budget_compact | `f22f25c402ef3af584b5adb3ff8626c712da062eaa03c979e2b6e5520bea2abc` |
| phase12a_budget_extended | `dca4782472e2fe51ec766ee6c66bb382a1b1ef812fce7384bf6489bb55cbb3c8` |

Git commit: `1f6848c65b18b5c4d12a0c49988c726ce5c9a389`  
EvoNAS version: `1.0.0rc2`

## C. Reproduction

```bash
git checkout 1f6848c65b18b5c4d12a0c49988c726ce5c9a389
pip install -e ".[dev,research]"
python scripts/run_phase12a_campaign.py
```

Single suite:

```bash
evonas benchmark --config configs/benchmarks/phase12a_sphere_paper.yaml
```

## D. Full campaign summary

See `artifacts/research/phase12a_campaign/tables/campaign_summary.md` (21 rows; authoritative).

## E. Hypothesis JSON

See `artifacts/research/phase12a_campaign/hypothesis_status.json`.

## F. Research reports (campaign)

- `reports/results_summary.md`
- `reports/discussion_notes.md`
- `reports/threats_to_validity.md`
- `reports/limitations.md`
- `reports/future_work.md`

## G. Placeholders inventory

| Topic | Status |
|-------|--------|
| MNIST/CIFAR accuracy | Not run |
| Neural train/inference timing | null |
| Closed-loop drift case study | Not run |
| Camera-ready 30–50 seeds | Not run |
| Multiplicity-corrected p-table | Not formatted |
| Author list / funding | Not filled |
| Final IEEE PDF styling | Not done |

## H. Software non-modification affidavit

Phase 12B generates documentation under `paper/` (and related docs). It does not modify PSO, SAPSO, trainers, closed-loop, dashboard, API, registry, or CLI source.
