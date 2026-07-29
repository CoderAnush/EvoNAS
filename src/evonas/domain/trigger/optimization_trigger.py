"""OptimizationTrigger — metric / drift / budget / manual / schedule (idea.md §21.5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from evonas.domain.decision.context import DecisionContext
from evonas.domain.decision.policies import DecisionPolicy
from evonas.domain.decision.records import TriggerDecision

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TriggerConfig:
    """Which trigger families are enabled."""

    manual: bool = True
    scheduled: bool = True
    metric_based: bool = True
    drift_based: bool = True
    budget_based: bool = True
    # Scheduled: fire when optimizations_used == 0 and force_initial
    schedule_on_first_cycle: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriggerConfig:
        """Load from YAML."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data[k] for k in known if k in data})


class OptimizationTrigger:
    """Evaluate whether the DecisionEngine should even consider optimization."""

    def __init__(
        self,
        policy: DecisionPolicy | None = None,
        config: TriggerConfig | None = None,
    ) -> None:
        self._policy = policy or DecisionPolicy()
        self._config = config or TriggerConfig()

    def evaluate(self, ctx: DecisionContext) -> TriggerDecision:
        """Return TriggerDecision(consider, reasons, scores)."""
        reasons: list[str] = []
        scores: dict[str, float] = {}
        p = self._policy
        cfg = self._config

        if cfg.manual and ctx.force_optimization:
            reasons.append("manual")
            scores["manual"] = 1.0

        if cfg.scheduled and cfg.schedule_on_first_cycle and ctx.budgets.optimizations_used == 0:
            if p.force_initial_search:
                reasons.append("scheduled_initial")
                scores["scheduled"] = 1.0

        if cfg.metric_based:
            acc = ctx.current_metrics.get("accuracy")
            if acc is not None:
                scores["accuracy"] = float(acc)
                if acc < p.accuracy_floor:
                    reasons.append("accuracy_below_floor")
                if ctx.accuracy_threshold is not None and acc < ctx.accuracy_threshold:
                    reasons.append("accuracy_below_threshold")
            # stagnation heuristic: empty improvement in history last entry
            if ctx.optimization_history:
                last = ctx.optimization_history[-1]
                if float(last.get("delta_accuracy", 0.0)) < p.min_expected_improvement:
                    reasons.append("fitness_stagnation")
                    scores["stagnation"] = float(last.get("delta_accuracy", 0.0))

        if cfg.drift_based:
            scores["drift_flag"] = 1.0 if ctx.drift_status == "significant" else 0.0
            if ctx.drift_status == "significant":
                reasons.append("drift_significant")
            psi = ctx.drift_report.get("psi_max")
            if psi is not None and float(psi) >= p.psi_threshold:
                reasons.append("psi_threshold")
                scores["psi_max"] = float(psi)

        if cfg.budget_based:
            remaining = ctx.budgets.max_optimizations - ctx.budgets.optimizations_used
            scores["optimizations_remaining"] = float(remaining)
            if remaining <= 0 or ctx.budgets.optimizations_exhausted:
                # Budget exhausted is a *negative* trigger — do not consider
                logger.info("Trigger suppressed: optimization budget exhausted")
                return TriggerDecision(
                    consider=False,
                    reasons=("budget_exhausted",),
                    scores=scores,
                    trigger_type="budget",
                )

        consider = len(reasons) > 0
        decision = TriggerDecision(
            consider=consider,
            reasons=tuple(reasons),
            scores=scores,
            trigger_type="composite",
        )
        logger.info(
            "Trigger consider=%s reasons=%s", decision.consider, list(decision.reasons)
        )
        return decision
