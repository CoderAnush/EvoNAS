"""CLI / use-case smoke for continuous learning (Phase 7)."""

from __future__ import annotations

import json
from pathlib import Path

from evonas.application.closed_loop.controller import ClosedLoopController
from evonas.application.continuous.use_cases import ContinuousLearningUseCase
from evonas.domain.continuous.engine import ContinuousLearningEngine
from evonas.domain.continuous.events import LearningRecommendation
from evonas.domain.continuous.policy import LearningPolicy
from evonas.presentation.cli.main import main
import numpy as np


def test_learn_usecase(tmp_path: Path) -> None:
    summary = ContinuousLearningUseCase().learn(
        "configs/continuous_learning/default.yaml",
        output_dir=tmp_path / "cl",
        cycles=2,
    )
    assert summary["cycles"] == 2
    assert summary["last_recommendation"] is not None
    assert Path(summary["run_dir"], "learning_history.json").exists()
    assert "observation" in summary


def test_detect_and_replay_cli(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "detect-data",
            "--config",
            "configs/continuous_learning/default.yaml",
            "--out",
            str(tmp_path / "detect"),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["change_report"]["has_changes"] is True

    learn = ContinuousLearningUseCase().learn(
        "configs/continuous_learning/default.yaml",
        output_dir=tmp_path / "learn",
        cycles=2,
    )
    history = Path(learn["run_dir"]) / "learning_history.json"
    code2 = main(
        ["replay-learning", "--history", str(history), "--out", str(tmp_path / "replay")]
    )
    assert code2 == 0
    replayed = json.loads(capsys.readouterr().out)
    assert replayed["steps"] >= 1


def test_learn_cli(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "learn",
            "--config",
            "configs/continuous_learning/default.yaml",
            "--out",
            str(tmp_path / "cli_learn"),
            "--cycles",
            "2",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["simulate"] is True


def test_controller_consumes_cl_observation(tmp_path: Path) -> None:
    """ClosedLoopController reads CL via published to_observation() only."""
    cl = ContinuousLearningEngine(
        artifacts_root=tmp_path / "cl_versions",
        policy=LearningPolicy(min_new_samples=5, max_drift_psi=0.1),
        seed=11,
    )
    rng = np.random.default_rng(11)
    ref_x, ref_y = rng.normal(size=(40, 3)), rng.integers(0, 2, size=(40,))
    cl.run_cycle(candidate_features=ref_x, candidate_labels=ref_y)
    cand_x = ref_x + 3.0
    cand_y = ref_y
    cl.run_cycle(
        reference_features=ref_x,
        reference_labels=ref_y,
        candidate_features=np.concatenate([ref_x, cand_x[:20]], axis=0),
        candidate_labels=np.concatenate([ref_y, cand_y[:20]], axis=0),
    )
    assert cl.last_result is not None

    cfg = {
        "run_id": "cl_hook",
        "seed": 1,
        "simulate": True,
        "policy": {
            "force_initial_search": False,
            "max_optimizations": 1,
            "accuracy_floor": 0.0,
            "cooldown_hours": 0.0,
            "min_improvement_abs": 0.01,
        },
        "closed_loop": {"max_cycles": 1},
        "triggers": {"schedule_on_first_cycle": False, "drift_based": True},
        "baseline": {"accuracy": 0.9, "metrics": {"accuracy": 0.9}},
        "observation": {},
        "search_space": {"path": "configs/search_spaces/sphere_2d.yaml"},
        "optimization": {
            "algorithm": "sapso",
            "swarm_size": 4,
            "max_iterations": 2,
            "log_particles": False,
        },
        "fitness": {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
        "experiment": {"artifacts_root": str(tmp_path / "loop")},
    }
    ctrl = ClosedLoopController(
        cfg,
        simulate=True,
        dry_run=True,
        output_dir=tmp_path / "loop",
        continuous_learning=cl,
    )
    # Observe path should pick up CL drift_status
    ctx = ctrl._observe()  # noqa: SLF001 — integration assertion
    assert ctx.drift_status in {"none", "mild", "significant"}
    assert ctx.experiment_metadata.get("cl_recommendation") in {
        r.value for r in LearningRecommendation
    }
