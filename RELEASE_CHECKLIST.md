# RELEASE_CHECKLIST.md — EvoNAS v0.7.0 RC1

## Repository

- [x] idea.md present (authority)  
- [x] LICENSE (MIT)  
- [x] README badges/version aligned to 0.7.0  
- [x] CHANGELOG includes v0.7.0  
- [x] .gitignore excludes artifacts/caches  
- [ ] CONTRIBUTING.md present (added in RC1)  
- [ ] GitHub issue/PR templates present (added in RC1)

## Testing

- [x] pytest green (117)  
- [x] ruff green  
- [x] mypy green  
- [x] E2E CLI smoke green  

## Documentation

- [x] Phase reports 1–7  
- [x] RC1 reports under `docs/rc1/`  
- [x] Demo package `docs/demo/`  
- [x] Research package `docs/research/`  
- [x] Developer / CLI / configuration guides  

## Version

- [x] `pyproject.toml` = 0.7.0  
- [x] `evonas.__version__` = 0.7.0  

## Artifacts

- [x] Smoke artifacts reproducible under `artifacts/` (gitignored)  
- [x] Summaries / histories / lineage generated  

## Demo / Research

- [x] Demo script &lt; 10 minutes  
- [x] Research experiment plan (no runs required for RC1)

## Git

- [ ] Commit Phase 7 + RC1 package  
- [ ] Tag `v0.7.0`  
- [ ] Push `main` + tag  
- [ ] Optional GitHub Release notes from `docs/rc1/RELEASE_NOTES_RC1.md`

## Phase 8 Gate

- [ ] Only after push + tag: begin Deployment Manager
