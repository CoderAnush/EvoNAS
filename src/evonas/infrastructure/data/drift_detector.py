"""Concrete IDriftDetector adapter wrapping domain drift math."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from evonas.domain.data.drift import detect_shift
from evonas.domain.data.models import DataStats, DriftReport

logger = logging.getLogger(__name__)


class DefaultDriftDetector:
    """Default Phase 1 drift detector (PSI + optional KS).

    Frozen public adapter for ``IDriftDetector``. Contains no I/O and does not
    load datasets — callers supply statistics and optional raw features.
    """

    def __init__(
        self,
        *,
        psi_threshold: float = 0.25,
        ks_p_threshold: float = 0.01,
    ) -> None:
        self._psi_threshold = float(psi_threshold)
        self._ks_p_threshold = float(ks_p_threshold)

    def detect(
        self,
        reference: DataStats,
        current: DataStats,
        *,
        reference_features: object | None = None,
        current_features: object | None = None,
    ) -> DriftReport:
        """Produce a DriftReport from stats and optional raw feature arrays."""
        ref_feat = np.asarray(reference_features) if reference_features is not None else None
        cur_feat = np.asarray(current_features) if current_features is not None else None
        report = detect_shift(
            reference,
            current,
            reference_features=ref_feat,
            current_features=cur_feat,
            psi_threshold=self._psi_threshold,
            ks_p_threshold=self._ks_p_threshold,
        )
        logger.debug("DefaultDriftDetector significant=%s", report.significant)
        return report

    def to_dict(self) -> dict[str, Any]:
        """Serialize detector thresholds for manifests / debugging."""
        return {
            "psi_threshold": self._psi_threshold,
            "ks_p_threshold": self._ks_p_threshold,
        }
