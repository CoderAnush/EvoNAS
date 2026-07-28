"""Trainer / evaluator integration tests (CPU)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from evonas.domain.common.enums import Split, TaskType
from evonas.domain.data.models import DatasetHandle, Schema
from evonas.domain.model import ArchitectureSpec, ConvBlockSpec
from evonas.domain.training.types import TrainConfig
from evonas.infrastructure.checkpoint import FileCheckpointManager
from evonas.infrastructure.training import (
    ModelFactory,
    PyTorchEvaluationEngine,
    PyTorchTrainingEngine,
)
from evonas.ports.training import IEvaluationEngine, ITrainingEngine


def _toy_handle(n: int = 64, seed: int = 0) -> DatasetHandle:
    rng = np.random.default_rng(seed)
    # Strong class signal so a tiny CNN can overfit quickly.
    labels = rng.integers(0, 3, size=n, dtype=np.int64)
    feats = rng.normal(0.0, 0.05, size=(n, 8, 8, 1)).astype(np.float32)
    for i, y in enumerate(labels):
        feats[i] += 0.4 * float(y)
    schema = Schema(
        name="toy",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        dtype="float32",
        feature_dim=64,
    )
    return DatasetHandle(
        split=Split.TRAIN,
        features=feats,
        labels=labels,
        indices=np.arange(n),
        schema=schema,
        checksum="x",
    )


@pytest.fixture
def tiny_spec() -> ArchitectureSpec:
    return ArchitectureSpec(
        name="tiny_baseline",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        conv_blocks=(
            ConvBlockSpec(out_channels=8, kernel=3, pool=2),
            ConvBlockSpec(out_channels=16, kernel=3, pool=2),
        ),
        dense_units=(32,),
        dropout=0.0,
    )


def test_engines_satisfy_ports(tiny_spec: ArchitectureSpec, tmp_path: Path) -> None:
    pytest.importorskip("torch")
    trainer = PyTorchTrainingEngine(checkpoint_manager=FileCheckpointManager(tmp_path / "c"))
    evaluator = PyTorchEvaluationEngine()
    assert isinstance(trainer, ITrainingEngine)
    assert isinstance(evaluator, IEvaluationEngine)


def test_overfit_tiny_subset(tiny_spec: ArchitectureSpec, tmp_path: Path) -> None:
    """idea.md Phase 2 gate: overfit tiny subset → high accuracy on CPU."""
    pytest.importorskip("torch")
    train = _toy_handle(80, seed=1)
    val = _toy_handle(20, seed=2)
    cfg = TrainConfig(
        epochs=25,
        batch_size=16,
        learning_rate=0.01,
        device="cpu",
        seed=1,
        checkpoint_every=5,
    )
    trainer = PyTorchTrainingEngine(
        checkpoint_manager=FileCheckpointManager(tmp_path / "ckpts"),
    )
    artifact = trainer.train(tiny_spec, train, val, cfg, run_context={})
    assert artifact.epochs_ran >= 1
    assert artifact.train_metrics.values["accuracy"] >= 0.85
    assert Path(artifact.best_weights_uri).exists()


def test_evaluator_returns_structured_metrics(tiny_spec: ArchitectureSpec) -> None:
    pytest.importorskip("torch")
    model, _ = ModelFactory().create(tiny_spec)
    data = _toy_handle(30, seed=3)
    result = PyTorchEvaluationEngine().evaluate(model, data, device="cpu", batch_size=8)
    assert result.n_samples == 30
    assert "accuracy" in result.metrics.values
    assert "f1_macro" in result.metrics.values
    assert len(result.confusion_matrix) == 3
