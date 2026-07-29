"""Dataset change detection — structured reports (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from evonas.domain.common.hashing import sha256_array


@dataclass(frozen=True, slots=True)
class ChangeReport:
    """Structured dataset change summary."""

    new_samples: int = 0
    removed_samples: int = 0
    duplicate_samples: int = 0
    schema_changed: bool = False
    feature_changed: bool = False
    label_changed: bool = False
    reference_n: int = 0
    candidate_n: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """True when any meaningful change is present."""
        return bool(
            self.new_samples
            or self.removed_samples
            or self.schema_changed
            or self.feature_changed
            or self.label_changed
            or self.duplicate_samples
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize change report."""
        return {
            "new_samples": self.new_samples,
            "removed_samples": self.removed_samples,
            "duplicate_samples": self.duplicate_samples,
            "schema_changed": self.schema_changed,
            "feature_changed": self.feature_changed,
            "label_changed": self.label_changed,
            "reference_n": self.reference_n,
            "candidate_n": self.candidate_n,
            "has_changes": self.has_changes,
            "details": dict(self.details),
        }


class DatasetChangeDetector:
    """Detect structural and content differences between datasets."""

    def detect(
        self,
        reference_features: np.ndarray,
        reference_labels: np.ndarray,
        candidate_features: np.ndarray,
        candidate_labels: np.ndarray,
    ) -> ChangeReport:
        """Compare reference vs candidate arrays."""
        ref_x = np.asarray(reference_features)
        ref_y = np.asarray(reference_labels)
        cand_x = np.asarray(candidate_features)
        cand_y = np.asarray(candidate_labels)

        schema_changed = ref_x.shape[1:] != cand_x.shape[1:] or ref_x.dtype != cand_x.dtype
        feature_changed = sha256_array(ref_x) != sha256_array(cand_x)
        label_changed = sha256_array(ref_y) != sha256_array(cand_y)

        # Row-hash based set difference for new / removed / duplicates
        ref_hashes = self._row_hashes(ref_x, ref_y)
        cand_hashes = self._row_hashes(cand_x, cand_y)
        ref_set = set(ref_hashes)
        cand_set = set(cand_hashes)
        new_samples = len(cand_set - ref_set)
        removed_samples = len(ref_set - cand_set)
        # duplicates within candidate
        unique, counts = np.unique(cand_hashes, return_counts=True)
        duplicate_samples = int(np.sum(counts[counts > 1]))

        return ChangeReport(
            new_samples=new_samples,
            removed_samples=removed_samples,
            duplicate_samples=duplicate_samples,
            schema_changed=schema_changed,
            feature_changed=feature_changed,
            label_changed=label_changed,
            reference_n=int(ref_x.shape[0]),
            candidate_n=int(cand_x.shape[0]),
            details={
                "n_unique_candidate": int(len(unique)),
                "ref_checksum": sha256_array(ref_x),
                "cand_checksum": sha256_array(cand_x),
            },
        )

    @staticmethod
    def _row_hashes(features: np.ndarray, labels: np.ndarray) -> np.ndarray:
        """Stable per-row identity hashes."""
        flat = np.ascontiguousarray(features).reshape(features.shape[0], -1)
        labs = np.ascontiguousarray(labels).reshape(labels.shape[0], -1)
        # Combine float bytes + label bytes into string hashes (vectorized via loop for clarity)
        out = np.empty(features.shape[0], dtype=object)
        for i in range(features.shape[0]):
            h = sha256_array(flat[i]) + ":" + sha256_array(labs[i])
            out[i] = h
        return out
