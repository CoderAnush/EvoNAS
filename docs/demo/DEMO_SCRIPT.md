# Demo Script — EvoNAS in Under 10 Minutes

**Audience:** Professor / research mentor  
**Mode:** Simulation / mock fitness (no GPU required)  
**Version:** v0.7.0 RC1

---

## Timing Budget (~9 minutes)

| Min | Segment |
|---:|---|
| 0:00–1:00 | Vision: autonomous lifecycle, not “just NAS” |
| 1:00–2:00 | Install check `evonas doctor` |
| 2:00–3:30 | Dataset prepare (toy) |
| 3:30–5:00 | Standard PSO vs SAPSO (mock) |
| 5:00–7:00 | Closed-loop simulate (accept/reject) |
| 7:00–8:30 | Continuous learning recommend-only |
| 8:30–9:30 | Artifacts + reproducibility talking points |
| 9:30–10:00 | Roadmap to Phase 8 / paper |

---

## Exact Commands

```bash
pip install -e ".[dev]"
evonas doctor
evonas prepare-dataset --config configs/datasets/toy_quick.yaml
evonas optimize --config configs/pso/mock_sphere.yaml --dry-run --out artifacts/demo/pso
evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run --out artifacts/demo/sapso
evonas compare-optimizers --config configs/optimization/pso_vs_sapso.yaml --out artifacts/demo/cmp
evonas simulate-loop --config configs/closed_loop/simulate.yaml --out artifacts/demo/loop --max-cycles 1
evonas learn --config configs/continuous_learning/default.yaml --out artifacts/demo/cl --cycles 2
```

Open `summary.json` / `lifecycle_history.json` / `learning_history.json` while speaking.
