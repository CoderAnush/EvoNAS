"""Architecture validator and factory tests."""

from __future__ import annotations

import pytest

from evonas.domain.architecture.constraints import ArchitectureValidator
from evonas.domain.architecture.factory import ArchitectureFactory
from evonas.domain.architecture.layers import dense
from evonas.domain.common.enums import TaskType
from evonas.domain.common.errors import ArchitectureError
from evonas.domain.model.architecture_spec import ArchitectureSpec


def test_factory_baseline_and_random() -> None:
    factory = ArchitectureFactory()
    baseline = factory.baseline()
    assert baseline.name == "baseline_cnn"
    assert ArchitectureValidator().validate(baseline).ok

    random_spec = factory.random(seed=7, n_conv=1, n_dense=1)
    assert ArchitectureValidator().validate(random_spec).ok
    assert random_spec.layers


def test_factory_from_yaml_configs() -> None:
    factory = ArchitectureFactory()
    for path in (
        "configs/models/baseline.yaml",
        "configs/models/baseline_cnn.yaml",
        "configs/models/future_template.yaml",
    ):
        spec = factory.from_yaml(path)
        assert ArchitectureValidator().validate(spec).ok


def test_validator_rejects_bad_activation() -> None:
    from evonas.domain.architecture.layers import LayerSpec

    bad = ArchitectureSpec(
        name="bad",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        layers=(
            LayerSpec("activation", {"name": "not_a_real_act"}),
            dense(3),
        ),
    )
    result = ArchitectureValidator().validate(bad)
    assert not result.ok
    assert any("activation" in e for e in result.errors)


def test_validator_rejects_dropout_range() -> None:
    from evonas.domain.architecture.layers import LayerSpec

    bad = ArchitectureSpec(
        name="drop",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(4,),
        num_classes=2,
        layers=(dense(8), LayerSpec("dropout", {"rate": 1.5}), dense(2)),
    )
    result = ArchitectureValidator().validate(bad)
    assert not result.ok


def test_require_valid_raises() -> None:
    bad = ArchitectureSpec(
        name="",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=1,
        layers=(dense(1),),
    )
    with pytest.raises(ArchitectureError):
        ArchitectureValidator().require_valid(bad)
