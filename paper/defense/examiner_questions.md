# Defense Preparation — Possible Examiner Questions (Phase 12B)

Answers must stay within Phase 12A evidence or clearly label placeholders.

---

## Q1. What is novel — SAPSO or the platform?

**A:** Primary product thesis is the **autonomous closed-loop platform**. SAPSO is the production search engine and a research component, not the sole novelty claim. Phase 12A does not prove SAPSO superiority on 2D mocks.

## Q2. Why did Standard PSO beat SAPSO?

**A:** On Sphere/Rastrigin 2D with these budgets, mean fitness favored PSO (e.g., Sphere paper −0.000223 vs −0.000350). Plausible factors: landscape simplicity, adaptation overhead, coefficient dynamics. We do **not** claim this transfers to CNN NAS `[PLACEHOLDER]`.

## Q3. Is Random Search a strong enough baseline?

**A:** It is a fairness baseline at **matched evaluation count**, not a claim that RS is state-of-the-art NAS. Stronger baselines (Grid on discrete spaces, BO, etc.) are future/`benchmarks/` quarantine work.

## Q4. Why mock fitness instead of MNIST?

**A:** Phase 12A prioritized reproducibility and full multi-seed suites on a frozen platform. Neural campaigns are explicitly deferred in the protocol.

## Q5. How do you prevent optimizer favoritism?

**A:** Pre-registered protocol; identical seeds/spaces/budgets; winner by mean fitness only; negative SAPSO deltas preserved; research baselines not wired into production closed loop.

## Q6. Explain closed loop vs continuous learning.

**A:** CL may recommend; DecisionEngine decides under policy; DecisionRecords audit. Phase 12A did not measure drift YES rates `[PLACEHOLDER]`.

## Q7. What does bit-exact reproducibility mean here?

**A:** Validation re-ran Standard PSO on fixed seeds; mean fitness matched exactly (−0.03588300969384031 twice) in the smoke cell.

## Q8. External validity?

**A:** Limited — 2D continuous mocks. External validity to image NAS is an open threat (documented).

## Q9. Where are the threats to validity?

**A:** Internal (seed/budget choices), external (transfer), construct (mock≠accuracy), conclusion (CI approximation / multiple testing).

## Q10. What would falsify your platform contribution?

**A:** Inability to reproduce suites from config hashes; silent mutation of result files by registry; production loop binding non-SAPSO engines by default — none of these occurred in 12A/11 design.
