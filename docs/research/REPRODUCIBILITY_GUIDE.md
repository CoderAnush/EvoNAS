# Reproducibility Guide

## What is recorded

| Field | Source |
|-------|--------|
| `evonas_version` | package |
| `git_commit` | `git rev-parse HEAD` |
| `config_hash` | SHA-256 of suite YAML |
| `checksums.json` | SHA-256 of key result files |
| `seeds` | explicit list |
| `python` / `platform` | runtime |

## How to reproduce

1. Check out the recorded git commit.
2. Install the recorded package version.
3. Re-run the same YAML (`config_hash` must match).
4. Compare `results.json` means (mock fitness should match bit-for-bit for identical seeds).

## Replay vs re-optimize

- **Report / dashboard** read artifacts only (no retrain).
- **Benchmark** re-executes search with frozen configs — use for verification, not for mutating history.
