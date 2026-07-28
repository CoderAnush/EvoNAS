"""Swarm state and population statistics (idea.md §13 / §86)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from evonas.domain.optimization.particle import Particle, ParticlePosition


@dataclass(slots=True)
class SwarmStatistics:
    """Aggregate swarm metrics for one iteration."""

    mean_fitness: float
    std_fitness: float
    best_fitness: float
    worst_fitness: float
    diversity: float

    def to_dict(self) -> dict[str, float]:
        """Serialize statistics."""
        return {
            "mean_fitness": self.mean_fitness,
            "std_fitness": self.std_fitness,
            "best_fitness": self.best_fitness,
            "worst_fitness": self.worst_fitness,
            "diversity": self.diversity,
        }


@dataclass(slots=True)
class SwarmState:
    """Snapshot of the swarm at iteration ``t`` (Standard PSO: fixed coeffs)."""

    particles: list[Particle]
    gbest_position: ParticlePosition
    gbest_fitness: float
    t: int
    w: float
    c1: float
    c2: float
    diversity: float = 0.0
    statistics: SwarmStatistics | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of particles."""
        return len(self.particles)

    def best_particle(self, *, maximize: bool = True) -> Particle:
        """Return the particle whose fitness matches global best (best effort)."""
        if not self.particles:
            raise ValueError("empty swarm")
        key = (lambda p: p.fitness) if maximize else (lambda p: -p.fitness)
        return max(self.particles, key=key)

    def to_dict(self) -> dict[str, object]:
        """Serialize swarm state."""
        return {
            "t": self.t,
            "w": self.w,
            "c1": self.c1,
            "c2": self.c2,
            "gbest_fitness": self.gbest_fitness,
            "gbest_position": self.gbest_position.as_list(),
            "diversity": self.diversity,
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "particles": [p.to_dict() for p in self.particles],
            "metadata": dict(self.metadata),
        }


class Swarm:
    """Population manager: init tracking, global best, statistics."""

    def __init__(self, particles: Sequence[Particle] | None = None) -> None:
        self._particles: list[Particle] = list(particles or [])
        self._gbest_position: ParticlePosition | None = None
        self._gbest_fitness: float | None = None
        self._iteration: int = 0

    @property
    def particles(self) -> list[Particle]:
        """Live particle list."""
        return self._particles

    @property
    def size(self) -> int:
        """Swarm size."""
        return len(self._particles)

    @property
    def iteration(self) -> int:
        """Current iteration index."""
        return self._iteration

    @property
    def gbest_position(self) -> ParticlePosition | None:
        """Global best position."""
        return self._gbest_position

    @property
    def gbest_fitness(self) -> float | None:
        """Global best fitness."""
        return self._gbest_fitness

    def set_particles(self, particles: Sequence[Particle]) -> None:
        """Replace the population."""
        self._particles = list(particles)

    def compute_diversity(self) -> float:
        """Mean Euclidean deviation from the swarm centroid (idea.md §15.2)."""
        if not self._particles:
            return 0.0
        xs = np.asarray([p.position.as_list() for p in self._particles], dtype=float)
        centroid = xs.mean(axis=0)
        dists = np.linalg.norm(xs - centroid, axis=1)
        return float(dists.mean())

    def compute_statistics(self) -> SwarmStatistics:
        """Compute fitness aggregates + diversity."""
        if not self._particles:
            return SwarmStatistics(0.0, 0.0, float("-inf"), float("inf"), 0.0)
        fits = np.asarray([p.fitness for p in self._particles], dtype=float)
        return SwarmStatistics(
            mean_fitness=float(fits.mean()),
            std_fitness=float(fits.std()),
            best_fitness=float(fits.max()),
            worst_fitness=float(fits.min()),
            diversity=self.compute_diversity(),
        )

    def update_global_best(self, *, maximize: bool = True) -> bool:
        """Refresh global best from personal bests. Return True if gbest changed."""
        if not self._particles:
            return False
        changed = False
        for particle in self._particles:
            particle.ensure_personal_best()
            cand_f = particle.pbest_fitness
            cand_x = particle.pbest_position
            if self._gbest_fitness is None:
                self._gbest_fitness = cand_f
                self._gbest_position = cand_x.copy()
                changed = True
                continue
            better = cand_f > self._gbest_fitness if maximize else cand_f < self._gbest_fitness
            if better:
                self._gbest_fitness = cand_f
                self._gbest_position = cand_x.copy()
                changed = True
        return changed

    def advance(self) -> None:
        """Increment iteration counter."""
        self._iteration += 1

    def snapshot(self, *, w: float, c1: float, c2: float) -> SwarmState:
        """Build an immutable-ish SwarmState view for logging."""
        stats = self.compute_statistics()
        if self._gbest_position is None or self._gbest_fitness is None:
            raise RuntimeError("global best not initialized")
        return SwarmState(
            particles=[p for p in self._particles],
            gbest_position=self._gbest_position.copy(),
            gbest_fitness=float(self._gbest_fitness),
            t=self._iteration,
            w=w,
            c1=c1,
            c2=c2,
            diversity=stats.diversity,
            statistics=stats,
        )
