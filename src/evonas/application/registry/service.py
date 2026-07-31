"""Application governance / registry use-cases (Phase 11)."""

from __future__ import annotations

from typing import Any

from evonas.application.registry.sync import RegistrySyncService
from evonas.infrastructure.registry.file_registry import FileGovernanceRegistry


class GovernanceService:
    """Facade for registry operations used by CLI / API / dashboard."""

    def __init__(self, registry: FileGovernanceRegistry | None = None) -> None:
        self.registry = registry or FileGovernanceRegistry.from_yaml()
        self._sync = RegistrySyncService(self.registry)

    def sync(self) -> dict[str, Any]:
        return self._sync.sync_all()

    def overview(self) -> dict[str, Any]:
        return self.registry.overview()

    def list_models(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("model", limit=limit)

    def get_model(self, model_id: str, version: str | None = None) -> dict[str, Any] | None:
        return self.registry.get_model(model_id, version)

    def register_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.registry.register(payload)

    def set_stage(
        self,
        model_id: str,
        version: str,
        stage: str,
        *,
        reason: str = "",
    ) -> dict[str, Any]:
        return self.registry.set_stage(model_id, version, stage, reason=reason)

    def list_experiments(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("experiment", limit=limit)

    def list_datasets(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("dataset", limit=limit)

    def list_artifacts(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("artifact", limit=limit)

    def list_promotions(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("promotion", limit=limit)

    def list_rollbacks(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.registry.list_objects("rollback", limit=limit)

    def search(self, **filters: Any) -> list[dict[str, Any]]:
        limit = int(filters.pop("limit", 100))
        return self.registry.search(filters, limit=limit)

    def lineage(self, object_id: str) -> dict[str, Any]:
        if "@" not in object_id and not str(object_id).startswith(("exp", "art_", "ds_")):
            graph = self.registry.model_lineage(object_id)
            if graph.get("models"):
                return graph
        sub = self.registry.lineage.subgraph(object_id, max_depth=12)
        sub["mermaid"] = self.registry.lineage.mermaid(object_id, max_depth=12)
        return sub

    def history(self, object_id: str) -> list[dict[str, Any]]:
        return self.registry.history(object_id)

    def compare(self, left: str, right: str) -> dict[str, Any]:
        return self.registry.compare_models(left, right)

    def lifecycle_graph(self) -> dict[str, Any]:
        return {
            "graph": self.registry.lifecycle.graph(),
            "mermaid": self.registry.lifecycle.mermaid_lifecycle(),
            "stages_mermaid": self.registry.lifecycle.mermaid_stages(),
        }

    def transition(
        self,
        kind: str,
        object_id: str,
        target: str,
        *,
        reason: str = "",
    ) -> dict[str, Any]:
        return self.registry.transition_lifecycle(kind, object_id, target, reason=reason)

    def dashboard_bundle(self) -> dict[str, Any]:
        return {
            "overview": self.overview(),
            "models": self.list_models(limit=50),
            "experiments": self.list_experiments(limit=50),
            "datasets": self.list_datasets(limit=50),
            "artifacts": self.list_artifacts(limit=50),
            "promotions": self.list_promotions(limit=50),
            "rollbacks": self.list_rollbacks(limit=50),
            "lifecycle": self.lifecycle_graph(),
        }
