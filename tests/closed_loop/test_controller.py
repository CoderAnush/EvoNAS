"""Closed-loop controller, workflow, simulation, and CLI tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evonas.application.closed_loop.controller import ClosedLoopController
from evonas.application.closed_loop.use_cases import (
    InspectClosedLoopUseCase,
    RunClosedLoopUseCase,
)
from evonas.domain.common.errors import DecisionError
from evonas.domain.lifecycle.states import LifecycleState
from evonas.presentation.cli.main import main


def _base_cfg(**overrides: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "run_id": "test_loop",
        "seed": 1,
        "simulate": True,
        "policy": {
            "force_initial_search": True,
            "max_optimizations": 2,
            "min_improvement_abs": 0.005,
            "allow_deploy": False,
            "cooldown_hours": 0.0,
            "accuracy_floor": 0.0,
        },
        "closed_loop": {"max_cycles": 1},
        "triggers": {"schedule_on_first_cycle": True},
        "baseline": {"accuracy": 0.50, "metrics": {"accuracy": 0.50}},
        "candidate_metrics_override": {"accuracy": 0.60},
        "search_space": {"path": "configs/search_spaces/sphere_2d.yaml"},
        "optimization": {
            "algorithm": "sapso",
            "swarm_size": 4,
            "max_iterations": 2,
            "log_particles": False,
        },
        "adaptation": {
            "inertia": {"w_min": 0.4, "w_max": 0.9, "alpha": 0.5, "beta": 0.3, "gamma": 0.2},
            "acceleration": {"c_min": 0.5, "c_max": 2.5, "c_sum": 4.1},
            "stagnation_iters": 4,
        },
        "fitness": {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
        "experiment": {"artifacts_root": "artifacts/closed_loop_test"},
    }
    cfg.update(overrides)
    return cfg


def test_simulate_loop_accepts_and_records(tmp_path: Path) -> None:
    cfg = _base_cfg()
    cfg["experiment"] = {"artifacts_root": str(tmp_path)}
    ctrl = ClosedLoopController(cfg, simulate=True, dry_run=True, output_dir=tmp_path)
    summary = ctrl.run(max_cycles=1)
    assert summary["optimizations_used"] == 1
    assert summary["state"] == LifecycleState.COMPLETED.value
    assert summary["promotions"]
    assert summary["promotions"][0]["accepted"] is True
    assert (Path(summary["run_dir"]) / "lifecycle_history.json").exists()
    assert (Path(summary["run_dir"]) / "decisions.jsonl").exists()
    assert (Path(summary["run_dir"]) / "lifecycle_transitions.csv").exists()
    assert ctrl.history.transitions
    assert any(d.get("question") == "should_start_optimization" for d in ctrl.history.decisions)


def test_skip_when_no_trigger(tmp_path: Path) -> None:
    cfg = _base_cfg(
        policy={
            "force_initial_search": False,
            "max_optimizations": 2,
            "min_improvement_abs": 0.005,
            "accuracy_floor": 0.0,
            "cooldown_hours": 0.0,
        },
        triggers={"schedule_on_first_cycle": False, "manual": True},
        observation={"force_optimization": False, "drift_status": "none"},
        experiment={"artifacts_root": str(tmp_path)},
    )
    # clear override that would not matter for start
    ctrl = ClosedLoopController(cfg, simulate=True, dry_run=True, output_dir=tmp_path)
    # Corrupt baseline above any floor and no triggers
    one = ctrl.run_once()
    assert one["optimized"] is False
    assert ctrl.state == LifecycleState.MONITORING


def test_reject_insufficient_improvement(tmp_path: Path) -> None:
    cfg = _base_cfg(
        candidate_metrics_override={"accuracy": 0.501},
        policy={
            "force_initial_search": True,
            "max_optimizations": 2,
            "min_improvement_abs": 0.05,
            "accuracy_floor": 0.0,
            "cooldown_hours": 0.0,
        },
        experiment={"artifacts_root": str(tmp_path)},
        baseline={"accuracy": 0.50, "metrics": {"accuracy": 0.50}},
    )
    ctrl = ClosedLoopController(cfg, simulate=True, dry_run=True, output_dir=tmp_path)
    summary = ctrl.run(max_cycles=1)
    assert summary["promotions"][0]["accepted"] is False
    assert summary["current_model_id"] == "baseline_local"


def test_illegal_transition_raises() -> None:
    cfg = _base_cfg()
    ctrl = ClosedLoopController(cfg, simulate=True, dry_run=True)
    with pytest.raises(DecisionError):
        ctrl.transition(LifecycleState.OPTIMIZING, "bad")


def test_failure_recovery(tmp_path: Path) -> None:
    class BoomOptimize:
        def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("boom")

    cfg = _base_cfg(experiment={"artifacts_root": str(tmp_path)})
    ctrl = ClosedLoopController(
        cfg,
        simulate=True,
        dry_run=True,
        output_dir=tmp_path,
        optimize_use_case=BoomOptimize(),  # type: ignore[arg-type]
    )
    result = ctrl.run_once()
    assert result.get("error")
    assert ctrl.state == LifecycleState.MONITORING
    assert any(e.get("kind") == "failure" for e in ctrl.history.events)


def test_use_case_simulate_yaml(tmp_path: Path) -> None:
    summary = RunClosedLoopUseCase().run(
        "configs/closed_loop/simulate.yaml",
        output_dir=tmp_path / "sim",
        simulate=True,
        dry_run=True,
        max_cycles=1,
    )
    assert summary["simulate"] is True
    assert summary["algorithm"] == "sapso"
    payload = InspectClosedLoopUseCase().inspect(summary["run_dir"])
    assert payload["decision_count"] >= 1


def test_cli_simulate_and_inspect(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "simulate-loop",
            "--config",
            "configs/closed_loop/simulate.yaml",
            "--out",
            str(tmp_path / "cli_sim"),
            "--max-cycles",
            "1",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["optimizations_used"] >= 1
    code2 = main(["inspect-loop", "--run-dir", summary["run_dir"]])
    assert code2 == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["transition_count"] >= 1


def test_cli_run_loop_dry(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "run-loop",
            "--config",
            "configs/closed_loop/default.yaml",
            "--out",
            str(tmp_path / "cli_run"),
            "--dry-run",
            "--max-cycles",
            "1",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["dry_run"] is True


def test_standard_pso_selectable(tmp_path: Path) -> None:
    cfg = _base_cfg(
        experiment={"artifacts_root": str(tmp_path)},
        optimization={
            "algorithm": "pso",
            "swarm_size": 4,
            "max_iterations": 2,
            "log_particles": False,
        },
    )
    ctrl = ClosedLoopController(cfg, simulate=True, dry_run=True, output_dir=tmp_path)
    summary = ctrl.run(max_cycles=1)
    assert summary["algorithm"] == "pso"
    opt = summary["cycle_summaries"][0]["optimization"]
    assert opt["algorithm"] == "standard_pso"
