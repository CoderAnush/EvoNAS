# Research Benchmarks

## Optimization Benchmarks

| Benchmark | Type | Purpose |
|---|---|---|
| Sphere | Synthetic maximize (neg distance) | Unit / smoke |
| Rastrigin | Synthetic multimodal | Exploration stress |
| CNN Quick search space | Architecture NAS | Application fidelity |
| PSO vs SAPSO comparison harness | Paired seeds | Primary algorithmic claim |

## System Benchmarks

| Benchmark | Metric |
|---|---|
| Quick Mode closed loop | Wall-clock &lt; 10 min (idea.md) |
| Decision audit completeness | Every YES/NO has DecisionRecord |
| CL recommendation purity | No direct optimize calls from CL |

## Non-Goals for First Paper

Cloud latency, multi-tenant scheduling, AutoML platform bake-offs beyond stated baselines.
