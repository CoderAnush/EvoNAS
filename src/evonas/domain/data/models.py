"""Dataset domain models — Schema, handles, manifests, windows, stats."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from evonas.domain.common.enums import Split, TaskType


@dataclass(frozen=True, slots=True)
class Schema:
    """Framework-agnostic description of a dataset's tensor contract."""

    name: str
    version: str
    task_type: TaskType
    input_shape: tuple[int, ...]
    num_classes: int | None
    dtype: str
    feature_dim: int
    label_dtype: str = "int64"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize schema for manifests."""
        payload = asdict(self)
        payload["task_type"] = self.task_type.value
        payload["input_shape"] = list(self.input_shape)
        return payload


@dataclass(slots=True)
class DatasetHandle:
    """In-memory view of a dataset partition or window.

    Features and labels are NumPy arrays. Domain code may consume handles;
    training backends (Phase 2+) convert them into framework tensors.
    """

    split: Split
    features: np.ndarray
    labels: np.ndarray
    indices: np.ndarray
    schema: Schema
    checksum: str
    window_id: str | None = None

    def __post_init__(self) -> None:
        if len(self.features) != len(self.labels):
            raise ValueError("features and labels length mismatch")
        if len(self.features) != len(self.indices):
            raise ValueError("features and indices length mismatch")

    @property
    def size(self) -> int:
        """Number of samples in this handle."""
        return int(self.features.shape[0])

    def is_empty(self) -> bool:
        """Return True when the handle contains no samples."""
        return self.size == 0


@dataclass(frozen=True, slots=True)
class DataWindow:
    """Index-based continuous-learning window over a split."""

    split: Split
    start_idx: int
    end_idx: int
    window_id: str

    def __post_init__(self) -> None:
        if self.start_idx < 0 or self.end_idx < self.start_idx:
            raise ValueError(f"invalid window bounds: [{self.start_idx}, {self.end_idx})")


@dataclass(frozen=True, slots=True)
class DataStats:
    """Aggregate statistics used for drift reference and observability."""

    split: Split
    n_samples: int
    feature_mean: tuple[float, ...]
    feature_std: tuple[float, ...]
    feature_min: tuple[float, ...]
    feature_max: tuple[float, ...]
    label_histogram: dict[int, int]
    flattened_histogram: tuple[int, ...]
    bin_edges: tuple[float, ...]
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize statistics for manifests / artifacts."""
        return {
            "split": self.split.value,
            "n_samples": self.n_samples,
            "feature_mean": list(self.feature_mean),
            "feature_std": list(self.feature_std),
            "feature_min": list(self.feature_min),
            "feature_max": list(self.feature_max),
            "label_histogram": {str(k): v for k, v in self.label_histogram.items()},
            "flattened_histogram": list(self.flattened_histogram),
            "bin_edges": list(self.bin_edges),
            "checksum": self.checksum,
        }


@dataclass(frozen=True, slots=True)
class DriftReport:
    """Result of comparing reference vs current distributions."""

    significant: bool
    psi: float
    ks_statistic: float
    ks_p_value: float
    psi_threshold: float
    ks_p_threshold: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize drift report for logs and decision context."""
        return {
            "significant": self.significant,
            "psi": self.psi,
            "ks_statistic": self.ks_statistic,
            "ks_p_value": self.ks_p_value,
            "psi_threshold": self.psi_threshold,
            "ks_p_threshold": self.ks_p_threshold,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Versioned checksummed manifest for a prepared dataset."""

    schema_version: str
    name: str
    version: str
    seed: int
    created_at: str
    schema: dict[str, Any]
    split_sizes: dict[str, int]
    checksums: dict[str, str]
    config_hash: str
    statistics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest JSON."""
        return asdict(self)
