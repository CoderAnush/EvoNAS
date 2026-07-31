# Release Notes — EvoNAS v1.0.0

**Tag:** `v1.0.0`  
**Date:** 2026-07-31  
**Codename:** Open Source Release (Phase 12C)

## Highlights

EvoNAS **1.0.0** is the first stable open-source release of the autonomous closed-loop AutoML/NAS platform:

- Self-Adaptive PSO production search engine + Standard PSO ablation
- Closed-loop controller & continuous-learning recommendations
- FastAPI platform + Streamlit operations dashboard
- Fair research benchmarking (PSO / SAPSO / Random Search)
- Metadata governance registry (stages, lineage, promotion ledgers)
- Phase 12A experimental evidence + Phase 12B publication package
- Architecture book, website, demo & reproducibility packages

## What 1.0.0 is

A **lab-ready / research-ready** platform with reproducible mock campaigns and full documentation for GitHub, thesis, IEEE drafts, and demos.

## What 1.0.0 is not

- Not a multi-tenant cloud AutoML service
- Not authenticated by default
- Not a claim that SAPSO wins all landscapes (Phase 12A: PSO edged SAPSO on 2D mocks)
- Not a completed neural MNIST/CIFAR paper campaign

## Upgrade from 1.0.0-rc2

See [`MIGRATION_GUIDE_v1.0.0.md`](MIGRATION_GUIDE_v1.0.0.md). Primarily a version + packaging/docs release; core engines unchanged in Phase 12C.

## Quality gates (release)

Run at tag time: `pytest`, `ruff`, `mypy` (see phase 12C report).

## Cite

Use root [`CITATION.cff`](../CITATION.cff).
