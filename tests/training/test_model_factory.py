"""Model factory and ArchitectureSpec tests."""

from __future__ import annotations

import pytest

from evonas.domain.common.enums import TaskType
from evonas.domain.model import ArchitectureSpec, ConvBlockSpec
from evonas.infrastructure.training.model_factory import ModelFactory
from evonas.ports.training import ITrainableModel


@pytest.fixture
def tiny_spec() -> ArchitectureSpec:
    return ArchitectureSpec(
        name="tiny",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        conv_blocks=(ConvBlockSpec(out_channels=8, kernel=3, pool=2),),
        dense_units=(16,),
        dropout=0.0,
    )


def test_arch_id_stable(tiny_spec: ArchitectureSpec) -> None:
    assert tiny_spec.arch_id() == ArchitectureSpec.from_dict(tiny_spec.to_dict()).arch_id()


def test_factory_builds_trainable_model(tiny_spec: ArchitectureSpec) -> None:
    pytest.importorskip("torch")
    model, spec = ModelFactory().create(tiny_spec)
    assert isinstance(model, ITrainableModel)
    assert spec.name == "tiny"
    assert ModelFactory().builder().count_parameters(model) > 0


def test_factory_loads_baseline_yaml() -> None:
    pytest.importorskip("torch")
    model, spec = ModelFactory().create("configs/models/baseline_cnn.yaml")
    assert spec.name == "baseline_cnn"
    assert isinstance(model, ITrainableModel)
