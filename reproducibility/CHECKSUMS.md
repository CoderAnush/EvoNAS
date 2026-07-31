# Checksums — EvoNAS v1.0.0

## Per research run

Each suite directory under `artifacts/research/<id>/` includes `checksums.json` covering:

- `meta.json`
- `results.json`
- `statistics.json`
- `comparison.json`

## Config hash

`meta.json` → `config_hash` (SHA-256 of suite YAML).

## Phase 12A reference hashes

See `paper/appendix.md` or `artifacts/research/phase12a_campaign/manifest.json`.

## Release tree checksum (optional)

```bash
# Example — adjust excludes for your OS
git archive v1.0.0 | sha256sum
```

Record output in this file when publishing the GitHub release:

```text
git archive sha256: [PLACEHOLDER]
```
