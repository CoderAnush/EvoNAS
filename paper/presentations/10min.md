# 10-Minute Presentation — EvoNAS (Phase 12B)

**Audience:** Conference short talk / seminar lightning  
**Slides:** 8–10 · Timing budget in brackets

---

## Slide 1 — Title (0:00–0:40)
EvoNAS: Autonomous Closed-Loop NAS with SAPSO  
Fair Phase 12A evaluation · `v1.0.0-rc2`  
`[PLACEHOLDER: speaker name]`

## Slide 2 — Problem (0:40–1:40)
NAS often ends at offline search. Missing: continuous loop, policy gates, audit, reproducible packages.

## Slide 3 — System in one diagram (1:40–3:00)
Clean Architecture → SAPSO engine → Closed loop → Registry → Research benchmarks (quarantined).  
`[PLACEHOLDER: architecture figure]`

## Slide 4 — Fair evaluation protocol (3:00–4:00)
Matched budgets · shared seeds · pre-registered RQs/Hs · honest winner = mean fitness.

## Slide 5 — Phase 12A setup (4:00–5:00)
Sphere & Rastrigin · PSO / SAPSO / RS · 10–15 seeds · mock fitness (maximize).

## Slide 6 — Results (5:00–7:00)
**Table:** Sphere paper means (−0.000223 / −0.000350 / −0.136)  
**Message:** PSO > SAPSO > RS everywhere; swarm ≫ RS; H1/H2 not supported.

## Slide 7 — Why honesty matters (7:00–8:20)
Platform integrity claim > “SAPSO always wins.” Neural results still `[PLACEHOLDER]`.

## Slide 8 — Takeaways & future (8:20–9:20)
Integrated platform + fair campaign. Next: neural NAS, drift case studies, 30–50 seeds.

## Slide 9 — Q&A (9:20–10:00)
Point to artifacts path and protocol doc.
