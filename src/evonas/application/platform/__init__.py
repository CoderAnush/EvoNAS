"""Application platform package — jobs, DI, services (Phase 9)."""

from evonas.application.platform.container import (
    PlatformContainer,
    PlatformSettings,
    get_container,
    reset_container,
)
from evonas.application.platform.jobs import JobManager, JobRecord, JobStatus

__all__ = [
    "JobManager",
    "JobRecord",
    "JobStatus",
    "PlatformContainer",
    "PlatformSettings",
    "get_container",
    "reset_container",
]
