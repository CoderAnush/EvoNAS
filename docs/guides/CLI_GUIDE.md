# CLI Guide — EvoNAS v1.0.0

Canonical command list: [`CLI.md`](../../CLI.md) (repo root).

## Everyday commands

| Goal | Command |
|------|---------|
| Version | `evonas version` |
| Health | `evonas doctor` / `evonas status` |
| Mock optimize | `evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run` |
| Compare PSO vs SAPSO | `evonas compare-optimizers --config configs/optimization/pso_vs_sapso.yaml` |
| Simulate closed loop | `evonas simulate-loop --config configs/closed_loop/simulate.yaml` |
| Continuous learning | `evonas learn --config configs/continuous_learning/default.yaml` |
| Benchmark suite | `evonas benchmark --config configs/benchmarks/default.yaml` |
| Research report | `evonas report --run-dir artifacts/research/<id>` |
| Registry | `evonas registry sync` · `evonas registry overview` |
| API + dashboard | `evonas serve --demo` |

## Tips

- Prefer `--dry-run` / mock configs for demos and CI.
- Research fairness: use `configs/benchmarks/*.yaml` (matched budgets).
- Governance never rewrites result files; sync is metadata-only.
