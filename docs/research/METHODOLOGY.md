# Experimental Methodology

See also: [`protocol.md`](protocol.md), [`STATISTICAL_TESTS.md`](STATISTICAL_TESTS.md), [`METRICS.md`](METRICS.md).

## Design

EvoNAS Phase 10 separates **algorithm implementation** from **evaluation infrastructure**.

- Production engines (PSO, SAPSO, trainers, closed loop) are treated as black boxes.
- The orchestrator only calls `ISearchAlgorithm` + shared `BenchmarkRunner`.
- Baselines for papers live in `evonas.benchmarks` and are never DI-wired into the controller.

## Metrics collected per run

Best fitness, iterations, evaluations, wall-clock seconds, stop reason. Aggregates across seeds: mean/median/std/best/worst. Optional pairwise significance and effect sizes.

## Reporting policy

Declare a winner only by mean fitness under the configured maximize/minimize sense. Ties are reported as `tie`. Negative or null SAPSO deltas are preserved in artifacts.
