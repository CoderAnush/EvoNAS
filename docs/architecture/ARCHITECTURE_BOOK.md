# EvoNAS Architecture Book — v1.0.0

**Audience:** Contributors, reviewers, thesis examiners, open-source users  
**Authority:** `idea.md` · Clean Architecture under `src/evonas/`  
**Release:** v1.0.0 (Phase 12C)  
**Scope:** Documentation only — no core engine changes in Phase 12C

---

## 1. Product thesis

EvoNAS is an **autonomous closed-loop AutoML platform**. Neural Architecture Search is a subsystem. Self-Adaptive PSO (SAPSO) is the **production** search engine. Standard PSO and Random Search exist for research comparison only and are not the default closed-loop engine.

## 2. Layered architecture

```mermaid
flowchart TB
  subgraph Presentation
    CLI[CLI]
    API[FastAPI]
    DASH[Streamlit Dashboard]
  end
  subgraph Application
    UC[Use Cases]
    ORCH[Experiment Orchestrator]
    GOV[Governance Service]
    LOOP[Closed-Loop Use Cases]
  end
  subgraph Domain
    PSO[Standard PSO]
    SAPSO[SAPSO]
    FIT[Fitness / Metrics]
    CL[Continuous Learning]
    REG[Registry Types]
  end
  subgraph Ports
    IS[ISearchAlgorithm]
    IF[IFitnessEvaluator]
    IR[IModelRegistry]
  end
  subgraph Infrastructure
    PT[PyTorch Trainer]
    ART[Artifact Manager]
    MOCK[Mock Fitness]
    FREG[File Governance Registry]
  end
  subgraph Quarantine
    BENCH[benchmarks.RandomSearch]
  end
  CLI --> UC
  API --> UC
  DASH --> API
  UC --> Domain
  UC --> Ports
  Infrastructure --> Ports
  BENCH -.->|research only| IS
  SAPSO --> IS
  PSO --> IS
```

### Dependency rule

Presentation → Application → Domain ← Infrastructure (via ports).  
Domain must not import infrastructure or presentation.

## 3. Component catalog

| Component | Package | Role |
|-----------|---------|------|
| Dataset plane | `domain/data`, `infrastructure/data` | Load, validate, drift signals |
| Dynamic builder | `domain/architecture`, `infrastructure/training` | Spec → network |
| Trainer / evaluator | `infrastructure/training` | PyTorch train/eval |
| Standard PSO | `domain/optimization/pso.py` | Fixed-coefficient baseline |
| SAPSO | `domain/optimization/sapso.py` | Adaptive production engine |
| Closed loop | `domain` + application loop use cases | Observe → decide → act |
| Continuous learning | `domain/continuous` | Recommendations only |
| Research suite | `application/research` | Fair multi-seed benchmarks |
| Registry | `domain/registry`, `infrastructure/registry` | Metadata lifecycle |
| Dashboard / API | `presentation/*` | Ops surfaces |

## 4. Deployment diagram

```mermaid
flowchart LR
  USER[Operator / Researcher]
  USER --> CLI
  USER --> BROWSER[Browser]
  BROWSER --> DASH[Dashboard :8501]
  BROWSER --> SWAGGER[API Docs :8000/docs]
  DASH --> API[FastAPI :8000]
  CLI --> API
  CLI --> FS[(artifacts/)]
  API --> FS
  API --> CFG[(configs/)]
  subgraph Optional Docker Compose
    DASH
    API
  end
```

Local default: `evonas serve` (API + dashboard). Docker: see `docs/ops/DEPLOYMENT.md` and `Dockerfile`.

## 5. Sequence — research benchmark cell

```mermaid
sequenceDiagram
  participant CLI
  participant Orch as ExperimentOrchestrator
  participant BR as BenchmarkRunner
  participant Alg as ISearchAlgorithm
  participant Fit as IFitnessEvaluator
  participant Art as ArtifactManager
  CLI->>Orch: run(suite.yaml)
  Orch->>Orch: expand matrix
  loop each algo × dataset × seeds
    Orch->>BR: run(factory, seeds)
    BR->>Alg: initialize + run
    Alg->>Fit: evaluate(position)
    Fit-->>Alg: fitness
    Alg-->>BR: SearchResult
  end
  Orch->>Art: write results/stats/figures/tables
  Orch->>Orch: registry.record
```

## 6. Sequence — closed-loop cycle (conceptual)

```mermaid
sequenceDiagram
  participant Ctrl as ClosedLoop
  participant Dec as DecisionEngine
  participant SAPSO
  participant Train as Trainer
  participant Reg as Registry
  Ctrl->>Ctrl: observe metrics / drift
  Ctrl->>Dec: decide(context, policy)
  alt authorize optimize
    Dec-->>Ctrl: YES
    Ctrl->>SAPSO: search
    Ctrl->>Train: evaluate candidate
    Ctrl->>Reg: record metadata
  else deny / wait
    Dec-->>Ctrl: NO
  end
```

## 7. Sequence — governance promote (metadata)

```mermaid
sequenceDiagram
  participant Op as Operator
  participant CLI
  participant Gov as GovernanceService
  participant FS as FileGovernanceRegistry
  Op->>CLI: models stage id ver production
  CLI->>Gov: transition stage
  Gov->>FS: audit + LKG snapshot metadata
  Note over FS: Does not rewrite experimental results
```

## 8. Invariants (v1.0)

1. Production closed-loop engine = SAPSO (unless explicit research profile).
2. Registry never mutates scientific result files.
3. Benchmark baselines stay in `evonas.benchmarks`.
4. Phase 12A/12B evidence and docs do not alter engines.
5. Config hashes + artifact checksums support reproducibility.

## 9. Related docs

- Quick start / install: `README.md`
- CLI: `CLI.md` · `docs/guides/CLI_GUIDE.md`
- API: `docs/ops/API_REFERENCE.md` · `docs/guides/API_GUIDE.md`
- Config: `CONFIGURATION.md` · `docs/guides/CONFIGURATION_GUIDE.md`
- Architecture diagrams (exportable): `docs/architecture/`
- Research protocol: `docs/research/experimental_protocol.md`
- Publication package: `paper/`
