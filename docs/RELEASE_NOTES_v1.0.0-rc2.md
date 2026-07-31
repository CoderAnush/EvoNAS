# Release Notes — v1.0.0-rc2

**EvoNAS AI Governance, Registry & Lifecycle (Phase 11)**

## Highlights

- File-backed governance registry under `artifacts/registry/`
- Model stages (`none` / `staging` / `production` / `archived`) with single-production invariant + LKG metadata snapshot
- Experiment / dataset / artifact indexes with checksums and environment stamps
- Configurable lifecycle transitions + Mermaid graphs
- Lineage traversal and search
- Promotion / rollback **metadata only** (no live deployment mutation)
- CLI: `registry`, `models`, `experiments`, `lineage`, `artifacts`
- Additive API + dashboard pages

## Version

Package: **`1.0.0rc2`** · Tag: **`v1.0.0-rc2`**

## Integrity

The registry records and indexes metadata. It does not rewrite fitness, metrics, or training outcomes.
