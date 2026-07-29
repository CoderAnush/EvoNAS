"""Trigger, validation, promotion, lifecycle state tests."""

from __future__ import annotations

from evonas.domain.decision.context import BudgetSnapshot, DecisionContext
from evonas.domain.decision.policies import DecisionPolicy
from evonas.domain.lifecycle.states import LifecycleState, can_transition
from evonas.domain.promotion.manager import PromotionManager
from evonas.domain.trigger.optimization_trigger import OptimizationTrigger, TriggerConfig
from evonas.domain.validation.engine import ValidationEngine


def test_allowed_transitions() -> None:
    assert can_transition(LifecycleState.IDLE, LifecycleState.MONITORING)
    assert can_transition(LifecycleState.DECISION, LifecycleState.OPTIMIZING)
    assert can_transition(LifecycleState.VALIDATION, LifecycleState.ACCEPTED)
    assert can_transition(LifecycleState.VALIDATION, LifecycleState.REJECTED)
    assert not can_transition(LifecycleState.IDLE, LifecycleState.OPTIMIZING)


def test_trigger_drift_and_budget() -> None:
    trig = OptimizationTrigger(
        DecisionPolicy(force_initial_search=False, accuracy_floor=0.0),
        TriggerConfig(schedule_on_first_cycle=False),
    )
    ctx = DecisionContext(
        drift_status="significant",
        budgets=BudgetSnapshot(max_optimizations=3, optimizations_used=0),
        current_metrics={"accuracy": 0.9},
    )
    d = trig.evaluate(ctx)
    assert d.consider is True
    assert "drift_significant" in d.reasons

    exhausted = DecisionContext(
        force_optimization=True,
        budgets=BudgetSnapshot(max_optimizations=1, optimizations_used=1),
    )
    out = trig.evaluate(exhausted)
    assert out.consider is False
    assert "budget_exhausted" in out.reasons


def test_validation_engine_thresholds() -> None:
    eng = ValidationEngine(
        DecisionPolicy(min_improvement_abs=0.01, max_complexity_params=1000)
    )
    ok = eng.validate(
        current_metrics={"accuracy": 0.5},
        candidate_metrics={"accuracy": 0.55},
        complexity_params=100,
    )
    assert ok.accepted is True
    bad = eng.validate(
        current_metrics={"accuracy": 0.5},
        candidate_metrics={"accuracy": 0.505},
        complexity_params=5000,
    )
    assert bad.accepted is False
    assert "complexity_exceeded" in bad.reasons


def test_promotion_manager() -> None:
    mgr = PromotionManager()
    a = mgr.accept("m2", previous_model_id="m1", reason="better", metrics={"accuracy": 0.7})
    assert a.accepted is True
    assert mgr.current_model_id == "m2"
    assert a.deployment_prepared is True
    r = mgr.reject("m3", previous_model_id="m2", reason="worse")
    assert r.accepted is False
    assert mgr.current_model_id == "m2"
    assert len(mgr.history) == 2
