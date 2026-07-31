# Sequence Diagrams — EvoNAS v1.0.0

See also `docs/architecture/ARCHITECTURE_BOOK.md` §§5–7.

## Optimize (dry-run / mock)

```mermaid
sequenceDiagram
  participant User
  participant CLI
  participant Opt as OptimizeUseCase
  participant PSO as StandardPSO or SAPSO
  participant Mock as MockFitnessEvaluator
  participant Art as ArtifactManager
  User->>CLI: optimize --config --dry-run
  CLI->>Opt: run
  Opt->>PSO: initialize + run
  PSO->>Mock: evaluate
  Mock-->>PSO: fitness
  PSO-->>Opt: SearchResult
  Opt->>Art: write history / metrics
  Opt-->>CLI: summary JSON
```

## Dashboard read path

```mermaid
sequenceDiagram
  participant UI as Streamlit
  participant Client as ApiClient
  participant API as FastAPI
  participant Load as Artifact loaders
  UI->>Client: GET dashboard/overview
  Client->>API: /api/v1/dashboard/overview
  API->>Load: read artifacts
  Load-->>API: payload
  API-->>Client: JSON
  Client-->>UI: render
```

## Registry sync

```mermaid
sequenceDiagram
  participant Op
  participant CLI
  participant Gov as GovernanceService
  participant Sync as RegistrySyncService
  participant FS as FileGovernanceRegistry
  Op->>CLI: registry sync
  CLI->>Gov: sync()
  Gov->>Sync: sync_all()
  Sync->>FS: register metadata from artifacts
  FS-->>Op: overview counts
```
