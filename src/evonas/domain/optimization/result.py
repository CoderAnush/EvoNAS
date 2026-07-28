"""Search result types for ISearchAlgorithm.run()."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evonas.domain.optimization.history import SwarmHistory
from evonas.domain.optimization.particle import Particle


@dataclass(slots=True)
class SearchResult:
    """Outcome of a completed PSO run."""

    best_particle: Particle
    best_fitness: float
    best_position: list[float]
    history: SwarmHistory
    iterations: int
    evaluations: int
    stopped_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize search result (history summarized)."""
        return {
            "best_fitness": self.best_fitness,
            "best_position": list(self.best_position),
            "best_particle": self.best_particle.to_dict(),
            "iterations": self.iterations,
            "evaluations": self.evaluations,
            "stopped_reason": self.stopped_reason,
            "history_length": len(self.history.records),
            "metadata": dict(self.metadata),
        }
