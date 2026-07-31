# Possible IEEE / Venue Reviewer Questions (Phase 12B)

Prepared responses for rebuttal drafts. Cite Phase 12A artifacts; never invent neural numbers.

---

## R1. “Contribution unclear — another PSO paper?”

**Response:** Position as **system + evaluation**. Contributions list: Clean-Architecture autonomous NAS lifecycle; SAPSO as production engine with quarantined baselines; fair Phase 12A campaign with honest negative SAPSO result on 2D mocks. Optimizer-only novelty is **not** claimed from 12A.

## R2. “Experiments too weak (synthetic only).”

**Response:** Agree as limitation. Phase 12A intentionally mock-first for reproducibility on frozen `v1.0.0-rc2`. Neural campaigns marked `[PLACEHOLDER]` / future work. Do not overclaim.

## R3. “SAPSO underperforms — why include it as production engine?”

**Response:** Production choice is architectural (adaptive control for harder NAS spaces / closed-loop use). Phase 12A falsifies blanket superiority on 2D mocks; that is reported. Production wiring remains SAPSO per design doctrine; evidence for CNN spaces pending.

## R4. “Missing significance tests / p-values in the paper body.”

**Response:** Pairwise payloads live in `statistics.json`. Camera-ready should promote a multiplicity-corrected table `[PLACEHOLDER: format for rebuttal]`. Descriptive means/ranks are primary in current draft.

## R5. “Unfair budgets?”

**Response:** RS `n_trials = swarm_size × max_iterations` by protocol. PSO mean evaluations 312 vs RS 300 in paper suite (initialization/accounting); document as near-matched and discuss residual asymmetry if reviewers press.

## R6. “Related work incomplete.”

**Response:** `references.bib` contains placeholders; bibliographic completion is a publication checklist item, not a software task.

## R7. “Reproducibility package?”

**Response:** Config hashes, checksums, CLI, commit, version in manifest; `scripts/run_phase12a_campaign.py`; appendix reproduction section.

## R8. “Closed-loop claims unsupported.”

**Response:** Architecture described; **empirical** closed-loop drift study not in Phase 12A — label as system description + future evaluation.

## R9. “Figures low quality / not camera-ready.”

**Response:** PNG/SVG/PDF exist under artifacts; IEEE final pass needs typography polish `[PLACEHOLDER: designer pass]`.

## R10. “Is Random Search sufficient?”

**Response:** Sufficiency for **fairness baseline**, not SOTA. Stronger baselines planned in research quarantine only.
