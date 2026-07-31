# EvoNAS Research Summary (Phase 12B)

**One-page briefing for PIs, examiners, and collaborators**

## What EvoNAS is

An open Clean-Architecture AutoML/NAS platform with SAPSO as the production search engine, closed-loop governance, continuous-learning recommendations, API/dashboard, and a fair research benchmarking layer.

## What Phase 12A measured

Fair multi-seed comparison of **Standard PSO vs SAPSO vs Random Search** on **Sphere** and **Rastrigin** mock landscapes with matched evaluation budgets. Platform frozen at **v1.0.0-rc2**.

## What the data show (only Phase 12A)

1. **Rank order stable:** Standard PSO > SAPSO > Random Search on every landscape/budget cell.
2. **H1/H2 not supported:** SAPSO did not beat PSO on mean fitness (Sphere paper: −0.000223 vs −0.000350).
3. **H3 supported:** Both swarm methods far beat Random Search (e.g., Sphere paper RS mean −0.136).
4. **Reproducibility:** Bit-exact Standard PSO re-run confirmed.

## What we do **not** claim

- SAPSO superiority on CNN/MNIST/CIFAR `[PLACEHOLDER — not run]`.
- Closed-loop drift recovery rates `[PLACEHOLDER — not in 12A]`.
- Training-time or inference-cost leadership `[null in 12A]`.

## Primary contribution at current evidence

**Integrated autonomous NAS platform + rigorous, unbiased evaluation practice**, not an unqualified optimizer win on 2D mocks.

## Artifacts

- Protocol: `docs/research/experimental_protocol.md`
- Results: `artifacts/research/phase12a_*`
- Manuscript: `paper/ieee_manuscript.md`
