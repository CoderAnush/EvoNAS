"""Policy-driven DecisionEngine (idea.md §21.6 / §25) — side-effect free."""

from __future__ import annotations

import logging

from evonas.domain.decision.context import DecisionContext
from evonas.domain.decision.policies import DecisionPolicy
from evonas.domain.decision.records import DecisionRecord

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Sole authority for lifecycle verbs (REQ-DEC-001 / REQ-DEC-010).

    Persistence of DecisionRecords is the controller's responsibility.
    """

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self._policy = policy or DecisionPolicy()

    @property
    def policy(self) -> DecisionPolicy:
        """Active policy."""
        return self._policy

    def should_start_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to begin a search (idea.md §25.1)."""
        p = self._policy
        reasons: dict[str, object] = {}

        if ctx.mode == "replay":
            return self._no("should_start_optimization", "NO_OP", "replay_mode", reasons)
        if ctx.optimization_state == "running":
            return self._no("should_start_optimization", "NO_OP", "already_running", reasons)

        if (
            ctx.budgets.hours_since_last_optimization is not None
            and ctx.budgets.hours_since_last_optimization < p.cooldown_hours
        ):
            reasons["hours_since"] = ctx.budgets.hours_since_last_optimization
            reasons["cooldown_hours"] = p.cooldown_hours
            return self._no("should_start_optimization", "NO_OP", "cooldown", reasons)

        if ctx.budgets.optimizations_exhausted or (
            ctx.budgets.optimizations_used >= p.max_optimizations
        ):
            return self._no("should_start_optimization", "NO_OP", "budget_exhausted", reasons)

        if ctx.budgets.search_wallclock_used_minutes >= p.max_search_wallclock_minutes:
            return self._no(
                "should_start_optimization", "NO_OP", "wallclock_budget_exhausted", reasons
            )

        need = False
        if ctx.force_optimization or p.force_initial_search and ctx.budgets.optimizations_used == 0:
            need = True
            reasons["force_or_initial"] = True
        if ctx.trigger_consider:
            need = True
            reasons["trigger"] = list(ctx.trigger_reasons)
        acc = ctx.current_metrics.get("accuracy")
        if acc is not None and acc < p.accuracy_floor:
            need = True
            reasons["accuracy_below_floor"] = acc
        if ctx.drift_status == "significant":
            need = True
            reasons["drift"] = ctx.drift_status
        if acc is not None and ctx.accuracy_threshold is not None and acc < ctx.accuracy_threshold:
            need = True
            reasons["below_threshold"] = True

        if need:
            logger.info("Decision YES START_OPTIMIZATION rationale=%s", reasons)
            return DecisionRecord(
                question="should_start_optimization",
                outcome=True,
                action="START_OPTIMIZATION",
                rationale=reasons,
                policy_version=p.policy_version,
                experiment_id=str(ctx.experiment_metadata.get("experiment_id"))
                if ctx.experiment_metadata.get("experiment_id")
                else None,
            )
        return self._no("should_start_optimization", "NO_OP", "no_trigger", reasons)

    def should_retrain(self, ctx: DecisionContext) -> DecisionRecord:
        """Lifecycle retrain outside search (Phase 6: conservative NO unless candidate)."""
        if ctx.candidate_model_id is not None:
            return DecisionRecord(
                question="should_retrain",
                outcome=True,
                action="RETRAIN",
                rationale={"reason": "candidate_requires_final_fit"},
                policy_version=self._policy.policy_version,
            )
        return self._no("should_retrain", "NO_OP", "no_candidate", {})

    def should_deploy(self, ctx: DecisionContext) -> DecisionRecord:
        """Deploy gate — Phase 6 returns promote-local semantics via Validation+Promotion.

        Actual deployment is Phase 8; this method authorizes *local promotion intent*
        only when ``allow_deploy`` is false we still allow ACCEPT candidate path via
        ``should_accept_candidate``.
        """
        if not self._policy.allow_deploy:
            return self._no(
                "should_deploy",
                "NO_OP",
                "deploy_disabled_until_phase_8",
                {"hint": "use_local_promotion"},
            )
        return self.should_accept_candidate(ctx)

    def should_accept_candidate(self, ctx: DecisionContext) -> DecisionRecord:
        """Accept/reject candidate for local promotion (Phase 6 Validation gate)."""
        p = self._policy
        if not ctx.candidate_metrics or not ctx.candidate_model_id:
            return self._no("should_accept_candidate", "REJECT", "no_candidate", {})
        cand_acc = float(ctx.candidate_metrics.get("accuracy", float("-inf")))
        cur_acc = float(ctx.current_metrics.get("accuracy", 0.0))
        delta = cand_acc - cur_acc
        rationale = {"candidate_accuracy": cand_acc, "current_accuracy": cur_acc, "delta": delta}
        if delta >= p.min_improvement_abs or (p.allow_parity_promote and delta >= 0):
            return DecisionRecord(
                question="should_accept_candidate",
                outcome=True,
                action="ACCEPT",
                rationale=rationale,
                policy_version=p.policy_version,
            )
        rationale["min_improvement_abs"] = p.min_improvement_abs
        return self._no("should_accept_candidate", "REJECT", "insufficient_improvement", rationale)

    def should_rollback(self, ctx: DecisionContext) -> DecisionRecord:
        """Rollback — stub until Phase 8."""
        if not self._policy.allow_rollback:
            return self._no(
                "should_rollback", "NO_OP", "rollback_disabled_until_phase_8", {}
            )
        return self._no("should_rollback", "NO_OP", "no_regression_signal", {})

    def should_continue_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Whether an in-flight search may continue."""
        if ctx.optimization_state != "running":
            return self._no("should_continue_optimization", "NO_OP", "not_running", {})
        if ctx.budgets.search_wallclock_used_minutes >= self._policy.max_search_wallclock_minutes:
            return self._no(
                "should_continue_optimization",
                "STOP_OPTIMIZATION",
                "wallclock",
                {},
            )
        return DecisionRecord(
            question="should_continue_optimization",
            outcome=True,
            action="CONTINUE_OPTIMIZATION",
            rationale={},
            policy_version=self._policy.policy_version,
        )

    def should_stop_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Whether to halt an in-flight search."""
        cont = self.should_continue_optimization(ctx)
        if cont.outcome:
            return self._no("should_stop_optimization", "NO_OP", "continue_allowed", {})
        return DecisionRecord(
            question="should_stop_optimization",
            outcome=True,
            action="STOP_OPTIMIZATION",
            rationale=cont.rationale,
            policy_version=self._policy.policy_version,
        )

    def _no(
        self, question: str, action: str, reason: str, extra: dict
    ) -> DecisionRecord:
        rationale = {"reason": reason, **extra}
        logger.info("Decision NO %s action=%s rationale=%s", question, action, rationale)
        return DecisionRecord(
            question=question,
            outcome=False,
            action=action,
            rationale=rationale,
            policy_version=self._policy.policy_version,
        )
