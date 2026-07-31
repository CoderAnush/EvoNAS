"""Record builders — attach standard metadata fields."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from evonas import __version__
from evonas.domain.registry.types import LifecycleState, ModelStage, RegistryKind
from evonas.infrastructure.experiments.index import git_commit


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def stamp_metadata(record: dict[str, Any], *, include_git: bool = True) -> dict[str, Any]:
    """Ensure every object exposes metadata / version / checksum fields."""
    payload = dict(record)
    payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    payload.setdefault("updated_at", payload["created_at"])
    payload.setdefault("evonas_version", __version__)
    payload.setdefault("creator", "evonas")
    payload.setdefault("lifecycle_state", LifecycleState.CREATED.value)
    payload.setdefault("tags", [])
    payload.setdefault("relationships", [])
    if include_git:
        payload.setdefault("git_commit", git_commit())
        payload.setdefault("python", platform.python_version())
        payload.setdefault("platform", platform.platform())
    # Stable content hash excluding checksum itself
    body = {k: v for k, v in payload.items() if k not in {"checksum", "hash", "updated_at"}}
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    payload["checksum"] = digest
    payload["hash"] = digest
    return payload


def model_record(
    *,
    model_id: str | None = None,
    version: str = "1",
    architecture: str | None = None,
    optimizer: str | None = None,
    dataset_version: str | None = None,
    training_config: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    artifacts: list[str] | None = None,
    status: str | None = None,
    stage: str = ModelStage.NONE.value,
    lifecycle_state: str = LifecycleState.CREATED.value,
    experiment_id: str | None = None,
    parent_version: str | None = None,
    genotype: list[float] | None = None,
    creator: str = "evonas",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mid = model_id or new_id("mdl")
    rec: dict[str, Any] = {
        "kind": RegistryKind.MODEL.value,
        "id": f"{mid}@{version}",
        "object_id": f"{mid}@{version}",
        "model_id": mid,
        "version": version,
        "architecture": architecture,
        "optimizer": optimizer,
        "dataset_version": dataset_version,
        "training_config": dict(training_config or {}),
        "metrics": dict(metrics or {}),
        "artifacts": list(artifacts or []),
        "status": status or stage,
        "stage": stage,
        "lifecycle_state": lifecycle_state,
        "experiment_id": experiment_id,
        "parent_version": parent_version,
        "genotype": list(genotype or []),
        "creator": creator,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        rec.update(extra)
    return stamp_metadata(rec)
