# Repository Statistics — EvoNAS v1.0.0

Generated as part of Phase 12C release packaging. Re-run commands below to refresh.

## Commands

```bash
git rev-parse HEAD
git describe --tags --always
git ls-files | Measure-Object -Line   # or: git ls-files | wc -l
Get-ChildItem -Recurse src -Filter *.py | Measure-Object
Get-ChildItem -Recurse tests -Filter *.py | Measure-Object
```

## Snapshot (fill at tag time)

| Metric | Value |
|--------|-------|
| Tag | `v1.0.0` |
| Package version | `1.0.0` |
| Tracked files (approx at packaging) | 341+ |
| `src/evonas` Python modules | 188 |
| `test_*.py` files | 32 |
| Quality gates | ruff ✅ · mypy 188 files ✅ · pytest 150 passed |
| License | MIT |
| Website | `website/index.html` |
| Citation | `CITATION.cff` |
| Publication | `paper/` |
| Reproducibility | `reproducibility/` |

## Quality gates

| Gate | Expected |
|------|----------|
| pytest | pass |
| ruff | pass |
| mypy | pass on `src` |

## Scientific artifacts

Phase 12A suites under `artifacts/research/phase12a_*` (may be local-only; not required in git).
