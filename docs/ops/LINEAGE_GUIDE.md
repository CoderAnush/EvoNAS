# Lineage Guide

## Edges

Lineage is a directed graph stored in `artifacts/registry/edges.jsonl`.

Typical chain:

```text
dataset_version → experiment → model@version → promotion
```

## Query

```bash
evonas lineage <object_id>
```

API: `GET /api/v1/registry/lineage/{object_id}` and `GET /api/v1/models/{model_id}/lineage`

Responses include `nodes`, `edges`, and a Mermaid `flowchart`.
