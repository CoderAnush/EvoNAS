"""Fitness calculator — metrics + complexity → Fitness (idea.md §21.11)."""

from __future__ import annotations

from typing import Any

from evonas.domain.architecture.complexity import ComplexityReport
from evonas.domain.fitness.types import Fitness, FitnessConfig
from evonas.domain.training.types import MetricSet


class FitnessCalculator:
    """Compute scalar fitness from evaluation metrics (extensible weights)."""

    def __init__(self, config: FitnessConfig | None = None) -> None:
        self._config = config or FitnessConfig()

    @property
    def config(self) -> FitnessConfig:
        """Active fitness configuration."""
        return self._config

    def compute(
        self,
        metrics: MetricSet | dict[str, float],
        complexity: ComplexityReport | None = None,
        penalties: dict[str, float] | None = None,
    ) -> Fitness:
        """Aggregate metrics into a Fitness value.

        Phase 4 default: maximize validation accuracy with optional param penalty.
        """
        if isinstance(metrics, MetricSet):
            values = dict(metrics.values)
            primary = metrics.primary
        else:
            values = dict(metrics)
            primary = self._config.primary_metric

        accuracy = float(values.get(primary, values.get("accuracy", self._config.fail_value)))
        param_pen = 0.0
        if complexity is not None and self._config.param_lambda:
            param_pen = self._config.param_lambda * float(complexity.estimated_params)
        extra = float((penalties or {}).get("extra", 0.0))
        value = self._config.accuracy_weight * accuracy - param_pen - extra
        components = {
            "accuracy": accuracy,
            "param_penalty": param_pen,
            "extra_penalty": extra,
        }
        return Fitness(
            value=float(value),
            components=components,
            sense=self._config.sense,
            metadata={"primary": primary},
        )

    def fail(self, reason: str, **meta: Any) -> Fitness:
        """Return configured fail fitness without crashing the swarm."""
        return Fitness(
            value=float(self._config.fail_value),
            components={"fail": 1.0},
            sense=self._config.sense,
            metadata={"reason": reason, **meta},
        )
