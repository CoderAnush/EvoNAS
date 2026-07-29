# Demo CLI Commands (Copy-Paste)

```bash
# Environment
pip install -e ".[dev]"
evonas version
evonas doctor

# Data
evonas prepare-dataset --config configs/datasets/toy_quick.yaml

# Optimization (mock)
evonas optimize --config configs/pso/mock_sphere.yaml --dry-run --out artifacts/demo/pso
evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run --out artifacts/demo/sapso
evonas compare-optimizers --config configs/optimization/pso_vs_sapso.yaml --out artifacts/demo/cmp

# Closed loop
evonas simulate-loop --config configs/closed_loop/simulate.yaml --out artifacts/demo/loop --max-cycles 1
evonas inspect-loop --run-dir artifacts/demo/loop/closed_loop_simulate

# Continuous learning
evonas learn --config configs/continuous_learning/default.yaml --out artifacts/demo/cl --cycles 2
evonas detect-data --config configs/continuous_learning/default.yaml --out artifacts/demo/detect
evonas replay-learning --history artifacts/demo/cl/run/learning_history.json --out artifacts/demo/replay
```

**Estimated demo time:** 8–10 minutes speaking + commands.
