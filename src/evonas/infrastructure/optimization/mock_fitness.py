"""Synthetic fitness evaluators for unit tests (Sphere / Rastrigin)."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from evonas.domain.fitness.types import Fitness


class MockFitnessEvaluator:
    """Cheap fitness landscape for PSO correctness tests (no NN training)."""

    def __init__(self, landscape: str = "sphere", *, maximize: bool = False) -> None:
        self._landscape = landscape.lower()
        self._maximize = maximize

    def evaluate(self, position: Sequence[float], *, particle_id: str | None = None) -> Fitness:
        """Evaluate synthetic objective. Default minimize Sphere."""
        x = np.asarray(list(position), dtype=float)
        if self._landscape == "sphere":
            raw = float(np.sum(x * x))
        elif self._landscape == "rastrigin":
            n = x.size
            raw = float(10 * n + np.sum(x * x - 10 * np.cos(2 * np.pi * x)))
        else:
            raise ValueError(f"unknown landscape '{self._landscape}'")
        # For maximize mode invert (useful if PSO config maximize=True)
        value = -raw if self._maximize else raw
        return Fitness(
            value=value,
            components={"raw": raw},
            sense="maximize" if self._maximize else "minimize",
            metadata={"landscape": self._landscape, "particle_id": particle_id},
        )


class ConstantFitnessEvaluator:
    """Deterministic constant fitness (cache / plumbing tests)."""

    def __init__(self, value: float = 0.5) -> None:
        self._value = float(value)

    def evaluate(self, position: Sequence[float], *, particle_id: str | None = None) -> Fitness:
        """Return constant fitness."""
        return Fitness(value=self._value, components={"const": self._value}, sense="maximize")
