# Changelog

All notable changes to EvoNAS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [v1.0.0-rc2] — 2026-07-31

### Added

- AI Governance, Registry & Lifecycle Platform (Phase 11)
- File-backed `FileGovernanceRegistry` under `artifacts/registry/`
- Model stages with single-production invariant + LKG metadata snapshots
- Experiment / dataset / artifact indexes, search, lineage graphs
- Configurable lifecycle transitions + Mermaid visualizations
- Promotion / rollback metadata ledgers (no live deployment mutation)
- CLI: `registry`, `models`, `experiments`, `lineage`, `artifacts`
- Additive API `/api/v1/registry/*` and `/api/v1/models/*`
- Dashboard pages: Registry, Models, Datasets, Lifecycle, Lineage, Version Graph, History
- Ops guides: Registry / Lifecycle / Lineage / Governance

### Changed

- Package version bumped to **1.0.0rc2**

### Notes

- Algorithms and experiment results are never rewritten by the registry

## [v1.0.0-rc1] — 2026-07-30

### Added

- Scientific Evaluation & Experimental Framework (Phase 10)
- `ExperimentOrchestrator` with algorithm × dataset × seed matrix
- Research baseline: `evonas.benchmarks.RandomSearch` (not closed-loop wired)
- Statistics: mean/median/variance/std/CI + optional Wilcoxon + Cliff’s δ
- Publication figures (PNG/SVG/PDF) and tables (CSV/Markdown/LaTeX)
- Experiment registry (`artifacts/research/index.jsonl`) + checksums
- Auto research reports (methodology / results / limitations / threats)
- CLI: `evonas benchmark`, `experiment`, `compare`, `report`
- Research docs: protocol, benchmark/reproducibility/figure/methodology guides

### Changed

- Package version bumped to **1.0.0rc1**
- Dashboard query discovers `artifacts/research` comparisons (no UI rewrite)

### Notes

- Optimizers / trainer / API / dashboard presentation engines unchanged
- Reporting is unbiased — winners follow recorded metrics only

## [v0.9.0] — 2026-07-30

### Added

- Platform Services & Deployment Layer (Phase 9) — FastAPI control plane
- `/api/v1` health, status, system, config, dashboard, optimization, training,
  closed-loop, continuous-learning, benchmarks, experiments, artifacts, replay, jobs
- Application platform services with FastAPI dependency injection
- In-memory JobManager (queued / running / completed / failed / cancelled)
- WebSocket live events at `/api/v1/ws/events`
- Dashboard API client — Streamlit no longer reads artifacts directly
- CLI: `evonas api`, `evonas serve`, `evonas status`
- Optional extra: `evonas[api]` (fastapi, uvicorn, httpx)
- Docker Compose (`api` + `dashboard`), Dockerfile.dashboard
- `configs/api`, `configs/deploy`, `.env.example`
- Ops docs: Deployment Guide, API Reference
- Phase 9 report and release notes

### Changed

- Package version bumped to **0.9.0**
- Artifact query facade moved to `application/platform` (shared by API)

### Notes

- Domain engines unchanged; API wraps existing use cases only
- Auth / cloud / Kubernetes / external DBs deferred

## [v0.8.0] — 2026-07-30

### Added

- AI Operations Dashboard (Phase 8) — Streamlit multipage control center
- `DashboardService` read-only facade over artifacts + ArchitectureVisualizer
- Demo Mode for presentations (no training / optimization)
- Plotly charts: fitness, SAPSO coefficients, diversity, drift, training curves
- Pages: Landing, Overview, Optimization, SAPSO, Architecture, Training, CL,
  Closed Loop, Experiments, Replay, Benchmarks, Artifacts, Health, Settings
- CLI: `evonas dashboard [--demo] [--port] [--headless]`
- Optional extra: `evonas[dashboard]` (streamlit, plotly, pandas, matplotlib)
- Phase 8 report and release notes
- Presentation-layer dashboard tests

### Changed

- Package version bumped to **0.8.0**

### Notes

- Dashboard consumes public interfaces / artifacts only — PSO/SAPSO/CL/Controller untouched.
- Deployment / FastAPI / auth deferred.

## [v0.7.0] — 2026-07-29

### Added

- Continuous Learning & Data Evolution Engine (Phase 7)
- `ContinuousLearningEngine` — detect → validate → version → drift → recommend
- `DataVersionManager`, `DatasetChangeDetector`, `IncrementalDatasetBuilder`
- `LearningPolicy` recommendations (`HOLD` / `RETRAIN_SAME_ARCH` / `OPTIMIZE_ARCH`)
- Dataset lineage, learning events, retention, window cursors, deterministic replay
- Drift integration via Phase 1 PSI/KS (`IDatasetManager` / `detect_shift`) — no duplicated math
- History export (JSON/CSV) + matplotlib visualizations
- Configs: `configs/continuous_learning/default.yaml`, `configs/continuous/default.yaml`
- CLI: `evonas learn`, `detect-data`, `replay-learning`
- Ports: `IContinuousLearningEngine`, `IDataVersionManager`, `IDatasetChangeDetector`, `ILearningPolicy`
- Optional ClosedLoopController observation merge via `to_observation()` only
- Phase 7 report and release notes
- Continuous-learning test suite

### Changed

- Package version bumped to **0.7.0**
- README roadmap marks Phase 7 complete
- RC1 freeze polish: domain hashing helpers; continuous plots via application layer; README extras aligned

### Notes

- Learning policies never authorize optimization — Decision Engine remains sole authority.
- Phase 1 data abstractions, Standard PSO, and SAPSO are unmodified.
- Release Candidate package documented under `docs/rc1/` (READY FOR PHASE 8 after tag push).

## [v0.6.0] — 2026-07-29

### Added

- Closed-Loop Autonomous Optimization Controller (Phase 6)
- `ClosedLoopController` + `WorkflowExecutor` orchestration (no PSO/train math in controller)
- Immutable serializable `DecisionContext` and policy-driven `DecisionEngine`
- `OptimizationTrigger` (manual / scheduled / metric / drift / budget)
- Lifecycle state machine with logged transitions
- `ValidationEngine` + local `PromotionManager` (accept/reject, no deploy)
- Failure recovery to safe `MONITORING` state
- Lifecycle history recorder (JSON / CSV / decisions JSONL)
- Lifecycle matplotlib visualizations
- Configs: `configs/closed_loop/default.yaml`, `simulate.yaml`, `configs/policies/default_policy.yaml`
- CLI: `evonas run-loop`, `simulate-loop`, `inspect-loop`
- Ports: `IClosedLoopController`, `IDecisionEngine`, `IOptimizationTrigger`, `IValidationEngine`, `IPromotionManager`
- Phase 6 report and release notes
- Decision / closed-loop test suites

### Changed

- Package version bumped to **0.6.0**
- README roadmap marks Phase 6 complete

### Notes

- Controller orchestrates existing `OptimizeUseCase` (SAPSO default, PSO selectable).
- Standard PSO and SAPSO engines are unmodified.
- No deployment, continuous learning datasets, FastAPI, dashboard, or registry in this release.

## [v0.5.0] — 2026-07-29

### Added

- Self-Adaptive PSO (SAPSO) engine (Phase 5)
- `AdaptiveController`, `ParameterScheduler`, `AdaptiveStateMachine`, `AdaptiveConfig`
- Normalized diversity metrics (`diversity.py`)
- `SelfAdaptivePSO` extending `StandardPSO` via `_get_velocity_coeffs()` hook
- Adaptive history recorder (JSON/CSV + state transitions)
- Adaptive coefficient / diversity / phase visualization
- `BenchmarkRunner` and `OptimizerComparison`
- `CompareOptimizersUseCase` + CLI `evonas compare-optimizers`
- Configs: `configs/pso/adaptive.yaml`, `adaptive_mock.yaml`, `configs/optimization/*`
- Port `IAdaptiveController`
- Phase 5 report and release notes
- Expanded optimization tests (**84 passing**)

### Changed

- `StandardPSO` exposes `_get_velocity_coeffs()` extension hook (fixed values unchanged)
- `OptimizeUseCase` selects `pso` vs `sapso` from YAML `optimization.algorithm`
- Package version bumped to **0.5.0**

### Notes

- Adaptation is deterministic and behaviour-driven — not random schedules.
- No closed-loop / continuous-learning behaviour in this release.

## [v0.4.0] — 2026-07-28

### Added

- Standard Particle Swarm Optimization engine (Phase 4)
- Domain modules: particle, swarm, velocity, position, initialization, stopping, history, cache, adapter
- `StandardPSO` implementing `ISearchAlgorithm` with fixed \(w, c_1, c_2\)
- `Fitness` / `FitnessCalculator` and `IFitnessEvaluator`
- `MockFitnessEvaluator` (Sphere / Rastrigin) and `ArchitectureFitnessEvaluator`
- Evaluation caching by `arch_id` + train-config hash
- `OptimizeUseCase` with reproducible artifact export
- CLI: `evonas optimize` (`--config`, `--out`, `--dry-run`, `--verbose`)
- Configs: `configs/pso/standard.yaml`, `configs/pso/mock_sphere.yaml`
- Search space: `configs/search_spaces/sphere_2d.yaml`
- PSO visualization (matplotlib Agg, optional)
- Optimization test suite
- Phase 4 report and release notes

### Notes

- No Self-Adaptive PSO / adaptive coefficients in this release.
- No closed-loop controller or continuous learning.

## [v0.3.0] — 2026-07-28

### Added

- Dynamic model generation framework (Phase 3)
- Expandable `LayerSpec` IR and `ArchitectureSpec.resolved_layers()`
- `ArchitectureSerializer` (JSON / YAML / dict) with schema versioning
- `ArchitectureValidator`, `ConstraintHandler`, `ArchitectureFactory`
- `SearchSpace` / `GeneSpec` and `ArchitectureGenerator` encode/decode
- Complexity estimator and text `ArchitectureVisualizer`
- `DynamicNetwork` PyTorch builder driven entirely by architecture IR
- Ports: `IArchitectureGenerator`, `IConstraintHandler`
- Configs: `configs/models/baseline.yaml`, `future_template.yaml`
- Search spaces: `configs/search_spaces/cnn_quick.yaml`, `cnn_small.yaml`
- CLI: `evonas build-model`, `inspect-model`, `validate-model`
- Architecture test suite including 100-genotype 1-epoch smoke (≥95%)
- Phase 3 report and release notes

### Changed

- `PyTorchModelBuilder` now builds `DynamicNetwork` (no BaselineCNN dependency)
- `ModelFactory` validates architectures before build
- Package version bumped to **0.3.0**

### Notes

- No PSO / NAS / closed-loop behavior in this release.
- Phase 2 training APIs and YAML remain backward compatible.
- `BaselineCNN` retained as a historical reference module only.

## [v0.2.0] — 2026-07-28

### Added

- Baseline learning system (Phase 2)
- `ArchitectureSpec` / `ConvBlockSpec` domain IR
- `ITrainableModel`, `IModelBuilder`, `ITrainingEngine`, `IEvaluationEngine`, `ICheckpointManager`
- `BaselineCNN` + `PyTorchModelBuilder` + `ModelFactory`
- `PyTorchTrainingEngine` with epoch loop, validation, early-stopping hook, checkpoints
- `PyTorchEvaluationEngine` with accuracy / precision / recall / F1 / confusion matrix
- Reusable domain metrics module
- `FileCheckpointManager`, `ArtifactManager`, `ExperimentRecorder`
- Training YAML: `configs/training/baseline.yaml`, `configs/models/baseline_cnn.yaml`
- CLI: `evonas train`, `evonas train-baseline`
- Phase 2 report and release notes
- Expanded test suite (**40 passing**)

### Notes

- No PSO / NAS / closed-loop behavior in this release.
- TensorFlow trainer remains deferred; ports allow a future adapter.

## [v0.1.0] — 2026-07-28

### Added

- Initial repository foundation (`src/evonas` Clean Architecture layout, packaging, CLI stub)
- Complete dataset management subsystem (`DatasetManager` / `IDatasetManager`)
- Dataset registry with atomic manifest generation under `artifacts/datasets/`
- Deterministic train / validation / test splits with checksum stability
- Dataset statistics computation for observability and drift reference
- PSI and Kolmogorov–Smirnov drift detection (`DefaultDriftDetector`)
- Transform pipeline (normalize, flatten)
- Configuration system (`ConfigurationManager`) with stable config hashing
- Structured logging bootstrap
- Quick Mode toy dataset (`configs/datasets/toy_quick.yaml`) plus MNIST / Fashion-MNIST / CIFAR-10 config stubs
- Future continuous learning hooks (`get_window`, subset, drift reports)
- Optional torchvision loader behind `evonas[pytorch]`
- Unit / integration tests (**29 passing**, ~82% line coverage)
- Phase 1 freeze report (`docs/phase_reports/phase1.md`)

### Notes

- No neural network training, PSO, or closed-loop controller in this release.
- Production optimization engine remains SAPSO-only per `idea.md` (implemented in later phases).

[v1.0.0-rc2]: https://github.com/CoderAnush/EvoNAS/releases/tag/v1.0.0-rc2
[v1.0.0-rc1]: https://github.com/CoderAnush/EvoNAS/releases/tag/v1.0.0-rc1
[v0.9.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.9.0
[v0.8.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.8.0
[v0.7.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.7.0
[v0.6.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.6.0
[v0.5.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.5.0
[v0.4.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.4.0
[v0.3.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.3.0
[v0.2.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.2.0
[v0.1.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.1.0
