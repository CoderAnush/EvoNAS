# Lifecycle Guide

## Asset lifecycle states

`created → training → evaluating → candidate → validated → promoted → archived/deprecated/rolled_back/deleted`

Illegal transitions raise `LifecycleError` (`EN_REG_001`).

## Model stages (idea.md §55)

`none → staging → production → archived`

Rules:

- At most one `production` version per `model_id`
- Promoting a new version archives the previous production and writes an LKG **metadata** rollback record
- No live serving pointers are mutated in Phase 11

## Visualization

```bash
evonas registry overview
```

Returns Mermaid for lifecycle and stage graphs (also on dashboard Lifecycle / Version Graph pages).
