"""Platform application services — wrap use cases / query engines (no business duplication)."""

from __future__ import annotations

import platform
import time
from pathlib import Path
from typing import Any, cast

from evonas import __version__
from evonas.application.platform.container import PlatformContainer
from evonas.application.platform.jobs import JobManager, JobRecord, ProgressCallback


def _d(data: Any) -> dict[str, Any]:
    return cast(dict[str, Any], data) if isinstance(data, dict) else {}


def _l(data: Any) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], data) if isinstance(data, list) else []


class HealthService:
    """Process and artifact health."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def health(self) -> dict[str, Any]:
        """Liveness payload."""
        return {
            "status": "ok",
            "version": __version__,
            "environment": self._c.settings.environment,
        }

    def status(self) -> dict[str, Any]:
        """Richer status including queue."""
        q = self._c.jobs.queue_depth()
        uptime = time.time() - self._c.settings.started_at
        return {
            **self.health(),
            "uptime_s": round(uptime, 1),
            "jobs": q,
            "artifacts_root": str(self._c.settings.artifacts_root),
            "demo": bool(getattr(self._c.dashboard_query.ctx, "demo_mode", False)),
        }

    def system(self) -> dict[str, Any]:
        """System resource snapshot."""
        base = self._c.dashboard_query.health()
        mem_mb = base.get("process_memory_mb")
        cpu = None
        try:
            import psutil  # type: ignore

            cpu = psutil.cpu_percent(interval=0.05)
            if mem_mb is None:
                mem_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
        except Exception:  # noqa: BLE001
            pass
        life = self._c.dashboard_query.lifecycle()
        state = (life.get("summary") or {}).get("state", "—")
        return {
            "version": __version__,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_percent": cpu,
            "process_memory_mb": mem_mb,
            "artifact_bytes": base.get("artifact_bytes", 0),
            "artifact_files": base.get("artifact_files", 0),
            "experiment_count": len(self._c.dashboard_query.experiments()),
            "lifecycle_state": state,
            "queue": self._c.jobs.queue_depth(),
            "uptime_s": round(time.time() - self._c.settings.started_at, 1),
            "warnings": base.get("warnings", []),
            "environment": self._c.settings.environment,
        }


class ConfigurationService:
    """Read-only configuration exposure."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def api_settings(self) -> dict[str, Any]:
        s = self._c.settings
        return {
            "host": s.host,
            "port": s.port,
            "environment": s.environment,
            "artifacts_root": str(s.artifacts_root),
            "max_workers": s.max_workers,
            "default_dry_run": s.default_dry_run,
            "config_path": str(s.config_path),
            "cors_origins": s.cors_origins,
        }

    def dashboard_settings(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.settings())

    def load_yaml(self, path: str) -> dict[str, Any]:
        data = self._c.config_manager.load(path)
        return data if isinstance(data, dict) else {"value": data}


class DashboardQueryService:
    """Dashboard payloads via existing query facade (server-side only)."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def set_demo(self, demo: bool) -> None:
        self._c.set_demo_mode(demo)

    def landing(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.landing())

    def optimization(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.optimization_summary())

    def sapso(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.sapso_analytics())

    def lifecycle(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.lifecycle())

    def continuous(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.continuous())

    def training(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.training())

    def architecture(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.architecture())

    def experiments(self) -> list[dict[str, Any]]:
        return _l(self._c.dashboard_query.experiments())

    def comparison(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.comparison())

    def health(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.health())

    def settings(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.settings())

    def overview(self) -> dict[str, Any]:
        return {
            "landing": self.landing(),
            "pipeline": [
                "dataset",
                "architecture",
                "training",
                "evaluation",
                "sapso",
                "closed_loop",
                "continuous_learning",
                "promotion",
            ],
            "lifecycle": self.lifecycle(),
            "continuous": self.continuous(),
        }


class ArtifactService:
    """Browse and preview artifacts."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def list_files(self, root_key: str = "artifacts") -> list[dict[str, Any]]:
        return _l(self._c.dashboard_query.browse_artifacts(root_key))

    def preview(self, abs_path: str) -> dict[str, Any]:
        return _d(self._c.dashboard_query.read_artifact(abs_path))

    def download_path(self, abs_path: str) -> Path | None:
        path = Path(abs_path)
        root = (self._c.settings.cwd / self._c.settings.artifacts_root).resolve()
        candidates = [path]
        if not path.is_absolute():
            candidates.append((self._c.settings.cwd / path).resolve())
            candidates.append((root / path).resolve())
        for cand in candidates:
            try:
                resolved = cand.resolve()
            except OSError:
                continue
            if not resolved.is_file():
                continue
            try:
                resolved.relative_to(root)
            except ValueError:
                continue
            return resolved
        return None


class ReplayService:
    """Replay recorded histories (no retrain)."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def steps(self, source: str = "lifecycle") -> list[dict[str, Any]]:
        return _l(self._c.dashboard_query.replay_steps(source))

    def enqueue_replay(self, source: str) -> JobRecord:
        jobs: JobManager = self._c.jobs

        def _run(progress: ProgressCallback) -> dict[str, Any]:
            frames = self.steps(source)
            total = max(len(frames), 1)
            for i, _frame in enumerate(frames):
                progress((i + 1) / total, f"replay {source} {i + 1}/{total}")
                time.sleep(0.01)
            return {"source": source, "frames": len(frames)}

        return jobs.submit("replay", _run, meta={"source": source})


class ExperimentService:
    """Experiment listing / compare / export."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def list_experiments(
        self,
        *,
        kind: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = _l(self._c.dashboard_query.experiments())
        if kind:
            rows = [r for r in rows if r.get("kind") == kind]
        if q:
            ql = q.lower()
            rows = [
                r
                for r in rows
                if ql in str(r.get("run_id", "")).lower()
                or ql in str(r.get("algorithm", "")).lower()
                or ql in str(r.get("path", "")).lower()
            ]
        return rows

    def compare(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.comparison())

    def export(self) -> dict[str, Any]:
        return {"experiments": self.list_experiments(), "comparison": self.compare()}


class OptimizationService:
    """Optimization via OptimizeUseCase as background jobs."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def current(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.optimization_summary())

    def sapso(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.sapso_analytics())

    def start(
        self,
        config_path: str,
        *,
        output_dir: str | None = None,
        dry_run: bool | None = None,
    ) -> JobRecord:
        dry = self._c.settings.default_dry_run if dry_run is None else dry_run

        def _run(progress: ProgressCallback) -> dict[str, Any]:
            from evonas.application.optimize import OptimizeUseCase

            progress(0.05, "starting optimization")
            result = OptimizeUseCase(config_manager=self._c.config_manager).run(
                config_path,
                output_dir=output_dir,
                dry_run=dry,
            )
            progress(1.0, "optimization complete")
            return result

        return self._c.jobs.submit(
            "optimization",
            _run,
            meta={"config": config_path, "dry_run": dry},
        )


class TrainingService:
    """Baseline training as background job."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def current(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.training())

    def start(self, config_path: str) -> JobRecord:
        def _run(progress: ProgressCallback) -> dict[str, Any]:
            from evonas.application.train_baseline import TrainBaselineUseCase

            progress(0.1, "starting training")
            result = TrainBaselineUseCase(config_manager=self._c.config_manager).run(
                config_path
            )
            progress(1.0, "training complete")
            return result

        return self._c.jobs.submit("training", _run, meta={"config": config_path})


class ClosedLoopService:
    """Closed-loop inspection + simulation jobs."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def current(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.lifecycle())

    def start(
        self,
        config_path: str,
        *,
        simulate: bool = True,
        dry_run: bool = True,
        max_cycles: int | None = None,
        output_dir: str | None = None,
    ) -> JobRecord:
        def _run(progress: ProgressCallback) -> dict[str, Any]:
            from evonas.application.closed_loop.use_cases import RunClosedLoopUseCase

            progress(0.05, "starting closed loop")
            result = RunClosedLoopUseCase(config_manager=self._c.config_manager).run(
                config_path,
                output_dir=output_dir,
                simulate=simulate,
                dry_run=dry_run,
                max_cycles=max_cycles,
            )
            progress(1.0, "closed loop finished")
            return result

        return self._c.jobs.submit(
            "closed_loop",
            _run,
            meta={"config": config_path, "simulate": simulate},
        )


class ContinuousLearningService:
    """Continuous learning query + jobs."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def current(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.continuous())

    def start(self, config_path: str, *, cycles: int = 2, output_dir: str | None = None) -> JobRecord:
        def _run(progress: ProgressCallback) -> dict[str, Any]:
            from evonas.application.continuous.use_cases import ContinuousLearningUseCase

            progress(0.1, "starting continuous learning")
            result = ContinuousLearningUseCase(
                config_manager=self._c.config_manager
            ).learn(
                config_path,
                output_dir=output_dir,
                cycles=cycles,
            )
            progress(1.0, "learning cycle complete")
            return result

        return self._c.jobs.submit(
            "continuous_learning",
            _run,
            meta={"config": config_path, "cycles": cycles},
        )


class BenchmarkService:
    """PSO vs SAPSO comparison."""

    def __init__(self, container: PlatformContainer) -> None:
        self._c = container

    def current(self) -> dict[str, Any]:
        return _d(self._c.dashboard_query.comparison())

    def start(self, config_path: str, *, output_dir: str | None = None) -> JobRecord:
        def _run(progress: ProgressCallback) -> dict[str, Any]:
            from evonas.application.compare_optimizers import CompareOptimizersUseCase

            progress(0.1, "starting comparison")
            result = CompareOptimizersUseCase(config_manager=self._c.config_manager).run(
                config_path,
                output_dir=output_dir,
            )
            progress(1.0, "comparison complete")
            return result

        return self._c.jobs.submit("benchmark", _run, meta={"config": config_path})
