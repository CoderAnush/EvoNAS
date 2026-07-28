"""DatasetManager integration / contract tests (Phase 1 gates)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from evonas.domain.common.enums import Split
from evonas.domain.common.errors import DataError
from evonas.domain.data.models import DatasetHandle
from evonas.infrastructure.data import DatasetManager
from evonas.ports.dataset import IDatasetManager


def test_dataset_manager_satisfies_port(toy_config: dict) -> None:
    assert isinstance(DatasetManager(toy_config), IDatasetManager)


def test_prepare_load_checksum_stable(toy_config: dict) -> None:
    mgr1 = DatasetManager(toy_config)
    mgr1.prepare()
    c1 = mgr1.checksums()
    mgr2 = DatasetManager(toy_config)
    mgr2.prepare()
    assert c1 == mgr2.checksums()


def test_split_disjointness(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    mgr.prepare()
    train, val, test = mgr.load(Split.TRAIN), mgr.load(Split.VAL), mgr.load(Split.TEST)
    assert len(np.intersect1d(train.indices, val.indices)) == 0
    assert len(np.intersect1d(train.indices, test.indices)) == 0
    assert len(np.intersect1d(val.indices, test.indices)) == 0
    assert train.size + val.size + test.size == toy_config["num_samples"]


def test_deterministic_shuffle_seed(toy_config: dict) -> None:
    a, b = DatasetManager(toy_config), DatasetManager(toy_config)
    a.prepare()
    b.prepare()
    assert np.array_equal(a.load(Split.TRAIN).indices, b.load(Split.TRAIN).indices)


def test_window_correctness(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    train = mgr.load(Split.TRAIN)
    window = mgr.get_window(0, 10, split=Split.TRAIN)
    assert window.size == 10
    assert window.window_id == "train:0:10"
    assert np.array_equal(window.indices, train.indices[0:10])


def test_empty_window_raises(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    mgr.prepare()
    with pytest.raises(DataError) as exc:
        mgr.get_window(5, 5, split=Split.TRAIN)
    assert "EN_DATA_002" in str(exc.value)


def test_subset_fraction(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    train = mgr.load(Split.TRAIN)
    sub = mgr.subset(Split.TRAIN, 0.5, seed=3)
    assert 0 < sub.size <= train.size
    assert np.array_equal(sub.indices, mgr.subset(Split.TRAIN, 0.5, seed=3).indices)


def test_manifest_written(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    mgr.prepare()
    path = Path(toy_config["manifest_dir"]) / "manifest.json"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "raw_features" in text
    assert "checksums" in text


def test_statistics_and_schema(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    schema = mgr.get_schema()
    assert schema.num_classes == 3
    assert schema.input_shape == (4, 4, 1)
    stats = mgr.compute_statistics(Split.TRAIN)
    assert stats.n_samples == mgr.load(Split.TRAIN).size


def test_drift_fires_on_shifted_handle(toy_config: dict) -> None:
    mgr = DatasetManager(toy_config)
    train = mgr.load(Split.TRAIN)
    shifted = DatasetHandle(
        split=Split.VAL,
        features=train.features + 2.5,
        labels=train.labels.copy(),
        indices=train.indices.copy(),
        schema=train.schema,
        checksum="shifted",
    )
    assert mgr.detect_shift(train, shifted).significant is True


def test_prepare_from_yaml_path(toy_config_path: Path) -> None:
    mgr = DatasetManager(toy_config_path)
    mgr.prepare()
    assert mgr.load("train").size > 0
