"""Dataset lineage graph (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class LineageEdge:
    """Parent → child dataset relationship."""

    parent_id: str
    child_id: str
    relation: str  # parent | training | candidate | derived
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize edge."""
        return {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "relation": self.relation,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class DatasetLineage:
    """Maintain full dataset lineage for audit and replay."""

    edges: list[LineageEdge] = field(default_factory=list)
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_node(self, version_id: str, **meta: Any) -> None:
        """Register a version node."""
        self.nodes[version_id] = {"version_id": version_id, **meta}

    def link(
        self,
        parent_id: str | None,
        child_id: str,
        *,
        relation: str = "derived",
        metadata: dict[str, Any] | None = None,
    ) -> LineageEdge | None:
        """Link parent→child; orphan children get a node only."""
        self.add_node(child_id)
        if parent_id is None:
            return None
        self.add_node(parent_id)
        edge = LineageEdge(
            parent_id=parent_id,
            child_id=child_id,
            relation=relation,
            metadata=dict(metadata or {}),
        )
        self.edges.append(edge)
        return edge

    def parents_of(self, version_id: str) -> list[str]:
        """Return parent version ids."""
        return [e.parent_id for e in self.edges if e.child_id == version_id]

    def children_of(self, version_id: str) -> list[str]:
        """Return child version ids."""
        return [e.child_id for e in self.edges if e.parent_id == version_id]

    def history(self, version_id: str) -> list[str]:
        """Walk parents to root (inclusive)."""
        chain = [version_id]
        seen = {version_id}
        current = version_id
        while True:
            parents = self.parents_of(current)
            if not parents:
                break
            parent = parents[0]
            if parent in seen:
                break
            chain.append(parent)
            seen.add(parent)
            current = parent
        return chain

    def to_dict(self) -> dict[str, Any]:
        """Serialize lineage."""
        return {
            "nodes": dict(self.nodes),
            "edges": [e.to_dict() for e in self.edges],
        }

    def export_json(self, path: str | Path) -> Path:
        """Write lineage JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return file_path
