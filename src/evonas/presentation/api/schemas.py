"""Pydantic request/response schemas for the control plane."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str | None = None


class JobCreateRequest(BaseModel):
    config_path: str = Field(..., examples=["configs/pso/adaptive_mock.yaml"])
    output_dir: str | None = None
    dry_run: bool | None = True
    simulate: bool | None = True
    max_cycles: int | None = None
    cycles: int | None = 2


class JobResponse(BaseModel):
    id: str
    kind: str
    status: str
    progress: float = 0.0
    message: str = ""
    result: Any = None
    error: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: float | None = None
    updated_at: float | None = None


class DemoToggleRequest(BaseModel):
    demo: bool = True


class ArtifactPreviewRequest(BaseModel):
    path: str


class ReplayRequest(BaseModel):
    source: str = Field("lifecycle", examples=["lifecycle", "learning", "optimization"])
    async_job: bool = False


class MessageResponse(BaseModel):
    detail: str
