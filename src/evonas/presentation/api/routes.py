"""API route modules."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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
from evonas.presentation.api import deps
from evonas.presentation.api.schemas import (
    ArtifactPreviewRequest,
    DemoToggleRequest,
    HealthResponse,
    JobCreateRequest,
    JobResponse,
    ReplayRequest,
)

if TYPE_CHECKING:
    from evonas.application.registry.service import GovernanceService

router = APIRouter(prefix="/api/v1")


def _job(record: Any) -> JobResponse:
    return JobResponse(**record.to_dict())


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health(svc: HealthService = Depends(deps.health_service)) -> HealthResponse:
    data = svc.health()
    return HealthResponse(**data)


@router.get("/status", tags=["health"])
def status(svc: HealthService = Depends(deps.health_service)) -> dict[str, Any]:
    return svc.status()


@router.get("/system", tags=["health"])
def system(svc: HealthService = Depends(deps.health_service)) -> dict[str, Any]:
    return svc.system()


@router.get("/version", tags=["health"])
def version(svc: HealthService = Depends(deps.health_service)) -> dict[str, Any]:
    return {"version": svc.health()["version"]}


@router.get("/config", tags=["configuration"])
def config(svc: ConfigurationService = Depends(deps.configuration_service)) -> dict[str, Any]:
    return {
        "api": svc.api_settings(),
        "dashboard": svc.dashboard_settings(),
    }


@router.get("/dashboard/landing", tags=["dashboard"])
def dash_landing(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.landing()


@router.get("/dashboard/overview", tags=["dashboard"])
def dash_overview(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.overview()


@router.get("/dashboard/optimization", tags=["dashboard"])
def dash_opt(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.optimization()


@router.get("/dashboard/sapso", tags=["dashboard"])
def dash_sapso(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.sapso()


@router.get("/dashboard/lifecycle", tags=["dashboard"])
def dash_life(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.lifecycle()


@router.get("/dashboard/continuous", tags=["dashboard"])
def dash_cl(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.continuous()


@router.get("/dashboard/training", tags=["dashboard"])
def dash_train(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.training()


@router.get("/dashboard/architecture", tags=["dashboard"])
def dash_arch(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.architecture()


@router.get("/dashboard/experiments", tags=["dashboard"])
def dash_exps(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> list[dict[str, Any]]:
    return svc.experiments()


@router.get("/dashboard/comparison", tags=["dashboard"])
def dash_cmp(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.comparison()


@router.get("/dashboard/health", tags=["dashboard"])
def dash_health(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.health()


@router.get("/dashboard/settings", tags=["dashboard"])
def dash_settings(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.settings()


@router.post("/dashboard/demo", tags=["dashboard"])
def dash_demo(
    body: DemoToggleRequest,
    svc: DashboardQueryService = Depends(deps.dashboard_service),
) -> dict[str, Any]:
    svc.set_demo(body.demo)
    return {"demo": body.demo}


@router.get("/optimization", tags=["optimization"])
def optimization_get(svc: OptimizationService = Depends(deps.optimization_service)) -> dict[str, Any]:
    return svc.current()


@router.get("/optimization/sapso", tags=["optimization"])
def optimization_sapso(svc: OptimizationService = Depends(deps.optimization_service)) -> dict[str, Any]:
    return svc.sapso()


@router.post("/optimization/jobs", response_model=JobResponse, tags=["optimization"])
def optimization_start(
    body: JobCreateRequest,
    svc: OptimizationService = Depends(deps.optimization_service),
) -> JobResponse:
    return _job(svc.start(body.config_path, output_dir=body.output_dir, dry_run=body.dry_run))


@router.get("/training", tags=["training"])
def training_get(svc: TrainingService = Depends(deps.training_service)) -> dict[str, Any]:
    return svc.current()


@router.post("/training/jobs", response_model=JobResponse, tags=["training"])
def training_start(
    body: JobCreateRequest,
    svc: TrainingService = Depends(deps.training_service),
) -> JobResponse:
    return _job(svc.start(body.config_path))


@router.get("/closed-loop", tags=["closed-loop"])
def closed_loop_get(svc: ClosedLoopService = Depends(deps.closed_loop_service)) -> dict[str, Any]:
    return svc.current()


@router.post("/closed-loop/jobs", response_model=JobResponse, tags=["closed-loop"])
def closed_loop_start(
    body: JobCreateRequest,
    svc: ClosedLoopService = Depends(deps.closed_loop_service),
) -> JobResponse:
    return _job(
        svc.start(
            body.config_path,
            simulate=bool(body.simulate if body.simulate is not None else True),
            dry_run=bool(body.dry_run if body.dry_run is not None else True),
            max_cycles=body.max_cycles,
            output_dir=body.output_dir,
        )
    )


@router.get("/continuous-learning", tags=["continuous-learning"])
def cl_get(svc: ContinuousLearningService = Depends(deps.continuous_service)) -> dict[str, Any]:
    return svc.current()


@router.post("/continuous-learning/jobs", response_model=JobResponse, tags=["continuous-learning"])
def cl_start(
    body: JobCreateRequest,
    svc: ContinuousLearningService = Depends(deps.continuous_service),
) -> JobResponse:
    return _job(
        svc.start(
            body.config_path,
            cycles=int(body.cycles or 2),
            output_dir=body.output_dir,
        )
    )


@router.get("/benchmarks", tags=["benchmarks"])
def benchmarks_get(svc: BenchmarkService = Depends(deps.benchmark_service)) -> dict[str, Any]:
    return svc.current()


@router.post("/benchmarks/jobs", response_model=JobResponse, tags=["benchmarks"])
def benchmarks_start(
    body: JobCreateRequest,
    svc: BenchmarkService = Depends(deps.benchmark_service),
) -> JobResponse:
    return _job(svc.start(body.config_path, output_dir=body.output_dir))


@router.get("/experiments", tags=["experiments"])
def experiments_list(
    kind: str | None = None,
    q: str | None = None,
    svc: ExperimentService = Depends(deps.experiment_service),
) -> list[dict[str, Any]]:
    return svc.list_experiments(kind=kind, q=q)


@router.get("/experiments/compare", tags=["experiments"])
def experiments_compare(svc: ExperimentService = Depends(deps.experiment_service)) -> dict[str, Any]:
    return svc.compare()


@router.get("/experiments/export", tags=["experiments"])
def experiments_export(svc: ExperimentService = Depends(deps.experiment_service)) -> dict[str, Any]:
    return svc.export()


@router.get("/datasets", tags=["datasets"])
def datasets(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    landing = svc.landing()
    cl = svc.continuous()
    return {
        "current": landing.get("dataset"),
        "lineage": cl.get("lineage"),
        "last_update": landing.get("last_dataset_update"),
    }


@router.get("/architectures", tags=["architectures"])
def architectures(svc: DashboardQueryService = Depends(deps.dashboard_service)) -> dict[str, Any]:
    return svc.architecture()


@router.get("/artifacts", tags=["artifacts"])
def artifacts_list(
    root: str = Query("artifacts"),
    svc: ArtifactService = Depends(deps.artifact_service),
) -> list[dict[str, Any]]:
    return svc.list_files(root)


@router.post("/artifacts/preview", tags=["artifacts"])
def artifacts_preview(
    body: ArtifactPreviewRequest,
    svc: ArtifactService = Depends(deps.artifact_service),
) -> dict[str, Any]:
    return svc.preview(body.path)


@router.get("/artifacts/download", tags=["artifacts"])
def artifacts_download(
    path: str,
    svc: ArtifactService = Depends(deps.artifact_service),
) -> FileResponse:
    resolved = svc.download_path(path)
    if resolved is None:
        raise HTTPException(status_code=404, detail="artifact not found or outside artifacts root")
    return FileResponse(resolved)


@router.get("/replay/{source}", tags=["replay"])
def replay_get(
    source: str,
    svc: ReplayService = Depends(deps.replay_service),
) -> dict[str, Any]:
    return {"source": source, "steps": svc.steps(source)}


@router.post("/replay", tags=["replay"])
def replay_post(
    body: ReplayRequest,
    svc: ReplayService = Depends(deps.replay_service),
) -> dict[str, Any]:
    if body.async_job:
        return _job(svc.enqueue_replay(body.source)).model_dump()
    return {"source": body.source, "steps": svc.steps(body.source)}


@router.get("/jobs", tags=["jobs"])
def jobs_list(
    kind: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from evonas.application.platform.container import get_container

    return [j.to_dict() for j in get_container().jobs.list_jobs(kind=kind, limit=limit)]


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
def jobs_get(job_id: str) -> JobResponse:
    from evonas.application.platform.container import get_container

    job = get_container().jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _job(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse, tags=["jobs"])
def jobs_cancel(job_id: str) -> JobResponse:
    from evonas.application.platform.container import get_container

    job = get_container().jobs.cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _job(job)


@router.get("/events", tags=["events"])
def events_recent(limit: int = 20) -> list[dict[str, Any]]:
    from evonas.application.platform.container import get_container

    return get_container().events.recent(limit)


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """Live job / platform events for the dashboard."""
    from evonas.application.platform.container import get_container

    await websocket.accept()
    hub = get_container().events
    queue = hub.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_text(json.dumps(event, default=str))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(queue)


# ----- Phase 11 Governance / Registry (additive) -----


class StageRequest(BaseModel):
    stage: str = Field(..., examples=["staging", "production", "archived"])
    reason: str = ""


class RegisterModelRequest(BaseModel):
    model_id: str | None = None
    version: str = "1"
    architecture: str | None = None
    optimizer: str | None = None
    dataset_version: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    experiment_id: str | None = None
    stage: str = "none"
    lifecycle_state: str = "created"
    tags: list[str] = Field(default_factory=list)


class TransitionRequest(BaseModel):
    kind: str
    object_id: str
    target: str
    reason: str = ""


def _gov() -> "GovernanceService":
    from evonas.application.registry.service import GovernanceService

    return GovernanceService()


@router.post("/registry/sync", tags=["registry"])
def registry_sync() -> dict[str, Any]:
    return _gov().sync()


@router.get("/registry/overview", tags=["registry"])
def registry_overview() -> dict[str, Any]:
    return _gov().overview()


@router.get("/registry/search", tags=["registry"])
def registry_search(
    q: str | None = None,
    kind: str | None = None,
    optimizer: str | None = None,
    dataset_version: str | None = None,
    version: str | None = None,
    status: str | None = None,
    lifecycle_state: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _gov().search(
        q=q,
        kind=kind,
        optimizer=optimizer,
        dataset_version=dataset_version,
        version=version,
        status=status,
        lifecycle_state=lifecycle_state,
        limit=limit,
    )


@router.get("/models", tags=["registry"])
def models_list(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_models(limit=limit)


@router.post("/models", tags=["registry"])
def models_register(body: RegisterModelRequest) -> dict[str, Any]:
    return _gov().register_model(body.model_dump())


@router.get("/models/compare", tags=["registry"])
def models_compare(left: str, right: str) -> dict[str, Any]:
    return _gov().compare(left, right)


@router.get("/models/{model_id}", tags=["registry"])
def models_get(model_id: str, version: str | None = None) -> dict[str, Any]:
    rec = _gov().get_model(model_id, version)
    if rec is None:
        raise HTTPException(status_code=404, detail="model not found")
    return rec


@router.post("/models/{model_id}/versions/{version}/stage", tags=["registry"])
def models_set_stage(model_id: str, version: str, body: StageRequest) -> dict[str, Any]:
    try:
        return _gov().set_stage(model_id, version, body.stage, reason=body.reason)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/models/{model_id}/lineage", tags=["registry"])
def models_lineage(model_id: str) -> dict[str, Any]:
    return _gov().lineage(model_id)


@router.get("/registry/experiments", tags=["registry"])
def registry_experiments(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_experiments(limit=limit)


@router.get("/registry/datasets", tags=["registry"])
def registry_datasets(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_datasets(limit=limit)


@router.get("/registry/artifacts", tags=["registry"])
def registry_artifacts(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_artifacts(limit=limit)


@router.get("/registry/promotions", tags=["registry"])
def registry_promotions(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_promotions(limit=limit)


@router.get("/registry/rollbacks", tags=["registry"])
def registry_rollbacks(limit: int = 100) -> list[dict[str, Any]]:
    return _gov().list_rollbacks(limit=limit)


@router.get("/registry/lifecycle", tags=["registry"])
def registry_lifecycle() -> dict[str, Any]:
    return _gov().lifecycle_graph()


@router.post("/registry/lifecycle/transition", tags=["registry"])
def registry_transition(body: TransitionRequest) -> dict[str, Any]:
    try:
        return _gov().transition(body.kind, body.object_id, body.target, reason=body.reason)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/registry/history/{object_id}", tags=["registry"])
def registry_history(object_id: str) -> list[dict[str, Any]]:
    return _gov().history(object_id)


@router.get("/registry/lineage/{object_id}", tags=["registry"])
def registry_lineage(object_id: str) -> dict[str, Any]:
    return _gov().lineage(object_id)


@router.get("/dashboard/registry", tags=["dashboard"])
def dash_registry() -> dict[str, Any]:
    return _gov().dashboard_bundle()
