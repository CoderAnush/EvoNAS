# Configuration Guide — EvoNAS v1.0.0

Root index: [`CONFIGURATION.md`](../../CONFIGURATION.md) (if present) and `configs/`.

## Layout

```text
configs/
  default.yaml
  modes/          # research | quick | replay
  datasets/
  search_spaces/
  pso/            # standard + adaptive (+ mock)
  optimization/   # comparisons / ablations
  closed_loop/
  continuous_learning/
  benchmarks/     # Phase 10 / 12A suites
  registry/
  api/
  deploy/
```

## Principles

1. YAML is the source of truth for runs; resolved copies land in artifact dirs.
2. Mock fitness configs are preferred for CI/demos.
3. Benchmark suites declare algorithms, datasets, seeds, and matched RS trials.
4. Registry config controls metadata roots — never mutates science files.
5. Record `config_hash` from suite `meta.json` when citing results.

## Examples

| Use | Config |
|-----|--------|
| Mock SAPSO | `configs/pso/adaptive_mock.yaml` |
| PSO vs SAPSO | `configs/optimization/pso_vs_sapso.yaml` |
| Research suite | `configs/benchmarks/default.yaml` |
| Phase 12A paper suite | `configs/benchmarks/phase12a_sphere_paper.yaml` |
| Simulate loop | `configs/closed_loop/simulate.yaml` |
| Registry | `configs/registry/registry.yaml` |
