"""Fitness domain types (multi-objective ready; Phase 4 uses scalar accuracy)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Fitness:
    """Scalar fitness with optional component breakdown.

    ``sense`` is ``maximize`` (default) or ``minimize`` so future
    multi-objective / inverted objectives remain representable.
    """

    value: float
    components: dict[str, float] = field(default_factory=dict)
    sense: str = "maximize"
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_better_than(self, other: Fitness) -> bool:
        """Compare according to sense."""
        if self.sense == "minimize":
            return self.value < other.value
        return self.value > other.value

    def to_dict(self) -> dict[str, Any]:
        """Serialize fitness."""
        return {
            "value": self.value,
            "components": dict(self.components),
            "sense": self.sense,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FitnessConfig:
    """Fitness aggregation configuration (idea.md fitness block)."""

    sense: str = "maximize"
    primary_metric: str = "accuracy"
    accuracy_weight: float = 1.0
    param_lambda: float = 0.0
    fail_value: float = -1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FitnessConfig:
        """Load from YAML mapping."""
        weights = data.get("weights", {}) if isinstance(data.get("weights"), dict) else {}
        penalties = data.get("penalties", {}) if isinstance(data.get("penalties"), dict) else {}
        return cls(
            sense=str(data.get("sense", "maximize")),
            primary_metric=str(data.get("primary_metric", "accuracy")),
            accuracy_weight=float(weights.get("accuracy", data.get("accuracy_weight", 1.0))),
            param_lambda=float(penalties.get("param_lambda", 0.0)),
            fail_value=float(data.get("fail_value", -1.0)),
        )
