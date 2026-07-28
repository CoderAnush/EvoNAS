"""Tests for transforms, statistics, and validator."""

from __future__ import annotations

import numpy as np
import pytest

from evonas.domain.common.enums import Split, TaskType
from evonas.domain.common.errors import DataError
from evonas.domain.data.models import DatasetHandle, Schema
from evonas.domain.data.statistics import compute_data_stats
from evonas.domain.data.transforms import TransformConfig, TransformPipeline
from evonas.domain.data.validator import DatasetValidator


def test_normalize_pipeline_bounds() -> None:
    pipe = TransformPipeline(TransformConfig(normalize=True, flatten=False))
    x = np.arange(32, dtype=np.float32).reshape(2, 4, 4, 1)
    out = pipe.apply(x)
    assert out.shape == x.shape
    assert out.min() >= 0.0 - 1e-5
    assert out.max() <= 1.0 + 1e-5


def test_compute_stats_label_histogram() -> None:
    features = np.random.default_rng(0).normal(size=(50, 4))
    labels = np.array([0] * 20 + [1] * 30)
    stats = compute_data_stats(features, labels, split=Split.TRAIN, checksum="x", feature_bins=5)
    assert stats.n_samples == 50
    assert stats.label_histogram[0] == 20
    assert stats.label_histogram[1] == 30
    assert len(stats.flattened_histogram) == 5


def test_validator_split_disjointness() -> None:
    v = DatasetValidator()
    a = np.array([0, 1, 2])
    b = np.array([3, 4])
    c = np.array([5, 6])
    assert v.validate_split_disjointness({Split.TRAIN: a, Split.VAL: b, Split.TEST: c}).ok
    bad = v.validate_split_disjointness(
        {Split.TRAIN: a, Split.VAL: np.array([2, 9]), Split.TEST: c}
    )
    assert not bad.ok
    with pytest.raises(DataError):
        v.require_ok(bad)


def test_validator_handle_feature_dim() -> None:
    schema = Schema(
        name="t",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(2, 2, 1),
        num_classes=2,
        dtype="float32",
        feature_dim=4,
    )
    handle = DatasetHandle(
        split=Split.TRAIN,
        features=np.zeros((3, 2, 2, 1), dtype=np.float32),
        labels=np.array([0, 1, 0]),
        indices=np.arange(3),
        schema=schema,
        checksum="z",
    )
    assert DatasetValidator().validate_handle(handle).ok
