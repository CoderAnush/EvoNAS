# Registry Guide

## Purpose

The governance registry indexes models, experiments, datasets, and artifacts produced by EvoNAS without modifying those results.

## Layout

```text
artifacts/registry/
  model/*.json
  experiment/*.json
  dataset/*.json
  artifact/*.json
  promotion/*.json
  rollback/*.json
  lifecycle_event/*.json
  edges.jsonl
  events.jsonl
  index.jsonl
```

## Sync

```bash
evonas registry sync
```

Scans `artifacts/{baselines,optimization,research,continuous_learning,closed_loop}` and upserts metadata records.

## Config

`configs/registry/registry.yaml` — root path, retention, lifecycle transitions, stage transitions, search fields.
