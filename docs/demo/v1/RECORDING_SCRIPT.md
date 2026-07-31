# Recording Script — EvoNAS v1.0.0 Demo Video

**Target length:** 6–8 minutes  
**Resolution:** 1920×1080 · terminal + browser

## Cold open (0:00–0:20)

VO: “EvoNAS is an autonomous AutoML platform — an AI system that continuously improves another AI.”

On screen: `website/index.html` or README hero.

## Setup (0:20–0:50)

```bash
evonas version
# 1.0.0
evonas doctor
```

## Optimize (0:50–2:00)

```bash
evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run
```

VO: “Self-Adaptive PSO adjusts coefficients while searching — production engine of the closed loop.”

## Closed loop (2:00–3:20)

```bash
evonas simulate-loop --config configs/closed_loop/simulate.yaml --max-cycles 3
```

Show DecisionRecords / run dir briefly.

## Research fairness (3:20–5:00)

```bash
evonas benchmark --config configs/benchmarks/default.yaml
```

Open fitness comparison figure. VO: “We compare Standard PSO, SAPSO, and Random Search under matched budgets. Phase 12A showed PSO edged SAPSO on 2D mocks — we report that honestly.”

## Ops surface (5:00–6:30)

```bash
evonas serve --demo
```

Browser: overview → benchmarks → registry.

## Close (6:30–7:30)

VO: “v1.0.0 is ready for GitHub, thesis, IEEE drafts, and demos. Neural campaigns are next — not invented today.”

End card: repo URL + `CITATION.cff`.
