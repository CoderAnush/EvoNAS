# CONFIGURATION.md

## Principles

- YAML is the operator interface  
- Prefer existing defaults for demos  
- Hashes of resolved configs are stored in artifacts for reproducibility  

## Map

| Goal | Config |
|---|---|
| Toy data | `configs/datasets/toy_quick.yaml` |
| Baseline train | `configs/training/baseline.yaml` |
| Standard PSO mock | `configs/pso/mock_sphere.yaml` |
| SAPSO mock | `configs/pso/adaptive_mock.yaml` |
| Compare engines | `configs/optimization/pso_vs_sapso.yaml` |
| Closed loop | `configs/closed_loop/default.yaml` |
| Closed loop simulate | `configs/closed_loop/simulate.yaml` |
| Decision policy | `configs/policies/default_policy.yaml` |
| Continuous learning | `configs/continuous_learning/default.yaml` |
| CL alias | `configs/continuous/default.yaml` |

## Algorithm Selection

```yaml
optimization:
  algorithm: sapso  # or pso
```

## Continuous Learning Keys

Engine accepts top-level `continuous_learning:` **or** `continuous:`.
