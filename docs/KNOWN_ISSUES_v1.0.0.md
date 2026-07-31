# Known Issues — EvoNAS v1.0.0

## Platform

| ID | Issue | Workaround / status |
|----|-------|---------------------|
| KI-1 | API/dashboard have **no built-in auth** | Bind to localhost; add reverse-proxy auth for shared hosts |
| KI-2 | Dashboard requires API | Use `evonas serve` |
| KI-3 | TensorFlow backend stubbed | Use PyTorch extra |
| KI-4 | Mock fitness ≠ neural accuracy | Don’t cite mock fitness as validation accuracy |
| KI-5 | Multi-landscape suite “winner” aggregates cells | Prefer per-dataset ranks in tables |
| KI-6 | RSS memory metric null on Windows | Expected in Phase 12A instrumentation |
| KI-7 | Large artifact trees | Don’t commit generated `artifacts/` dumps to git by default |
| KI-8 | GitHub Pages not auto-configured | Host `website/` manually or enable Pages |

## Research

| ID | Issue | Notes |
|----|-------|-------|
| KI-R1 | No MNIST/CIFAR campaign in v1.0.0 | Placeholder in publication package |
| KI-R2 | Paper-draft seed counts (10–15), not 30–50 | Camera-ready pending |
| KI-R3 | BibTeX placeholders | Complete before IEEE submission |

## Process

Report new issues with `.github/ISSUE_TEMPLATE/bug_report.md`.
