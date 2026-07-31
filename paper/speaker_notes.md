# Speaker Notes — EvoNAS Presentations (Phase 12B)

Use with `presentations/10min.md`, `20min.md`, and `45min.md`.  
**Rule:** If asked for a number not in Phase 12A, say “not measured in Phase 12A” — do not improvise.

---

## Opening line (all lengths)

“EvoNAS is an autonomous NAS platform; today I report a fair Phase 12A comparison where we deliberately did **not** force SAPSO to look better than Standard PSO.”

---

## Integrity cues (say explicitly)

- “All means are from `artifacts/research/phase12a_*`.”
- “Fitness sense is maximize; less negative is better.”
- “Training accuracy and inference cost are null for this mock campaign.”
- “H1 and H2 were not supported — that is a feature of honest science.”

---

## 10-minute pacing notes

- Skip architecture depth; one diagram only.
- Spend most time on Slide 6 results table.
- End with: “Platform enables unbiased comparison; neural results are next.”

## 20-minute pacing notes

- Two minutes on closed-loop vs CL distinction — examiners like this.
- When showing ranks, emphasize **identical order** across budgets (H4).
- If overtime, cut instrumentation figures.

## 45-minute pacing notes

- Offer a 60-second “skip path” after architecture if audience is EC-heavy.
- Keep a backup slide with the full campaign summary table.
- Practice answering: “Why did SAPSO lose on Sphere?” → adaptation overhead / landscape too easy / budgets; **do not** invent neural wins.

---

## Hard numbers to memorize

| Claim | Number |
|-------|--------|
| Sphere paper PSO mean | −0.00022277 |
| Sphere paper SAPSO mean | −0.000350268 |
| Sphere paper RS mean | −0.135848 |
| Seeds (paper suite) | 15 |
| Rank order | PSO > SAPSO > RS |
| Bit-exact re-run | true |
| Version | v1.0.0-rc2 |

---

## Transitions

- Problem → System: “So we built a full lifecycle, not only an optimizer.”
- System → Experiments: “Then we froze the code and ran a pre-registered campaign.”
- Results → Discussion: “The interesting result is methodological: the framework can falsify our own hope for SAPSO.”

---

## Closing line

“EvoNAS’s present scientific contribution is a reproducible autonomous NAS stack plus an evaluation practice that reports negative results.”
