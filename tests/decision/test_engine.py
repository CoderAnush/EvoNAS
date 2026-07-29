"""DecisionEngine and policy unit tests."""

from __future__ import annotations

from pathlib import Path

from evonas.domain.decision.context import BudgetSnapshot, DecisionContext
from evonas.domain.decision.engine import DecisionEngine
from evonas.domain.decision.policies import DecisionPolicy


def _ctx(**kwargs) -> DecisionContext:
    base = dict(
        current_metrics={"accuracy": 0.55},
        best_metrics={"accuracy": 0.55},
        budgets=BudgetSnapshot(max_optimizations=3, optimizations_used=0),
        trigger_consider=True,
        trigger_reasons=("manual",),
    )
    base.update(kwargs)
    return DecisionContext(**base)


def test_policy_from_yaml() -> None:
    policy = DecisionPolicy.from_yaml("configs/policies/default_policy.yaml")
    assert policy.policy_version == "1.0.0"
    assert policy.allow_deploy is False
    assert policy.max_optimizations == 3


def test_should_start_when_triggered() -> None:
    eng = DecisionEngine(DecisionPolicy(force_initial_search=False, accuracy_floor=0.0))
    rec = eng.should_start_optimization(_ctx())
    assert rec.outcome is True
    assert rec.action == "START_OPTIMIZATION"


def test_cooldown_blocks_start() -> None:
    eng = DecisionEngine(DecisionPolicy(cooldown_hours=2.0, force_initial_search=False))
    ctx = _ctx(
        budgets=BudgetSnapshot(
            max_optimizations=3,
            optimizations_used=1,
            cooldown_hours=2.0,
            hours_since_last_optimization=0.5,
        ),
        trigger_consider=True,
    )
    rec = eng.should_start_optimization(ctx)
    assert rec.outcome is False
    assert rec.rationale["reason"] == "cooldown"


def test_budget_exhausted() -> None:
    eng = DecisionEngine(DecisionPolicy(max_optimizations=1, force_initial_search=False))
    ctx = _ctx(
        budgets=BudgetSnapshot(max_optimizations=1, optimizations_used=1),
        trigger_consider=True,
    )
    rec = eng.should_start_optimization(ctx)
    assert rec.outcome is False
    assert rec.rationale["reason"] == "budget_exhausted"


def test_accept_candidate_min_improvement() -> None:
    eng = DecisionEngine(DecisionPolicy(min_improvement_abs=0.01))
    ctx = _ctx(
        candidate_model_id="c1",
        candidate_metrics={"accuracy": 0.58},
        current_metrics={"accuracy": 0.55},
    )
    yes = eng.should_accept_candidate(ctx)
    assert yes.outcome is True
    no = eng.should_accept_candidate(
        _ctx(
            candidate_model_id="c2",
            candidate_metrics={"accuracy": 0.552},
            current_metrics={"accuracy": 0.55},
        )
    )
    assert no.outcome is False


def test_deploy_and_rollback_gated() -> None:
    eng = DecisionEngine(DecisionPolicy(allow_deploy=False, allow_rollback=False))
    ctx = _ctx(candidate_model_id="c1", candidate_metrics={"accuracy": 0.9})
    assert eng.should_deploy(ctx).outcome is False
    assert "phase_8" in eng.should_deploy(ctx).rationale["reason"]
    assert eng.should_rollback(ctx).outcome is False


def test_decision_context_roundtrip() -> None:
    ctx = _ctx(dataset_version="toy", drift_status="significant")
    restored = DecisionContext.from_dict(ctx.to_dict())
    assert restored.drift_status == "significant"
    assert restored.budgets.max_optimizations == 3


def test_policy_nested_dict(tmp_path: Path) -> None:
    path = tmp_path / "p.yaml"
    path.write_text(
        "policy_version: '9.9'\nbudgets:\n  max_optimizations: 5\n",
        encoding="utf-8",
    )
    policy = DecisionPolicy.from_yaml(path)
    assert policy.policy_version == "9.9"
    assert policy.max_optimizations == 5
