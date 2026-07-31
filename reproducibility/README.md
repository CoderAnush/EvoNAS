# Reproducibility Package — EvoNAS v1.0.0

This package freezes **how** to reproduce v1.0.0 software behavior and Phase 12A scientific artifacts. It does not change engines.

| File | Purpose |
|------|---------|
| [`VERSION_MANIFEST.md`](VERSION_MANIFEST.md) | Tag, commits, package version |
| [`environment.yml`](environment.yml) | Conda-style environment sketch |
| [`REQUIREMENTS_LOCK.md`](REQUIREMENTS_LOCK.md) | How to lock pip deps |
| [`EXECUTION_GUIDE.md`](EXECUTION_GUIDE.md) | Step-by-step reproduction |
| [`CHECKSUMS.md`](CHECKSUMS.md) | Where checksums live |

## Integrity rules

1. Check out tag `v1.0.0`.
2. Install declared extras.
3. For science claims, prefer Phase 12A suite YAMLs and compare `config_hash`.
4. Never edit `results.json` by hand.
