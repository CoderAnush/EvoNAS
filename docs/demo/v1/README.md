# Demo Package — EvoNAS v1.0.0

Index for conference / portfolio demos. Core engines are unchanged.

| Asset | Path |
|-------|------|
| Demo flow | [`DEMO_FLOW.md`](DEMO_FLOW.md) |
| Recording script | [`RECORDING_SCRIPT.md`](RECORDING_SCRIPT.md) |
| Screenshots checklist | [`SCREENSHOTS.md`](SCREENSHOTS.md) |
| Talking points | [`../../docs/demo/TALKING_POINTS.md`](../../docs/demo/TALKING_POINTS.md) |
| CLI cheat sheet | [`../../docs/demo/CLI_COMMANDS.md`](../../docs/demo/CLI_COMMANDS.md) |

## Recommended live path (8–12 min)

1. `evonas version` → show **1.0.0**
2. `evonas doctor`
3. Mock SAPSO optimize (dry-run)
4. `evonas simulate-loop` — decision records
5. `evonas benchmark --config configs/benchmarks/default.yaml`
6. Open `artifacts/research/*/figures/`
7. `evonas serve --demo` — dashboard overview + benchmarks page
8. Integrity beat: Phase 12A did **not** crown SAPSO on 2D mocks
