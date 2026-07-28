"""Dataset structural validation (schema + split integrity)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.common.errors import DataError
from evonas.domain.data.models import DatasetHandle, Schema

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of a validation pass."""

    ok: bool
    errors: tuple[str, ...] = ()

    @property
    def error_message(self) -> str:
        """Join errors for exception messages."""
        return "; ".join(self.errors)


class DatasetValidator:
    """Validate schema contracts and split disjointness / coverage.

    Responsibility: validation only (SRP). Does not load or transform data.
    """

    def validate_schema(self, schema: Schema) -> ValidationResult:
        """Validate schema invariants."""
        errors: list[str] = []
        if not schema.name:
            errors.append("schema.name must be non-empty")
        if not schema.version:
            errors.append("schema.version must be non-empty")
        if not schema.input_shape or any(d <= 0 for d in schema.input_shape):
            errors.append("schema.input_shape must contain positive dims")
        if schema.feature_dim <= 0:
            errors.append("schema.feature_dim must be positive")
        if schema.task_type.value.endswith("classification"):
            if schema.num_classes is None or schema.num_classes < 2:
                errors.append("classification schema requires num_classes >= 2")
        ok = not errors
        if not ok:
            logger.warning("Schema validation failed: %s", errors)
        return ValidationResult(ok=ok, errors=tuple(errors))

    def validate_handle(self, handle: DatasetHandle) -> ValidationResult:
        """Validate a loaded handle against its schema."""
        errors: list[str] = []
        schema_result = self.validate_schema(handle.schema)
        errors.extend(schema_result.errors)

        if handle.size == 0:
            errors.append(f"split {handle.split.value} is empty")

        expected_feat = handle.schema.feature_dim
        flat = handle.features.reshape(handle.size, -1)
        if flat.shape[1] != expected_feat:
            errors.append(f"feature dim mismatch: got {flat.shape[1]}, expected {expected_feat}")

        if handle.schema.num_classes is not None:
            labels = handle.labels.astype(np.int64, copy=False).ravel()
            if labels.min() < 0 or labels.max() >= handle.schema.num_classes:
                errors.append("labels outside [0, num_classes)")

        ok = not errors
        if not ok:
            logger.warning("Handle validation failed for %s: %s", handle.split.value, errors)
        return ValidationResult(ok=ok, errors=tuple(errors))

    def validate_split_disjointness(
        self,
        indices: dict[Split, np.ndarray],
    ) -> ValidationResult:
        """Ensure train/val/test index sets are pairwise disjoint."""
        errors: list[str] = []
        splits = list(indices.keys())
        for i, a in enumerate(splits):
            for b in splits[i + 1 :]:
                inter = np.intersect1d(indices[a], indices[b])
                if inter.size > 0:
                    errors.append(f"splits {a.value} and {b.value} share {inter.size} indices")
        ok = not errors
        if not ok:
            logger.error("Split disjointness violated: %s", errors)
        return ValidationResult(ok=ok, errors=tuple(errors))

    def require_ok(self, result: ValidationResult, *, code: str = "EN_DATA_001") -> None:
        """Raise DataError when validation failed."""
        if not result.ok:
            raise DataError(result.error_message, code=code)
