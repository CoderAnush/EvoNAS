# CLI.md — EvoNAS Command Reference (v0.7.0)

```text
evonas version
evonas doctor
evonas prepare-dataset --config PATH
evonas train | train-baseline --config PATH
evonas build-model | inspect-model | validate-model --config PATH
evonas optimize --config PATH [--out DIR] [--dry-run] [--verbose]
evonas compare-optimizers --config PATH [--out DIR]
evonas run-loop --config PATH [--out DIR] [--dry-run] [--max-cycles N]
evonas simulate-loop --config PATH [--out DIR] [--max-cycles N]
evonas inspect-loop --run-dir DIR
evonas learn --config PATH [--out DIR] [--cycles N]
evonas detect-data --config PATH [--out DIR]
evonas replay-learning --history PATH [--out DIR]
```

## Notes

- `run` / `replay` print guidance to prefer `run-loop` / `simulate-loop` in Phase 6+.  
- Default configs are documented in `CONFIGURATION.md`.  
- Simulation / `--dry-run` uses mock fitness (no NN training).
