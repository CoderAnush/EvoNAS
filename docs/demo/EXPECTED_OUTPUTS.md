# Expected Outputs

| Command | Expect |
|---|---|
| `evonas version` | `0.7.0` |
| `prepare-dataset` | schema + checksum lines; manifest under `artifacts/datasets/` |
| `optimize --dry-run` | `summary.json` with `best_fitness`, `run_dir`, plots optional |
| `compare-optimizers` | `winner` in {sapso, standard_pso, tie} |
| `simulate-loop` | `optimizations_used >= 1`, promotions list, `lifecycle_history.json` |
| `learn --cycles 2` | `results` length 2, `observation` mapping, `learning_history.json` |
| `detect-data` | `change_report.has_changes` true in simulation |

Failure is unexpected if configs above are used on a clean install with `[dev]`.
