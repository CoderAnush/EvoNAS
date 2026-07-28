"""Stopping criteria for Standard PSO (extensible)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class StoppingContext:
    """Inputs consulted by stopping criteria."""

    iteration: int
    max_iterations: int
    best_fitness: float
    evaluations: int
    no_improve_count: int
    target_fitness: float | None = None
    max_no_improve: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StopDecision:
    """Whether the search should stop and why."""

    stop: bool
    reason: str


class StoppingCriterion(ABC):
    """One stopping rule."""

    @abstractmethod
    def evaluate(self, ctx: StoppingContext) -> StopDecision:
        """Return a stop decision for the current context."""


class MaxIterationsCriterion(StoppingCriterion):
    """Stop when iteration reaches max_iterations."""

    def evaluate(self, ctx: StoppingContext) -> StopDecision:
        if ctx.iteration >= ctx.max_iterations:
            return StopDecision(True, "max_iterations")
        return StopDecision(False, "")


class TargetFitnessCriterion(StoppingCriterion):
    """Stop when best fitness reaches/exceeds target (maximize)."""

    def __init__(self, *, maximize: bool = True) -> None:
        self._maximize = maximize

    def evaluate(self, ctx: StoppingContext) -> StopDecision:
        if ctx.target_fitness is None:
            return StopDecision(False, "")
        hit = (
            ctx.best_fitness >= ctx.target_fitness
            if self._maximize
            else ctx.best_fitness <= ctx.target_fitness
        )
        if hit:
            return StopDecision(True, "target_fitness")
        return StopDecision(False, "")


class NoImprovementCriterion(StoppingCriterion):
    """Stop after max_no_improve iterations without gbest improvement."""

    def evaluate(self, ctx: StoppingContext) -> StopDecision:
        if ctx.max_no_improve is None:
            return StopDecision(False, "")
        if ctx.no_improve_count >= ctx.max_no_improve:
            return StopDecision(True, "no_improvement")
        return StopDecision(False, "")


class CompositeStopping:
    """OR-combine multiple stopping criteria."""

    def __init__(self, criteria: list[StoppingCriterion] | None = None) -> None:
        self._criteria = criteria or [
            MaxIterationsCriterion(),
            TargetFitnessCriterion(),
            NoImprovementCriterion(),
        ]

    def evaluate(self, ctx: StoppingContext) -> StopDecision:
        """Stop if any criterion fires."""
        for criterion in self._criteria:
            decision = criterion.evaluate(ctx)
            if decision.stop:
                return decision
        return StopDecision(False, "")
