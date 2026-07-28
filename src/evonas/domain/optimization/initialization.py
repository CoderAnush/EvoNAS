"""Particle initialization strategies (idea.md §13.2)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from evonas.domain.optimization.particle import Particle
from evonas.domain.search_space.space import SearchSpace


class InitializationStrategy(ABC):
    """Strategy for sampling initial particle positions/velocities."""

    @abstractmethod
    def initialize(
        self,
        space: SearchSpace,
        swarm_size: int,
        *,
        seed: int,
        init_velocity_scale: float = 0.2,
    ) -> list[Particle]:
        """Return ``swarm_size`` particles inside the search-space box."""


class RandomInitialization(InitializationStrategy):
    """Uniform random positions; scaled random velocities."""

    def initialize(
        self,
        space: SearchSpace,
        swarm_size: int,
        *,
        seed: int,
        init_velocity_scale: float = 0.2,
    ) -> list[Particle]:
        rng = np.random.default_rng(seed)
        lows, highs = space.bounds()
        lows_a = np.asarray(lows, dtype=float)
        highs_a = np.asarray(highs, dtype=float)
        spans = np.maximum(highs_a - lows_a, 1e-12)
        particles: list[Particle] = []
        for i in range(swarm_size):
            x = rng.uniform(lows_a, highs_a)
            v = rng.uniform(-spans, spans) * float(init_velocity_scale)
            particles.append(
                Particle.from_vectors(f"p{i}", x.tolist(), v.tolist())
            )
        return particles


class SeededInitialization(RandomInitialization):
    """Alias of random init emphasizing deterministic seeding (config clarity)."""


class BaselineInitialization(InitializationStrategy):
    """Seed particle 0 from a baseline genotype; fill the rest randomly.

    Future extension point for warm-start / elite injection.
    """

    def __init__(self, baseline_position: Sequence[float] | None = None) -> None:
        self._baseline = list(float(x) for x in baseline_position) if baseline_position else None
        self._random = RandomInitialization()

    def initialize(
        self,
        space: SearchSpace,
        swarm_size: int,
        *,
        seed: int,
        init_velocity_scale: float = 0.2,
    ) -> list[Particle]:
        particles = self._random.initialize(
            space,
            swarm_size,
            seed=seed,
            init_velocity_scale=init_velocity_scale,
        )
        if self._baseline is not None and particles:
            if len(self._baseline) != space.dimension:
                raise ValueError(
                    f"baseline dim {len(self._baseline)} != space dim {space.dimension}"
                )
            particles[0].position.values = list(self._baseline)
            particles[0].ensure_personal_best()
            particles[0].personal_best = None
            particles[0].ensure_personal_best()
        return particles


def get_initialization(name: str, **kwargs: object) -> InitializationStrategy:
    """Factory for named initialization strategies."""
    key = str(name).lower()
    if key in {"random", "seeded"}:
        return SeededInitialization() if key == "seeded" else RandomInitialization()
    if key == "baseline":
        baseline = kwargs.get("baseline_position")
        return BaselineInitialization(
            baseline if isinstance(baseline, (list, tuple)) else None
        )
    raise ValueError(f"unknown initialization strategy '{name}'")
