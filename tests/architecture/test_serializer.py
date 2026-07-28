"""Architecture serialization / equality / hashing tests."""

from __future__ import annotations

import json
from pathlib import Path

from evonas.domain.architecture.factory import ArchitectureFactory
from evonas.domain.architecture.serializer import ArchitectureSerializer
from evonas.domain.common.enums import TaskType
from evonas.domain.model.architecture_spec import ArchitectureSpec, ConvBlockSpec


def test_json_yaml_roundtrip(tmp_path: Path) -> None:
    factory = ArchitectureFactory()
    spec = factory.baseline()
    ser = ArchitectureSerializer()

    json_path = tmp_path / "arch.json"
    yaml_path = tmp_path / "arch.yaml"
    ser.save(spec, json_path)
    ser.save(spec, yaml_path)

    loaded_json = ser.load(json_path)
    loaded_yaml = ser.load(yaml_path)
    assert loaded_json == spec
    assert loaded_yaml == spec
    assert loaded_json.arch_id() == spec.arch_id()


def test_dict_roundtrip_and_hash() -> None:
    ser = ArchitectureSerializer()
    spec = ArchitectureFactory().baseline()
    restored = ser.from_dict(ser.to_dict(spec))
    assert restored == spec
    assert hash(restored) == hash(spec)
    # JSON string stability for core fields
    blob = json.loads(ser.to_json(spec))
    assert blob["name"] == "baseline_cnn"


def test_legacy_phase2_equals_explicit_layers() -> None:
    legacy = ArchitectureSpec(
        name="legacy",
        version="1.0.0",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        conv_blocks=(
            ConvBlockSpec(out_channels=16, kernel=3, activation="relu", pool=2),
            ConvBlockSpec(out_channels=32, kernel=3, activation="relu", pool=2),
        ),
        dense_units=(64,),
        dropout=0.1,
        schema_version="2.0",
    )
    explicit = ArchitectureFactory().baseline(name="legacy")
    # Same resolved layer structure → same arch_id when names match and layers align
    assert legacy.resolved_layers() == explicit.resolved_layers()
    assert legacy.arch_id() == explicit.arch_id()
