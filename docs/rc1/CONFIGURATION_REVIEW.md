# Configuration Review (RC1)

## Inventory

| Directory | Purpose |
|---|---|
| `configs/datasets/` | Phase 1 datasets |
| `configs/training/`, `configs/models/` | Phase 2–3 |
| `configs/search_spaces/`, `configs/pso/`, `configs/optimization/` | Phase 4–5 |
| `configs/closed_loop/`, `configs/policies/` | Phase 6 |
| `configs/continuous_learning/` | Phase 7 canonical |
| `configs/continuous/` | Phase 7 alias (idea.md path) |
| `configs/modes/` | Mode stubs (quick/research/replay) |

## Validation

- Defaults are simulation/mock-friendly for demos  
- Naming is snake_case YAML throughout  
- Dual CL configs documented with header comments  
- No secrets in YAML  

## Consistency Notes

1. Prefer `configs/continuous_learning/default.yaml` in docs/CLI defaults.  
2. Closed-loop policy may reference `configs/policies/default_policy.yaml`.  
3. Optimizer algorithm selected via `optimization.algorithm: pso|sapso`.  

## Non-Goals

No schema hard-fail framework beyond existing `ConfigurationManager` / domain validation — adequate for RC1.
