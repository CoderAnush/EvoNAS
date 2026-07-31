# EvoNAS Conference Poster — Content Layout (Phase 12B)

**Format:** A0 / A1 portrait recommended · Markdown content for design tools (PowerPoint / Inkscape / LaTeX `tikzposter`)  
**Evidence:** Phase 12A only · Placeholders marked

---

## Title banner

**EvoNAS:** Autonomous Closed-Loop NAS with Self-Adaptive PSO  
Fair multi-seed evaluation on Sphere & Rastrigin (Phase 12A)  
Software `v1.0.0-rc2` · `[PLACEHOLDER: authors / institution / QR to repo]`

---

## Column 1 — Problem & System

### Problem
One-shot NAS ≠ continuous governed redesign with audit and rollback.

### Approach
Clean Architecture · SAPSO production engine · Closed loop + CL recommendations · Research baselines quarantined · Registry metadata-only

### `[PLACEHOLDER: small architecture diagram]`

---

## Column 2 — Method

### Fair protocol
- Identical space, seeds, budgets  
- RS trials = swarm × iterations  
- Mean fitness winner (maximize)  
- Wilcoxon + Cliff’s δ when available  

### Suites
Sphere paper (15 seeds) · Multi-landscape (12) · Compact/Extended budgets (10)

---

## Column 3 — Results (Phase 12A numbers)

### Sphere paper mean fitness
| Algo | Mean |
|------|-----:|
| PSO | −0.000223 |
| SAPSO | −0.000350 |
| RS | −0.136 |

### Rank everywhere
**PSO > SAPSO > RS**

### Hypotheses
H1/H2 ✗ · H3 ✓ · H4 ✓ · Bit-exact re-run ✓

### Figures to place
1. Fitness bar chart — `phase12a_sphere_paper/figures/accuracy_fitness_comparison.png`  
2. Coefficient evolution — `phase12a_campaign/figures/coefficient_evolution.png`  
3. Diversity — `phase12a_campaign/figures/diversity_evolution.png`

---

## Column 4 — Takeaways

1. Platform enables unbiased optimizer comparison.  
2. On 2D mocks, classical PSO edged SAPSO; both beat RS.  
3. Neural NAS results: `[PLACEHOLDER]`.  
4. Integrity > marketing claims.

### Footer
Repo / DOI / contact `[PLACEHOLDER]` · Protocol: `experimental_protocol.md`
