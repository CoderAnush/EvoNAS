# Release Notes — EvoNAS v0.3.0

**Date:** 2026-07-28  
**Codename:** Dynamic Model Generation Framework  

## Highlights

EvoNAS can now turn an Architecture definition into a trainable PyTorch network without hardcoding depth or hidden sizes. Future PSO (Phase 4) only needs to emit `ArchitectureSpec` objects.

## What you can do

```bash
evonas validate-model --config configs/models/baseline.yaml
evonas inspect-model  --config configs/models/baseline.yaml
evonas build-model    --config configs/models/baseline.yaml
evonas train          --config configs/training/baseline.yaml
```

## Included

- Layer IR (`LayerSpec`) + `ArchitectureSpec` schema 3.0 with Phase 2 legacy synthesis
- `ArchitectureSerializer`, `ArchitectureFactory`, `ArchitectureValidator`, `ConstraintHandler`
- `SearchSpace` / `GeneSpec` + `ArchitectureGenerator` encode/decode
- `DynamicNetwork` + updated `PyTorchModelBuilder`
- Architecture text visualization
- Configs under `configs/models/` and `configs/search_spaces/`
- Comprehensive architecture tests (including 100-genotype smoke ≥95%)

## Not included

PSO, SAPSO, NAS loops, closed-loop control, deployment, or dashboards.

## Upgrade notes

- Package version is **0.3.0**.
- Existing Phase 2 training configs remain valid.
- Prefer `configs/models/baseline.yaml` for explicit layer IR going forward.
