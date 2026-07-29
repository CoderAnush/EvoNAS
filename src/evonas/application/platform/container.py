"""Platform service container — dependency injection root (Phase 9)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas.application.platform.events import EventHub
from evonas.application.platform.jobs import JobManager
from evonas.infrastructure.config.manager import ConfigurationManager


@dataclass
class PlatformSettings:
    """Resolved API / platform settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:8501"])
    title: str = "EvoNAS Control Plane"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    log_level: str = "INFO"
    json_logs: bool = False
    artifacts_root: Path = field(default_factory=lambda: Path("artifacts"))
    max_workers: int = 2
    default_dry_run: bool = True
    environment: str = "development"
    cwd: Path = field(default_factory=Path.cwd)
    config_path: Path = field(default_factory=lambda: Path("configs/api/default.yaml"))
    started_at: float = field(default_factory=time.time)

    @classmethod
    def from_yaml_and_env(cls, config_path: str | Path | None = None) -> PlatformSettings:
        """Load YAML then overlay environment variables."""
        path = Path(
            config_path
            or os.environ.get("EVONAS_API_CONFIG", "configs/api/default.yaml")
        )
        raw: dict[str, Any] = {}
        manager = ConfigurationManager()
        if path.exists():
            loaded = manager.load(path)
            raw = loaded if isinstance(loaded, dict) else {}
        api = dict(raw.get("api", {}))
        logging_cfg = dict(raw.get("logging", {}))
        artifacts = dict(raw.get("artifacts", {}))
        jobs = dict(raw.get("jobs", {}))
        settings = cls(
            host=str(api.get("host", "0.0.0.0")),
            port=int(api.get("port", 8000)),
            reload=bool(api.get("reload", False)),
            cors_origins=list(api.get("cors_origins", ["http://localhost:8501"])),
            title=str(api.get("title", "EvoNAS Control Plane")),
            docs_url=str(api.get("docs_url", "/docs")),
            redoc_url=str(api.get("redoc_url", "/redoc")),
            openapi_url=str(api.get("openapi_url", "/openapi.json")),
            log_level=str(logging_cfg.get("level", "INFO")),
            json_logs=bool(logging_cfg.get("json_logs", False)),
            artifacts_root=Path(str(artifacts.get("root", "artifacts"))),
            max_workers=int(jobs.get("max_workers", 2)),
            default_dry_run=bool(jobs.get("default_dry_run", True)),
            environment=str(raw.get("environment", "development")),
            cwd=Path.cwd(),
            config_path=path,
        )
        if os.environ.get("EVONAS_API_HOST"):
            settings.host = os.environ["EVONAS_API_HOST"]
        if os.environ.get("EVONAS_API_PORT"):
            settings.port = int(os.environ["EVONAS_API_PORT"])
        if os.environ.get("EVONAS_LOG_LEVEL"):
            settings.log_level = os.environ["EVONAS_LOG_LEVEL"]
        if os.environ.get("EVONAS_JSON_LOGS", "").strip() in {"1", "true", "True"}:
            settings.json_logs = True
        if os.environ.get("EVONAS_ARTIFACTS_ROOT"):
            settings.artifacts_root = Path(os.environ["EVONAS_ARTIFACTS_ROOT"])
        if os.environ.get("EVONAS_ENV"):
            settings.environment = os.environ["EVONAS_ENV"]
        return settings


class PlatformContainer:
    """Singleton-style DI container for FastAPI Depends()."""

    def __init__(self, settings: PlatformSettings | None = None) -> None:
        self.settings = settings or PlatformSettings.from_yaml_and_env()
        self.events = EventHub()
        self.jobs = JobManager(
            max_workers=self.settings.max_workers,
            publish=self.events.publish,
        )
        self.config_manager = ConfigurationManager()
        self._dashboard_query: Any = None  # lazy DashboardService

    @property
    def dashboard_query(self) -> Any:
        """Lazy artifact query engine (existing DashboardService)."""
        if self._dashboard_query is None:
            from evonas.application.platform.query_facade import (
                DashboardContext,
                DashboardService,
            )

            demo = os.environ.get("EVONAS_DASHBOARD_DEMO", "").strip() in {
                "1",
                "true",
                "True",
            }
            self._dashboard_query = DashboardService(
                DashboardContext(cwd=self.settings.cwd, demo_mode=demo)
            )
        return self._dashboard_query

    def set_demo_mode(self, demo: bool) -> None:
        """Toggle demo mode on the query engine."""
        from evonas.application.platform.query_facade import (
            DashboardContext,
            DashboardService,
        )

        self._dashboard_query = DashboardService(
            DashboardContext(cwd=self.settings.cwd, demo_mode=demo)
        )

    def shutdown(self) -> None:
        """Release resources."""
        self.jobs.shutdown(wait=False)


_CONTAINER: PlatformContainer | None = None


def get_container() -> PlatformContainer:
    """Return process-wide container."""
    global _CONTAINER
    if _CONTAINER is None:
        _CONTAINER = PlatformContainer()
    return _CONTAINER


def reset_container(settings: PlatformSettings | None = None) -> PlatformContainer:
    """Replace container (tests)."""
    global _CONTAINER
    if _CONTAINER is not None:
        _CONTAINER.shutdown()
    _CONTAINER = PlatformContainer(settings)
    return _CONTAINER
