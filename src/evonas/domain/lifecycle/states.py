"""Lifecycle states for the Closed-Loop Controller (Phase 6)."""

from __future__ import annotations

from enum import Enum


class LifecycleState(str, Enum):
    """Explicit lifecycle states — every transition must be logged."""

    IDLE = "idle"
    MONITORING = "monitoring"
    DECISION = "decision"
    OPTIMIZING = "optimizing"
    TRAINING = "training"
    EVALUATION = "evaluation"
    VALIDATION = "validation"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


# Legal directed transitions (orchestrator enforces).
ALLOWED_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.IDLE: frozenset({LifecycleState.MONITORING, LifecycleState.FAILED}),
    LifecycleState.MONITORING: frozenset(
        {LifecycleState.DECISION, LifecycleState.COMPLETED, LifecycleState.FAILED}
    ),
    LifecycleState.DECISION: frozenset(
        {
            LifecycleState.OPTIMIZING,
            LifecycleState.MONITORING,
            LifecycleState.COMPLETED,
            LifecycleState.FAILED,
        }
    ),
    LifecycleState.OPTIMIZING: frozenset(
        {LifecycleState.TRAINING, LifecycleState.EVALUATION, LifecycleState.FAILED}
    ),
    LifecycleState.TRAINING: frozenset(
        {LifecycleState.EVALUATION, LifecycleState.FAILED}
    ),
    LifecycleState.EVALUATION: frozenset(
        {LifecycleState.VALIDATION, LifecycleState.FAILED}
    ),
    LifecycleState.VALIDATION: frozenset(
        {
            LifecycleState.ACCEPTED,
            LifecycleState.REJECTED,
            LifecycleState.FAILED,
        }
    ),
    LifecycleState.ACCEPTED: frozenset(
        {LifecycleState.MONITORING, LifecycleState.COMPLETED, LifecycleState.FAILED}
    ),
    LifecycleState.REJECTED: frozenset(
        {LifecycleState.MONITORING, LifecycleState.COMPLETED, LifecycleState.FAILED}
    ),
    LifecycleState.COMPLETED: frozenset({LifecycleState.IDLE}),
    LifecycleState.FAILED: frozenset({LifecycleState.IDLE, LifecycleState.MONITORING}),
}


def can_transition(src: LifecycleState, dst: LifecycleState) -> bool:
    """Return True if ``src → dst`` is allowed."""
    return dst in ALLOWED_TRANSITIONS.get(src, frozenset())
