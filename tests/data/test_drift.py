"""Unit tests for drift math."""

from __future__ import annotations

import numpy as np
import pytest

from evonas.domain.common.enums import Split
from evonas.domain.data.drift import detect_shift, population_stability_index
from evonas.domain.data.models import DataStats
from evonas.domain.data.statistics import compute_data_stats, flatten_features, rebin_to_edges


def test_psi_zero_for_identical() -> None:
    hist = (10, 20, 30, 40)
    assert population_stability_index(hist, hist) == pytest.approx(0.0, abs=1e-9)


def test_psi_positive_for_shift() -> None:
    expected = (40, 30, 20, 10)
    actual = (10, 20, 30, 40)
    assert population_stability_index(expected, actual) > 0.1


def test_detect_shift_flags_synthetic_feature_shift() -> None:
    rng = np.random.default_rng(0)
    ref = rng.normal(0.0, 1.0, size=(200, 8))
    cur = rng.normal(3.0, 1.0, size=(200, 8))
    labels = np.zeros(200, dtype=np.int64)
    ref_stats = compute_data_stats(ref, labels, split=Split.TRAIN, checksum="r", feature_bins=10)
    cur_stats = compute_data_stats(cur, labels, split=Split.VAL, checksum="c", feature_bins=10)
    cur_stats = DataStats(
        split=cur_stats.split,
        n_samples=cur_stats.n_samples,
        feature_mean=cur_stats.feature_mean,
        feature_std=cur_stats.feature_std,
        feature_min=cur_stats.feature_min,
        feature_max=cur_stats.feature_max,
        label_histogram=cur_stats.label_histogram,
        flattened_histogram=rebin_to_edges(flatten_features(cur), ref_stats.bin_edges),
        bin_edges=ref_stats.bin_edges,
        checksum=cur_stats.checksum,
    )
    report = detect_shift(
        ref_stats,
        cur_stats,
        reference_features=ref,
        current_features=cur,
        psi_threshold=0.1,
        ks_p_threshold=0.01,
    )
    assert report.significant is True
    assert report.psi > 0.1 or report.ks_p_value < 0.01
