# CLI.md — EvoNAS Command Reference (v1.0.0-rc1)

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
evonas dashboard [--demo] [--port 8501] [--headless]
evonas api [--host HOST] [--port PORT] [--reload] [--config PATH]
evonas serve [--api-port N] [--dashboard-port N] [--demo] [--headless] [--api-only]
evonas status [--api-url URL]
evonas learn --config PATH [--out DIR] [--cycles N]
evonas detect-data --config PATH [--out DIR]
evonas replay-learning --history PATH [--out DIR]
evonas benchmark --config PATH [--out DIR] [--dry-run]
evonas experiment list [--limit N]
evonas experiment show EXPERIMENT_ID
evonas compare --config PATH [--out DIR] [--suite]
evonas report --run-dir DIR [--out PATH]
```

## Notes

- `run` / `replay` print guidance to prefer `run-loop` / `simulate-loop` in Phase 6+.  
- Default configs are documented in `CONFIGURATION.md`.  
- Simulation / `--dry-run` uses mock fitness (no NN training).
- Dashboard requires the API (`EVONAS_API_URL`); prefer `evonas serve --demo`.
- Phase 10 research suite: `configs/benchmarks/default.yaml`.
- Extras: `pip install -e ".[api,dashboard,dev]"`.
