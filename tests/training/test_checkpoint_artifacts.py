"""Checkpoint and artifact manager tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from evonas.infrastructure.checkpoint import FileCheckpointManager
from evonas.infrastructure.experiments import ArtifactManager


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    import torch

    mgr = FileCheckpointManager(tmp_path / "ckpts")
    uri = mgr.save("latest", {"model_state": {"w": torch.tensor([1.0])}, "epoch": 1})
    loaded = mgr.load(uri)
    assert loaded["epoch"] == 1
    assert "latest" in "".join(mgr.list())


def test_artifact_manager_creates_layout(tmp_path: Path) -> None:
    arts = ArtifactManager(tmp_path / "baselines")
    run = arts.create_run("run_test")
    assert (run / "checkpoints").is_dir()
    path = arts.write_json(run, "metrics.json", {"accuracy": 0.9})
    assert path.exists()
