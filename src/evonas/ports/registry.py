"""Registry ports — Model Registry & governance (idea.md §21.15 / Phase 11)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IModelRegistry(Protocol):
    """First-class model versioning, stages, and lineage queries."""

    def register(self, record: dict[str, Any]) -> dict[str, Any]:
        """Register a model version (metadata only)."""

    def get(self, model_id: str, version: str | None = None) -> dict[str, Any] | None:
        """Fetch a model (latest version if version is None)."""

    def set_stage(self, model_id: str, version: str, stage: str, *, reason: str = "") -> dict[str, Any]:
        """Transition registry stage with audit."""

    def list(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """List registered models (newest first)."""

    def lineage(self, model_id: str) -> dict[str, Any]:
        """Return lineage graph for a model family."""


@runtime_checkable
class IGovernanceStore(Protocol):
    """Unified registry for models, experiments, datasets, artifacts."""

    def upsert(self, kind: str, record: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a registry object."""

    def get(self, kind: str, object_id: str) -> dict[str, Any] | None:
        """Retrieve by kind + id."""

    def list_objects(self, kind: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """List objects of a kind."""

    def search(self, query: dict[str, Any], *, limit: int = 100) -> list[dict[str, Any]]:
        """Search across kinds with filters."""


__all__ = ["IGovernanceStore", "IModelRegistry"]
