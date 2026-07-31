# Benchmark Guide

## Quick start

```bash
pip install -e ".[dev]"
evonas benchmark --config configs/benchmarks/default.yaml
```

Outputs land in `artifacts/research/<experiment_id>/`.

## Suite configs

| Config | Purpose |
|--------|---------|
| `configs/benchmarks/default.yaml` | Sphere · PSO/SAPSO/Random · 5 seeds |
| `configs/benchmarks/multi_landscape.yaml` | Sphere + Rastrigin |
| `configs/benchmarks/phase12a_*.yaml` | Phase 12A paper-draft / multi-landscape / budget suites |
| `configs/optimization/pso_vs_sapso.yaml` | Legacy PSO vs SAPSO only |

### Phase 12A campaign

```bash
python scripts/run_phase12a_campaign.py
```

Protocol: `docs/research/experimental_protocol.md`. Outputs: `artifacts/research/phase12a_*`.

## CLI map

| Command | Role |
|---------|------|
| `evonas benchmark` | Full scientific suite |
| `evonas compare` | Legacy compare or `--suite` mode |
| `evonas compare-optimizers` | Original Phase 5 helper |
| `evonas experiment list/show` | Registry queries |
| `evonas report --run-dir` | Regenerate markdown report |

## Dashboard

Research runs write `comparison.json`. The existing Benchmarks page discovers them under `artifacts/research/` (no duplicate Plotly logic).
