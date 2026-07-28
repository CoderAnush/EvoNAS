# Changelog

All notable changes to EvoNAS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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

[v0.4.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.4.0
[v0.3.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.3.0
[v0.2.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.2.0
[v0.1.0]: https://github.com/CoderAnush/EvoNAS/releases/tag/v0.1.0
