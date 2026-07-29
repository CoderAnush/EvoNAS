"""Statistical analysis for multi-seed research experiments.

Methods are documented explicitly. No distributional assumptions are hardcoded
into reporting — optional significance tests are gated by configuration.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np


def summarize(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Descriptive statistics + normal-approx CI (documented as such).

    CI uses mean ± z * (s / sqrt(n)) with z from the standard normal quantile.
    This is an approximation — not a claim of normality of the underlying data.
    """
    arr = np.asarray(list(values), dtype=float)
    n = int(arr.size)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "variance": None,
            "std": None,
            "min": None,
            "max": None,
            "ci_low": None,
            "ci_high": None,
            "ci_level": confidence,
            "ci_method": "normal_approx",
        }
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if n > 1 else 0.0
    var = float(arr.var(ddof=1)) if n > 1 else 0.0
    z = _z_quantile(confidence)
    se = std / math.sqrt(n) if n > 0 else 0.0
    return {
        "n": n,
        "mean": mean,
        "median": float(np.median(arr)),
        "variance": var,
        "std": std,
        "min": float(arr.min()),
        "max": float(arr.max()),
        "ci_low": mean - z * se,
        "ci_high": mean + z * se,
        "ci_level": confidence,
        "ci_method": "normal_approx",
    }


def paired_wilcoxon(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Optional paired Wilcoxon signed-rank test (SciPy).

    Returns ``available=False`` if SciPy is missing or samples are too small /
    constant. Does not invent p-values.
    """
    x = np.asarray(list(a), dtype=float)
    y = np.asarray(list(b), dtype=float)
    if x.size != y.size or x.size < 3:
        return {
            "test": "wilcoxon_signed_rank",
            "available": False,
            "reason": "need paired samples with n>=3",
        }
    try:
        from scipy import stats  # type: ignore[import-untyped]
    except ImportError:
        return {
            "test": "wilcoxon_signed_rank",
            "available": False,
            "reason": "scipy not installed",
        }
    diff = x - y
    if np.allclose(diff, 0.0):
        return {
            "test": "wilcoxon_signed_rank",
            "available": True,
            "statistic": 0.0,
            "pvalue": 1.0,
            "note": "all paired differences are zero",
        }
    try:
        result = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
    except ValueError as exc:
        return {
            "test": "wilcoxon_signed_rank",
            "available": False,
            "reason": str(exc),
        }
    return {
        "test": "wilcoxon_signed_rank",
        "available": True,
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "alternative": "two-sided",
    }


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Cliff's delta effect size (non-parametric)."""
    x = list(a)
    y = list(b)
    if not x or not y:
        return {"effect": "cliffs_delta", "delta": None, "n_a": len(x), "n_b": len(y)}
    more = less = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                more += 1
            elif xi < yj:
                less += 1
    denom = len(x) * len(y)
    delta = (more - less) / denom if denom else 0.0
    return {
        "effect": "cliffs_delta",
        "delta": float(delta),
        "n_a": len(x),
        "n_b": len(y),
        "interpretation": _interpret_cliffs(delta),
    }


def compare_paired(
    a: Sequence[float],
    b: Sequence[float],
    *,
    label_a: str = "a",
    label_b: str = "b",
    confidence: float = 0.95,
    run_significance: bool = True,
) -> dict[str, Any]:
    """Honest paired comparison summary — no winner bias."""
    payload: dict[str, Any] = {
        "label_a": label_a,
        "label_b": label_b,
        "summary_a": summarize(a, confidence=confidence),
        "summary_b": summarize(b, confidence=confidence),
        "delta_mean_b_minus_a": (
            float(np.mean(b) - np.mean(a)) if len(a) and len(b) else None
        ),
        "effect_size": cliffs_delta(a, b),
    }
    if run_significance:
        payload["significance"] = paired_wilcoxon(a, b)
    else:
        payload["significance"] = {
            "test": "wilcoxon_signed_rank",
            "available": False,
            "reason": "disabled by configuration",
        }
    return payload


def _z_quantile(confidence: float) -> float:
    # Common levels without requiring SciPy
    table = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}
    if confidence in table:
        return table[confidence]
    # fallback approx via SciPy if present
    try:
        from scipy import stats

        return float(stats.norm.ppf(0.5 + confidence / 2.0))
    except Exception:  # noqa: BLE001
        return 1.959963984540054


def _interpret_cliffs(delta: float) -> str:
    ad = abs(delta)
    if ad < 0.147:
        return "negligible"
    if ad < 0.33:
        return "small"
    if ad < 0.474:
        return "medium"
    return "large"
