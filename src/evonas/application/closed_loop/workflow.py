"""Workflow executor — stage orchestration without owning PSO / training math."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

from evonas.domain.decision.context import DecisionContext
from evonas.domain.lifecycle.states import LifecycleState
from evonas.ports.closed_loop import (
    IDecisionEngine,
    IPromotionManager,
    IValidationEngine,
)

if TYPE_CHECKING:
    from evonas.domain.lifecycle.history import LifecycleHistory

logger = logging.getLogger(__name__)

TransitionFn = Callable[[LifecycleState, str], None]
RunOptimizerFn = Callable[[], dict[str, Any]]
ExtractMetricsFn = Callable[[dict[str, Any]], dict[str, float]]
PersistDecisionFn = Callable[[Any], None]


class WorkflowExecutor:
    """Sequence: Decision YES → Optimize → Train/Eval → Validate → Promote.

    Calls existing ports / callables only — never updates PSO equations or
    builds networks directly.
    """

    def __init__(
        self,
        *,
        decisions: IDecisionEngine,
        validation: IValidationEngine,
        promotion: IPromotionManager,
        algorithm: str = "sapso",
    ) -> None:
        self._decisions = decisions
        self._validation = validation
        self._promotion = promotion
        self._algorithm = algorithm

    def run_optimization_pipeline(
        self,
        ctx: DecisionContext,
        *,
        transition: TransitionFn,
        run_optimizer: RunOptimizerFn,
        extract_metrics: ExtractMetricsFn,
        persist_decision: PersistDecisionFn,
        history: LifecycleHistory,
        current_model_id: str,
        current_metrics: dict[str, float],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Execute optimize→validate→accept/reject and return a cycle summary."""
        transition(LifecycleState.OPTIMIZING, "start_optimization")
        history.add_optimization(
            {
                "request": True,
                "algorithm": self._algorithm,
                "dry_run": dry_run,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        opt_summary = run_optimizer()
        transition(LifecycleState.TRAINING, "optimizer_completed_training_path")
        transition(LifecycleState.EVALUATION, "metrics_available")

        candidate_id = str(
            opt_summary.get("best_arch_id")
            or opt_summary.get("best_architecture")
            or f"candidate_{ctx.budgets.optimizations_used}"
        )
        candidate_metrics = extract_metrics(opt_summary)
        train_seconds = float(opt_summary.get("seconds", 0.0) or 0.0)

        transition(LifecycleState.VALIDATION, "validate_candidate")
        validation = self._validation.validate(
            current_metrics=current_metrics,
            candidate_metrics=candidate_metrics,
            complexity_params=opt_summary.get("complexity_params"),
            train_seconds=train_seconds if train_seconds > 0 else None,
        )
        history.add_event("validation", **validation.to_dict())

        ctx_cand = replace(
            ctx,
            candidate_model_id=candidate_id,
            candidate_metrics=candidate_metrics,
            optimization_state="converged",
        )
        d_accept = self._decisions.should_accept_candidate(ctx_cand)
        persist_decision(d_accept)
        d_deploy = self._decisions.should_deploy(ctx_cand)
        persist_decision(d_deploy)

        accepted = validation.accepted and d_accept.outcome
        if accepted:
            promo = self._promotion.accept(
                candidate_id,
                previous_model_id=current_model_id,
                reason="validation_and_decision_accept",
                metrics=candidate_metrics,
            )
            transition(LifecycleState.ACCEPTED, promo.reason)
            history.add_promotion(promo.to_dict())
        else:
            reason = (
                d_accept.rationale.get("reason")
                or (validation.reasons[0] if validation.reasons else "rejected")
            )
            promo = self._promotion.reject(
                candidate_id,
                previous_model_id=current_model_id,
                reason=str(reason),
                metrics=candidate_metrics,
            )
            transition(LifecycleState.REJECTED, promo.reason)
            history.add_promotion(promo.to_dict())

        history.add_optimization(
            {
                "result": opt_summary,
                "accepted": accepted,
                "candidate_id": candidate_id,
            }
        )
        logger.info(
            "Workflow candidate=%s accepted=%s accuracy=%s",
            candidate_id,
            accepted,
            candidate_metrics.get("accuracy"),
        )
        return {
            "optimized": True,
            "accepted": accepted,
            "candidate_id": candidate_id,
            "candidate_metrics": candidate_metrics,
            "optimization": opt_summary,
            "validation": validation.to_dict(),
            "promotion": promo.to_dict(),
            "new_model_id": candidate_id if accepted else current_model_id,
            "new_metrics": candidate_metrics if accepted else current_metrics,
        }
