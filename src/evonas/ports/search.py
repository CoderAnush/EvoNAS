"""Search / fitness ports (idea.md §21.7 / §21.11)."""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from evonas.domain.fitness.types import Fitness
from evonas.domain.optimization.history import SwarmHistory
from evonas.domain.optimization.particle import Particle
from evonas.domain.optimization.result import SearchResult
from evonas.domain.optimization.swarm import SwarmState
from evonas.domain.search_space.space import SearchSpace
from evonas.ports.adaptive import IAdaptiveController


@runtime_checkable
class IFitnessEvaluator(Protocol):
    """Evaluate a continuous genotype position → Fitness.

    PSO never trains models itself — this adapter owns train/eval.
    Designed so future multi-objective evaluators can return richer Fitness.
    """

    def evaluate(self, position: Sequence[float], *, particle_id: str | None = None) -> Fitness:
        """Evaluate one particle position."""


@runtime_checkable
class IFitnessCalculator(Protocol):
    """Aggregate metrics into Fitness."""

    def compute(self, metrics: Any, complexity: Any = None, penalties: Any = None) -> Fitness:
        """Compute fitness from metrics."""


@runtime_checkable
class ISearchAlgorithm(Protocol):
    """Optimizer contract — StandardPSO implements this; SAPSO will too (Phase 5)."""

    def initialize(self, space: SearchSpace, seed: int) -> None:
        """Initialize swarm for ``space`` with ``seed``."""

    def set_evaluator(self, fn: IFitnessEvaluator) -> None:
        """Inject fitness evaluator."""

    def step(self) -> SwarmState:
        """Execute one PSO iteration."""

    def run(self, budget: dict[str, Any] | None = None) -> SearchResult:
        """Run until stopping criteria / budget."""

    def get_best(self) -> Particle:
        """Return best particle (by global best)."""

    def get_history(self) -> SwarmHistory:
        """Return swarm history."""


__all__ = [
    "IAdaptiveController",
    "IFitnessCalculator",
    "IFitnessEvaluator",
    "ISearchAlgorithm",
    "SearchResult",
]
