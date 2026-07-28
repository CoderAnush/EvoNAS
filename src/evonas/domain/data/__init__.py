"""Data domain package — models, drift, statistics, transforms, validation."""

from evonas.domain.data.drift import detect_shift, kolmogorov_smirnov, population_stability_index
from evonas.domain.data.models import (
    DataStats,
    DataWindow,
    DatasetHandle,
    DatasetManifest,
    DriftReport,
    Schema,
)
from evonas.domain.data.statistics import compute_data_stats
from evonas.domain.data.transforms import TransformConfig, TransformPipeline
from evonas.domain.data.validator import DatasetValidator, ValidationResult

__all__ = [
    "DataStats",
    "DataWindow",
    "DatasetHandle",
    "DatasetManifest",
    "DatasetValidator",
    "DriftReport",
    "Schema",
    "TransformConfig",
    "TransformPipeline",
    "ValidationResult",
    "compute_data_stats",
    "detect_shift",
    "kolmogorov_smirnov",
    "population_stability_index",
]
