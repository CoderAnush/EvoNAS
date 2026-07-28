"""Swarm search history recording (JSONL / CSV export)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas.domain.optimization.swarm import SwarmState


@dataclass(slots=True)
class IterationRecord:
    """One PSO iteration log entry."""

    iteration: int
    gbest_fitness: float
    gbest_position: list[float]
    mean_fitness: float
    diversity: float
    evaluations: int
    w: float
    c1: float
    c2: float
    particles: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize record."""
        return {
            "iteration": self.iteration,
            "gbest_fitness": self.gbest_fitness,
            "gbest_position": list(self.gbest_position),
            "mean_fitness": self.mean_fitness,
            "diversity": self.diversity,
            "evaluations": self.evaluations,
            "w": self.w,
            "c1": self.c1,
            "c2": self.c2,
            "particles": list(self.particles),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_swarm_state(
        cls,
        state: SwarmState,
        *,
        evaluations: int,
        include_particles: bool = True,
    ) -> IterationRecord:
        """Build a record from a SwarmState snapshot."""
        stats = state.statistics
        return cls(
            iteration=state.t,
            gbest_fitness=state.gbest_fitness,
            gbest_position=state.gbest_position.as_list(),
            mean_fitness=stats.mean_fitness if stats else 0.0,
            diversity=state.diversity,
            evaluations=evaluations,
            w=state.w,
            c1=state.c1,
            c2=state.c2,
            particles=[p.to_dict() for p in state.particles] if include_particles else [],
            metadata=dict(state.metadata),
        )


@dataclass(slots=True)
class SwarmHistory:
    """Full search history with export helpers."""

    records: list[IterationRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def append(self, record: IterationRecord) -> None:
        """Append an iteration record."""
        self.records.append(record)

    def best_fitness_curve(self) -> list[float]:
        """Global-best fitness over iterations."""
        return [r.gbest_fitness for r in self.records]

    def mean_fitness_curve(self) -> list[float]:
        """Mean swarm fitness over iterations."""
        return [r.mean_fitness for r in self.records]

    def to_dict(self) -> dict[str, Any]:
        """Serialize entire history."""
        return {
            "metadata": dict(self.metadata),
            "records": [r.to_dict() for r in self.records],
        }

    def export_json(self, path: str | Path) -> Path:
        """Write history JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return file_path

    def export_jsonl(self, path: str | Path) -> Path:
        """Write one JSON object per iteration."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as fh:
            for record in self.records:
                fh.write(json.dumps(record.to_dict()) + "\n")
        return file_path

    def export_csv(self, path: str | Path) -> Path:
        """Write a flat CSV of iteration-level metrics (no per-particle dump)."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "iteration",
            "gbest_fitness",
            "mean_fitness",
            "diversity",
            "evaluations",
            "w",
            "c1",
            "c2",
        ]
        with file_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for record in self.records:
                writer.writerow({k: getattr(record, k) for k in fields})
        return file_path
