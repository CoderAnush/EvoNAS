# Figure Guide

Publication figures are written by `PublicationFigures` to `figures/` inside each research run.

## Default exports

| Stem | Content | Formats |
|------|---------|---------|
| `fitness_convergence` | Per-seed best fitness series | PNG, SVG, PDF |
| `accuracy_fitness_comparison` | Mean ± std bar chart | PNG, SVG, PDF |
| `runtime_comparison` | Mean wall-clock bars | PNG, SVG, PDF |
| `coefficient_evolution` | Optional SAPSO w/c1/c2 | PNG, SVG, PDF |
| `diversity_evolution` | Optional diversity | PNG, SVG, PDF |

## Style

- Matplotlib Agg backend
- ~6.4×4.0 in, 200 DPI
- White-grid style when available

## Interactive

Dashboard Plotly charts remain the interactive surface; Phase 10 figures are for papers/PDF supplements and do not duplicate dashboard rendering code.
