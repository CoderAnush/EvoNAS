"""FastAPI dependency providers."""

from __future__ import annotations

from evonas.application.platform.container import PlatformContainer, get_container
from evonas.application.platform.services import (
    ArtifactService,
    BenchmarkService,
    ClosedLoopService,
    ConfigurationService,
    ContinuousLearningService,
    DashboardQueryService,
    ExperimentService,
    HealthService,
    OptimizationService,
    ReplayService,
    TrainingService,
)


def container_dep() -> PlatformContainer:
    return get_container()


def health_service() -> HealthService:
    return HealthService(get_container())


def configuration_service() -> ConfigurationService:
    return ConfigurationService(get_container())


def dashboard_service() -> DashboardQueryService:
    return DashboardQueryService(get_container())


def artifact_service() -> ArtifactService:
    return ArtifactService(get_container())


def replay_service() -> ReplayService:
    return ReplayService(get_container())


def experiment_service() -> ExperimentService:
    return ExperimentService(get_container())


def optimization_service() -> OptimizationService:
    return OptimizationService(get_container())


def training_service() -> TrainingService:
    return TrainingService(get_container())


def closed_loop_service() -> ClosedLoopService:
    return ClosedLoopService(get_container())


def continuous_service() -> ContinuousLearningService:
    return ContinuousLearningService(get_container())


def benchmark_service() -> BenchmarkService:
    return BenchmarkService(get_container())
