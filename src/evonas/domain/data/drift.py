"""Drift detection utilities (PSI + Kolmogorov–Smirnov)."""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from scipy import stats  # type: ignore[import-untyped]

from evonas.domain.data.models import DataStats, DriftReport

logger = logging.getLogger(__name__)

_EPS = 1e-12


def population_stability_index(
    expected_counts: Sequence[int] | np.ndarray,
    actual_counts: Sequence[int] | np.ndarray,
) -> float:
    """Compute PSI between expected and actual histogram bins.

    PSI = sum_i (a_i - e_i) * ln((a_i + eps) / (e_i + eps))
    where a_i, e_i are normalized probabilities.
    """
    expected = np.asarray(expected_counts, dtype=np.float64)
    actual = np.asarray(actual_counts, dtype=np.float64)
    if expected.shape != actual.shape:
        raise ValueError("histogram shapes must match for PSI")
    if expected.sum() <= 0 or actual.sum() <= 0:
        raise ValueError("histograms must have positive total mass")

    e = expected / expected.sum()
    a = actual / actual.sum()
    psi = float(np.sum((a - e) * np.log((a + _EPS) / (e + _EPS))))
    logger.debug("Computed PSI=%.6f", psi)
    return psi


def kolmogorov_smirnov(
    reference: np.ndarray,
    current: np.ndarray,
) -> tuple[float, float]:
    """Two-sample KS test on flattened feature values.

    Returns
    -------
    statistic, p_value
    """
    ref = np.asarray(reference, dtype=np.float64).ravel()
    cur = np.asarray(current, dtype=np.float64).ravel()
    if ref.size == 0 or cur.size == 0:
        raise ValueError("KS requires non-empty samples")
    result = stats.ks_2samp(ref, cur, alternative="two-sided", method="auto")
    logger.debug("Computed KS statistic=%.6f p=%.6g", result.statistic, result.pvalue)
    return float(result.statistic), float(result.pvalue)


def detect_shift(
    reference_stats: DataStats,
    current_stats: DataStats,
    *,
    reference_features: np.ndarray | None = None,
    current_features: np.ndarray | None = None,
    psi_threshold: float = 0.25,
    ks_p_threshold: float = 0.01,
) -> DriftReport:
    """Compare reference vs current distributions and flag significance.

    Significance rule (idea.md): DriftScore fires when PSI exceeds threshold
    OR KS p-value is below threshold (when raw features are provided).
    """
    psi = population_stability_index(
        reference_stats.flattened_histogram,
        current_stats.flattened_histogram,
    )

    ks_stat = 0.0
    ks_p = 1.0
    if reference_features is not None and current_features is not None:
        ks_stat, ks_p = kolmogorov_smirnov(reference_features, current_features)

    psi_hit = psi > psi_threshold
    ks_hit = ks_p < ks_p_threshold if reference_features is not None else False
    significant = bool(psi_hit or ks_hit)

    report = DriftReport(
        significant=significant,
        psi=psi,
        ks_statistic=ks_stat,
        ks_p_value=ks_p,
        psi_threshold=psi_threshold,
        ks_p_threshold=ks_p_threshold,
        details={
            "psi_hit": psi_hit,
            "ks_hit": ks_hit,
            "reference_split": reference_stats.split.value,
            "current_split": current_stats.split.value,
            "reference_n": reference_stats.n_samples,
            "current_n": current_stats.n_samples,
        },
    )
    logger.info(
        "DriftReport significant=%s psi=%.4f ks_p=%.4g",
        report.significant,
        report.psi,
        report.ks_p_value,
    )
    return report
