# Visual Asset Specifications (Dashboard-Ready)

Placeholders for future dashboard / slides. Generate SVGs/PNGs later from these specs.

## V1 — System Architecture

Layers: Presentation → Application → Domain ← Ports ← Infrastructure.  
Highlight SAPSO inside domain/optimization.

## V2 — Closed-Loop Workflow

States: Idle→Monitoring→Decision→Optimizing→Training→Evaluation→Validation→Accepted|Rejected→Monitoring.

## V3 — SAPSO Flowchart

Swarm stats → AdaptiveController → (w,c1,c2) → Standard velocity update → Fitness → History.

## V4 — Dataset Lineage

Parent → training candidate → child versions with checksums.

## V5 — Optimization Pipeline

SearchSpace → Particles → Evaluate → Update → Stop → Best architecture.

## V6 — Lifecycle Timeline

Horizontal swimlane of DecisionRecords + promotions.

## V7 — State Machine Diagram

Use mermaid from `docs/phase_reports/phase6.md` as source of truth.

## Export Targets

| Asset | Suggested path |
|---|---|
| PNG/SVG | `docs/visual/exports/` (gitignored until curated) |
| Mermaid sources | phase reports + this file |
