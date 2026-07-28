"""Particle representation for Standard PSO (idea.md §13)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(slots=True)
class ParticlePosition:
    """Continuous architecture genotype (search-space coordinates)."""

    values: list[float]

    def __len__(self) -> int:
        return len(self.values)

    def copy(self) -> ParticlePosition:
        """Deep copy of the position vector."""
        return ParticlePosition(list(self.values))

    def as_list(self) -> list[float]:
        """Return a plain list copy."""
        return list(self.values)


@dataclass(slots=True)
class ParticleVelocity:
    """Particle velocity vector."""

    values: list[float]

    def __len__(self) -> int:
        return len(self.values)

    def copy(self) -> ParticleVelocity:
        """Deep copy of the velocity vector."""
        return ParticleVelocity(list(self.values))

    def as_list(self) -> list[float]:
        """Return a plain list copy."""
        return list(self.values)


@dataclass(slots=True)
class PersonalBest:
    """Personal-best position and fitness for a particle."""

    position: ParticlePosition
    fitness: float

    def copy(self) -> PersonalBest:
        """Deep copy."""
        return PersonalBest(self.position.copy(), float(self.fitness))


@dataclass(slots=True)
class Particle:
    """One swarm member: position, velocity, fitness, and personal best.

    The PSO engine manipulates vectors only — never neural networks.
    """

    id: str
    position: ParticlePosition
    velocity: ParticleVelocity
    fitness: float = float("-inf")
    personal_best: PersonalBest | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def pbest_position(self) -> ParticlePosition:
        """Personal-best position (falls back to current)."""
        if self.personal_best is None:
            return self.position
        return self.personal_best.position

    @property
    def pbest_fitness(self) -> float:
        """Personal-best fitness (falls back to current)."""
        if self.personal_best is None:
            return self.fitness
        return self.personal_best.fitness

    def dimension(self) -> int:
        """Genotype dimensionality."""
        return len(self.position)

    def ensure_personal_best(self) -> None:
        """Initialize personal best from the current state if missing."""
        if self.personal_best is None:
            self.personal_best = PersonalBest(self.position.copy(), float(self.fitness))

    def update_personal_best(self, *, maximize: bool = True) -> bool:
        """Update personal best if current fitness improves. Return True if updated."""
        self.ensure_personal_best()
        assert self.personal_best is not None
        better = (
            self.fitness > self.personal_best.fitness
            if maximize
            else self.fitness < self.personal_best.fitness
        )
        if better:
            self.personal_best = PersonalBest(self.position.copy(), float(self.fitness))
            return True
        return False

    def to_dict(self) -> dict[str, object]:
        """Serialize particle state for logging."""
        return {
            "id": self.id,
            "position": self.position.as_list(),
            "velocity": self.velocity.as_list(),
            "fitness": self.fitness,
            "pbest_position": self.pbest_position.as_list(),
            "pbest_fitness": self.pbest_fitness,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_vectors(
        cls,
        particle_id: str,
        position: Sequence[float],
        velocity: Sequence[float],
        *,
        fitness: float = float("-inf"),
    ) -> Particle:
        """Construct a particle from raw vectors."""
        pos = ParticlePosition(list(float(x) for x in position))
        vel = ParticleVelocity(list(float(v) for v in velocity))
        particle = cls(id=particle_id, position=pos, velocity=vel, fitness=float(fitness))
        particle.ensure_personal_best()
        return particle
