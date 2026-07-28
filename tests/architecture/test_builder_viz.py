"""Dynamic builder and visualization tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from evonas.domain.architecture.complexity import estimate_complexity
from evonas.domain.architecture.factory import ArchitectureFactory
from evonas.domain.architecture.visualization import ArchitectureVisualizer
from evonas.infrastructure.training.model_factory import ModelFactory
from evonas.infrastructure.training.pytorch_builder import PyTorchModelBuilder
from evonas.ports.training import ITrainableModel


def test_builder_from_baseline_yaml() -> None:
    pytest.importorskip("torch")
    import torch

    model, spec = ModelFactory().create("configs/models/baseline.yaml")
    assert isinstance(model, ITrainableModel)
    x = torch.randn(2, 8, 8, 1)
    logits = model(x)
    assert tuple(logits.shape) == (2, 3)
    assert estimate_complexity(spec).estimated_params > 0


def test_builder_legacy_phase2_yaml() -> None:
    pytest.importorskip("torch")
    model, spec = ModelFactory().create("configs/models/baseline_cnn.yaml")
    assert isinstance(model, ITrainableModel)
    assert spec.depth >= 1
    assert PyTorchModelBuilder().count_parameters(model) > 0


def test_builder_random_architecture() -> None:
    pytest.importorskip("torch")
    import torch

    spec = ArchitectureFactory().random(seed=3, n_conv=2, n_dense=1)
    model = PyTorchModelBuilder().build(spec)
    logits = model(torch.randn(4, 8, 8, 1))
    assert tuple(logits.shape) == (4, 3)


def test_visualizer_export(tmp_path: Path) -> None:
    spec = ArchitectureFactory().baseline()
    out = tmp_path / "summary.txt"
    text = ArchitectureVisualizer().export_text(spec, str(out))
    assert "Dense" in text or "Conv2D" in text
    assert out.read_text(encoding="utf-8").strip() == text.strip()
