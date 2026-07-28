"""Evaluation cache for architecture fitness (idea.md Part LXXX)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas.domain.fitness.types import Fitness

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CacheEntry:
    """Cached fitness evaluation."""

    arch_id: str
    fitness: Fitness
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize cache entry."""
        return {
            "arch_id": self.arch_id,
            "fitness": self.fitness.to_dict(),
            "metrics": dict(self.metrics),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """Deserialize cache entry."""
        fit_raw = data.get("fitness", {})
        fitness = Fitness(
            value=float(fit_raw.get("value", 0.0)),
            components=dict(fit_raw.get("components", {})),
            sense=str(fit_raw.get("sense", "maximize")),
            metadata=dict(fit_raw.get("metadata", {})),
        )
        return cls(
            arch_id=str(data["arch_id"]),
            fitness=fitness,
            metrics=dict(data.get("metrics", {})),
            created_at=data.get("created_at"),
        )


class EvaluationCache:
    """In-memory + optional on-disk fitness cache keyed by arch_id (+ train hash)."""

    def __init__(
        self,
        *,
        namespace: str = "default",
        disk_dir: str | Path | None = None,
    ) -> None:
        self._namespace = namespace
        self._memory: dict[str, CacheEntry] = {}
        self._disk_dir = Path(disk_dir) if disk_dir else None
        if self._disk_dir is not None:
            self._disk_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _key(self, arch_id: str, train_hash: str | None = None) -> str:
        suffix = train_hash or "default"
        return f"{self._namespace}:{arch_id}:{suffix}"

    def get(self, arch_id: str, train_hash: str | None = None) -> CacheEntry | None:
        """Return cached entry or None."""
        key = self._key(arch_id, train_hash)
        if key in self._memory:
            self.hits += 1
            return self._memory[key]
        if self._disk_dir is not None:
            path = self._disk_dir / f"{arch_id[:16]}-{train_hash or 'default'}.json"
            if path.exists():
                entry = CacheEntry.from_dict(json.loads(path.read_text(encoding="utf-8")))
                self._memory[key] = entry
                self.hits += 1
                return entry
        self.misses += 1
        return None

    def put(
        self,
        arch_id: str,
        fitness: Fitness,
        *,
        train_hash: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> CacheEntry:
        """Store a fitness result."""
        from datetime import datetime, timezone

        entry = CacheEntry(
            arch_id=arch_id,
            fitness=fitness,
            metrics=dict(metrics or {}),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        key = self._key(arch_id, train_hash)
        self._memory[key] = entry
        if self._disk_dir is not None:
            path = self._disk_dir / f"{arch_id[:16]}-{train_hash or 'default'}.json"
            path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
        return entry

    def stats(self) -> dict[str, int]:
        """Hit/miss counters."""
        return {"hits": self.hits, "misses": self.misses, "size": len(self._memory)}
