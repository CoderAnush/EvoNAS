# EvoNAS — Action Plan After Phase 7

**Date:** 2026-07-30

---

## Step 1 — Freeze v0.7.0

- [x] Validate pytest / ruff / mypy  
- [x] E2E CLI smoke  
- [x] RC1 documentation package  
- [ ] Commit Phase 7 + RC1 docs  
- [ ] Annotated tag `v0.7.0`

## Step 2 — Push

- [ ] `git push origin main`  
- [ ] `git push origin v0.7.0`  
- [ ] Optional GitHub Release from RC1 notes  

## Step 3 — Dashboard (Phase 9 track; may follow deploy)

- Streamlit run / replay / metrics / policies  
- Consume frozen artifacts — do not rewrite engines  

## Step 4 — Deployment (Phase 8)

- Localhost staging / promote / LKG  
- Rollback path  
- Docker target  
- Wire `should_deploy` / `should_rollback` for real  

## Step 5 — Research

- Execute `docs/research/EXPERIMENT_PLAN.md`  
- PSO vs SAPSO ablations on agreed datasets  
- Statistical tests + figures  

## Step 6 — Publication

- IEEE-oriented paper from `docs/research/PAPER_OUTLINE.md`  
- Cite reproducible artifact manifests / Replay Mode  

---

## Ordering Rule

**Do not start Phase 8 implementation until Step 2 (push) completes**, unless explicitly overridden by the project owner.
