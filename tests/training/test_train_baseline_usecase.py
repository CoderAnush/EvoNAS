"""End-to-end baseline use-case smoke (short)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def test_train_baseline_use_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("torch")
    from evonas.application.train_baseline import TrainBaselineUseCase

    # Point artifacts into tmp
    cfg = {
        "run_id": "test_baseline_run",
        "seed": 3,
        "dataset": {"config_path": "configs/datasets/toy_quick.yaml"},
        "model": {
            "architecture_path": "configs/models/baseline_cnn.yaml",
            "align_with_dataset": True,
            "backend": "pytorch",
        },
        "data": {"subset_fraction": 0.25, "subset_seed": 3},
        "training": {
            "epochs": 3,
            "batch_size": 32,
            "learning_rate": 0.01,
            "optimizer": "adam",
            "device": "cpu",
            "seed": 3,
            "checkpoint_every": 1,
            "num_workers": 0,
        },
    }
    cfg_path = tmp_path / "train.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    use_case = TrainBaselineUseCase()
    # Redirect ArtifactManager root via monkeypatch on instance
    use_case._artifacts = __import__(
        "evonas.infrastructure.experiments.artifact_manager", fromlist=["ArtifactManager"]
    ).ArtifactManager(tmp_path / "baselines")
    use_case._recorder = __import__(
        "evonas.infrastructure.experiments.experiment_recorder", fromlist=["ExperimentRecorder"]
    ).ExperimentRecorder(use_case._artifacts)

    summary = use_case.run(cfg_path)
    assert summary["epochs_ran"] == 3
    assert Path(summary["metrics_path"]).exists()
    assert "test_accuracy" in summary
