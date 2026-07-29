# Research Experiment Plan (Planning Only — No Runs)

**Status:** Planning for post-RC1 research  
**Version baseline:** v0.7.0

## Goals

1. Quantify SAPSO vs Standard PSO under identical seeds.  
2. Measure closed-loop decision quality under synthetic drift.  
3. Demonstrate continuous-learning recommendations preceding authorized search.

## Experiment Matrix (planned)

| ID | Question | Config family | Seeds |
|---|---|---|---|
| E1 | SAPSO vs PSO on Sphere / Rastrigin | `configs/pso/*_mock.yaml` | 10+ |
| E2 | SAPSO vs PSO on CNN Quick search space | `configs/optimization/*` + toy/MNIST subset | 5+ |
| E3 | Ablation fixed vs adaptive coefficients | `sapso_ablation_fixed.yaml` | 10+ |
| E4 | Drift → CL recommend → DecisionEngine YES rate | CL + closed_loop simulate | 5+ |
| E5 | Warm-start continuous cycles | future Research Mode | TBD |

## Protocol Notes

- Fix seeds; log `config_hash`; export histories.  
- Do not change adaptive equations mid-study without a new version tag.  
- Use Replay Mode for paper reproducibility once wired end-to-end.
