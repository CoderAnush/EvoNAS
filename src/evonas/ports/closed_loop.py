"""Closed-loop ports (Phase 6)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from evonas.domain.decision.context import DecisionContext
from evonas.domain.decision.records import DecisionRecord, TriggerDecision
from evonas.domain.lifecycle.states import LifecycleState
from evonas.domain.promotion.manager import PromotionRecord
from evonas.domain.validation.engine import ValidationResult


@runtime_checkable
class IDecisionEngine(Protocol):
    """Policy-driven lifecycle authority."""

    def should_start_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to start search."""

    def should_retrain(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to retrain."""

    def should_deploy(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to deploy (Phase 8 gated)."""

    def should_rollback(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to rollback (Phase 8 gated)."""

    def should_continue_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether search may continue."""

    def should_stop_optimization(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide whether to stop search."""

    def should_accept_candidate(self, ctx: DecisionContext) -> DecisionRecord:
        """Decide local promotion accept/reject."""


@runtime_checkable
class IOptimizationTrigger(Protocol):
    """Trigger evaluation prior to DecisionEngine start question."""

    def evaluate(self, ctx: DecisionContext) -> TriggerDecision:
        """Return whether optimization should be considered."""


@runtime_checkable
class IValidationEngine(Protocol):
    """Candidate vs baseline validation."""

    def validate(
        self,
        *,
        current_metrics: dict[str, float],
        candidate_metrics: dict[str, float],
        complexity_params: int | None = None,
        train_seconds: float | None = None,
    ) -> ValidationResult:
        """Validate candidate."""


@runtime_checkable
class IPromotionManager(Protocol):
    """Local accept/reject without deployment."""

    def accept(
        self,
        model_id: str,
        *,
        previous_model_id: str | None,
        reason: str,
        metrics: dict[str, float] | None = None,
    ) -> PromotionRecord:
        """Accept candidate locally."""

    def reject(
        self,
        model_id: str,
        *,
        previous_model_id: str | None,
        reason: str,
        metrics: dict[str, float] | None = None,
    ) -> PromotionRecord:
        """Reject candidate."""


@runtime_checkable
class IClosedLoopController(Protocol):
    """Top-level orchestrator public surface."""

    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""

    def run_once(self) -> dict[str, Any]:
        """Execute one observe→…→finish cycle."""

    def run(self, *, max_cycles: int | None = None) -> dict[str, Any]:
        """Run until completed or max_cycles."""
