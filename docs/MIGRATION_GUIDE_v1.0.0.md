# Migration Guide — → EvoNAS v1.0.0

## From `1.0.0rc2`

| Area | Action |
|------|--------|
| Package version | Reinstall / bump to `1.0.0` (`pip install -e .`) |
| CLI | Commands unchanged; `evonas version` prints `1.0.0` |
| Configs | Existing YAML under `configs/` remain valid |
| Artifacts | Prior `artifacts/` remain readable; re-sync registry if desired (`evonas registry sync`) |
| Research | Phase 12A artifacts remain authoritative; no need to re-run unless verifying |
| Docs | Prefer `docs/guides/*`, `docs/architecture/*`, `paper/`, `website/` |

## Breaking changes

**None intentionally introduced in Phase 12C** (docs/release packaging). Core PSO/SAPSO/training/closed-loop implementations were not modified for this release.

## Deprecated

- Treat `1.0.0-rc1` / `rc2` tags as pre-releases; cite **v1.0.0** going forward.

## From ≤ v0.9

Follow prior release notes for API/dashboard introduction, then land on v1.0.0. Expect new CLI groups: `benchmark`, `registry`, `models`, etc.
