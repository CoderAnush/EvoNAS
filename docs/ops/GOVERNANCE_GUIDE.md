# Governance Guide

## Principles

1. **Metadata only** — never rewrite experiment/model numeric results.
2. **Auditable** — stage/lifecycle events append to `events.jsonl`.
3. **Reproducible** — records stamp `evonas_version`, `git_commit`, checksum/hash.
4. **Searchable** — filters by kind, optimizer, dataset version, metrics, tags, dates.
5. **Separated from algorithms** — PSO/SAPSO/CL/controller untouched.

## Promotion vs deploy

`PromotionManager` (closed-loop) remains local accept/reject. Phase 11 ledger stores promotion/rollback **records** for governance views. Live deployment rollback remains deferred.
