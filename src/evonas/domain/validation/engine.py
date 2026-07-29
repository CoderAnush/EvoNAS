"""Validation engine — accept/reject candidates vs baseline (no deploy)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from evonas.domain.decision.policies import DecisionPolicy

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of validating a candidate against the current/baseline model."""

    accepted: bool
    reasons: tuple[str, ...] = ()
    metrics: dict[str, float] = field(default_factory=dict)
    deltas: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize validation result."""
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "metrics": dict(self.metrics),
            "deltas": dict(self.deltas),
        }


class ValidationEngine:
    """Compare candidate metrics to baseline using configurable thresholds."""

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self._policy = policy or DecisionPolicy()

    def validate(
        self,
        *,
        current_metrics: dict[str, float],
        candidate_metrics: dict[str, float],
        complexity_params: int | None = None,
        train_seconds: float | None = None,
    ) -> ValidationResult:
        """Return acceptance decision with reasons."""
        p = self._policy
        reasons: list[str] = []
        cur_acc = float(current_metrics.get("accuracy", 0.0))
        cand_acc = float(candidate_metrics.get("accuracy", float("-inf")))
        delta = cand_acc - cur_acc
        deltas = {"accuracy": delta}
        metrics = {"current_accuracy": cur_acc, "candidate_accuracy": cand_acc}

        ok = True
        if delta < p.min_improvement_abs and not (
            p.allow_parity_promote and delta >= 0
        ):
            ok = False
            reasons.append("insufficient_accuracy_improvement")
        else:
            reasons.append("accuracy_improvement_ok")

        if p.max_complexity_params is not None and complexity_params is not None:
            if complexity_params > p.max_complexity_params:
                ok = False
                reasons.append("complexity_exceeded")
            metrics["complexity_params"] = float(complexity_params)

        if p.max_train_seconds is not None and train_seconds is not None:
            if train_seconds > p.max_train_seconds:
                ok = False
                reasons.append("train_time_exceeded")
            metrics["train_seconds"] = float(train_seconds)

        result = ValidationResult(
            accepted=ok, reasons=tuple(reasons), metrics=metrics, deltas=deltas
        )
        logger.info("Validation accepted=%s reasons=%s", ok, reasons)
        return result
