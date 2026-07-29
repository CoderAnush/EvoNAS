# Release Notes — v1.0.0-rc1

**EvoNAS Scientific Evaluation & Experimental Framework (Phase 10)**

## Highlights

- `ExperimentOrchestrator` — matrix execution, aggregation, exports
- Fair multi-seed benchmarks: Standard PSO · SAPSO · Random Search
- Statistical summaries + optional paired Wilcoxon + Cliff’s δ
- Publication figures (PNG/SVG/PDF) and tables (CSV/Markdown/LaTeX)
- Experiment registry with config/git/version/checksum metadata
- Auto-generated methodology/results/limitations reports
- CLI: `evonas benchmark`, `experiment`, `compare`, `report`

## Version

Package version: **`1.0.0rc1`** (tag: `v1.0.0-rc1`)

## Install / smoke

```bash
pip install -e ".[dev]"
evonas benchmark --config configs/benchmarks/default.yaml
evonas experiment list
```

## Integrity note

Results are reported honestly. If SAPSO does not win under a given configuration, the framework records that without bias.

## Not in this RC

Model registry, auth, cloud, IEEE manuscript drafting.
