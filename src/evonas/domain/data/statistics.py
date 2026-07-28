"""Dataset statistics computation for drift reference and observability."""

from __future__ import annotations

import logging

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.data.models import DataStats

logger = logging.getLogger(__name__)


def flatten_features(features: np.ndarray) -> np.ndarray:
    """Flatten NCHW/NHWC/feature tensors to (N, D) then ravel for histograms."""
    arr = np.asarray(features)
    if arr.ndim == 1:
        return arr.astype(np.float64, copy=False)
    return arr.reshape(arr.shape[0], -1).astype(np.float64, copy=False)


def compute_data_stats(
    features: np.ndarray,
    labels: np.ndarray,
    *,
    split: Split,
    checksum: str,
    feature_bins: int = 10,
) -> DataStats:
    """Compute per-feature moments, label histogram, and flattened value histogram."""
    if feature_bins < 2:
        raise ValueError("feature_bins must be >= 2")

    flat = flatten_features(features)
    if flat.ndim == 1:
        # Single vector — treat as one sample with D features if needed
        flat_2d = flat.reshape(1, -1)
    else:
        flat_2d = flat

    feature_mean = tuple(float(x) for x in flat_2d.mean(axis=0))
    feature_std = tuple(float(x) for x in flat_2d.std(axis=0))
    feature_min = tuple(float(x) for x in flat_2d.min(axis=0))
    feature_max = tuple(float(x) for x in flat_2d.max(axis=0))

    labels_i = np.asarray(labels).astype(np.int64, copy=False).ravel()
    unique, counts = np.unique(labels_i, return_counts=True)
    label_histogram = {int(k): int(v) for k, v in zip(unique, counts, strict=True)}

    values = flat_2d.ravel()
    hist, bin_edges = np.histogram(values, bins=feature_bins)

    stats = DataStats(
        split=split,
        n_samples=int(features.shape[0]),
        feature_mean=feature_mean,
        feature_std=feature_std,
        feature_min=feature_min,
        feature_max=feature_max,
        label_histogram=label_histogram,
        flattened_histogram=tuple(int(x) for x in hist.tolist()),
        bin_edges=tuple(float(x) for x in bin_edges.tolist()),
        checksum=checksum,
    )
    logger.debug(
        "Computed DataStats split=%s n=%d bins=%d",
        split.value,
        stats.n_samples,
        feature_bins,
    )
    return stats


def rebin_to_edges(
    values: np.ndarray, bin_edges: tuple[float, ...] | list[float]
) -> tuple[int, ...]:
    """Histogram `values` using fixed reference bin edges (for comparable PSI).

    Values outside the edge range are clipped into the outer bins so the
    histogram retains positive mass (required for PSI).
    """
    edges = np.asarray(bin_edges, dtype=np.float64)
    clipped = np.clip(
        np.asarray(values, dtype=np.float64).ravel(),
        edges[0],
        edges[-1],
    )
    hist, _ = np.histogram(clipped, bins=edges)
    return tuple(int(x) for x in hist.tolist())
