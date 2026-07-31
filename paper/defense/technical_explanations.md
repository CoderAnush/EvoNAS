# Technical Explanations for Defense / Review (Phase 12B)

Short, precise explanations examiners expect. No new results.

---

## 1. Why maximize sense yields negative fitness

Mock landscapes typically encode a cost (Sphere/Rastrigin). With `maximize=True`, the evaluator returns a transformed score where **higher (less negative) is better**. Always state the sense when quoting means.

## 2. Matched evaluation budget

For swarm methods, a full run uses on the order of `swarm_size × max_iterations` fitness calls (plus initialization accounting). Random Search sets `n_trials` to that product so comparisons are not accidentally budget-asymmetric.

## 3. Why research baselines are quarantined

`evonas.benchmarks` implements `ISearchAlgorithm` but is not the default closed-loop engine. This prevents “algorithm shopping” in production while allowing IEEE-style comparisons.

## 4. SAPSO vs Standard PSO difference

Same velocity skeleton. SAPSO updates \((w,c_1,c_2)\) each iteration via diversity/improvement/phase rules and records adaptive history. Standard PSO keeps fixed Clerc-type coefficients from config.

## 5. What Phase 12A “winner” means

Orchestrator declares winner by **highest mean best fitness** among reported cells under maximize sense. For multi-landscape suites, a single suite-level winner may reflect the best cell; per-dataset ranks are the scientifically preferred readout (always PSO > SAPSO > RS in 12A).

## 6. Registry vs results integrity

Phase 11 governance sync indexes artifacts as metadata. It must not rewrite `results.json`. Phase 12A manifest records sync counts; checksums cover key result files.

## 7. Coefficient / diversity figures

Generated from **instrumentation runs** (representative seed), not averaged across all suite seeds. Treat as descriptive support for RQ4, not as primary endpoint.

## 8. What “not supported” means for H1/H2

Mean(SAPSO) was **not** ≥ mean(PSO) on the stated landscapes. This is not a proof that SAPSO is worse on all problems; it is a failed superiority hypothesis under this protocol.

## 9. Null metrics

Training time, inference cost, neural accuracy, memory RSS were out of scope or unavailable. Do not estimate them verbally in defense.

## 10. How to reproduce a single number

1. Check out commit in manifest.  
2. Install `v1.0.0rc2`.  
3. Run the suite YAML.  
4. Compare `tables/summary.csv` and `meta.json` `config_hash`.
