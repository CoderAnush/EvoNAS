# EvoNAS v0.7.0 RC1 — Release Candidate Notes

**Version:** v0.7.0 RC1  
**Codename:** Closed-Loop + Continuous Learning Freeze  
**Date:** 2026-07-30  
**Authority:** `idea.md`

---

## Features Included

| Phase | Capability |
|---|---|
| 0–1 | Dataset manager, checksums, drift (PSI/KS) |
| 2 | Baseline train / eval / checkpoints |
| 3 | Dynamic architecture IR + PyTorch builder |
| 4 | Standard PSO |
| 5 | SAPSO (deterministic adaptation) |
| 6 | Closed-loop controller (observe→decide→optimize→validate→promote local) |
| 7 | Continuous learning (version/lineage/recommend — no optimize authority) |

---

## Architecture Snapshot

```text
CLI → Application use-cases → Domain services
                           ↘ Ports ← Infrastructure adapters
ContinuousLearningEngine ──to_observation──▶ ClosedLoopController
ClosedLoopController ──OptimizeUseCase──▶ StandardPSO | SAPSO
```

---

## Testing Summary

- **117** pytest cases passing  
- **~85%** line coverage  
- ruff + mypy clean  
- E2E CLI smoke (dataset → PSO → SAPSO → loop → learn) green  

---

## Known Limitations

- No production deployment / rollback (Phase 8)  
- No FastAPI / dashboard (Phase 8–9)  
- No model registry / notifications  
- Real NN fitness slower than mock; demos use mock/toy  
- GitHub Actions CI not yet configured  
- `evonas run` / `replay` are thin redirects to Phase 6 commands  

---

## Roadmap After RC1

1. Freeze push `v0.7.0`  
2. Phase 8 — Deployment Manager  
3. Phase 9 — Dashboard  
4. Research experiments + paper  
5. Registry / tracking phases per `idea.md`

---

## Install (RC1)

```bash
pip install -e ".[dev]"
# optional NN path
pip install -e ".[pytorch,dev]"
evonas doctor
evonas simulate-loop --config configs/closed_loop/simulate.yaml
```
