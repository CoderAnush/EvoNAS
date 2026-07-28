"""IDatasetManager and IDriftDetector ports (idea.md §21.1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from evonas.domain.common.enums import Split
from evonas.domain.data.models import (
    DataStats,
    DatasetHandle,
    DriftReport,
    Schema,
)


@runtime_checkable
class IDatasetManager(Protocol):
    """Public contract for the EvoNAS data plane.

    Implementations acquire, version, checksum, split, window, and summarize
    datasets. They do not train models or authorize lifecycle decisions.
    """

    def prepare(self) -> None:
        """Download/cache/materialize dataset and write checksum manifests."""

    def load(self, split: Split | str) -> DatasetHandle:
        """Load a named split as a DatasetHandle."""

    def get_schema(self) -> Schema:
        """Return the resolved dataset schema."""

    def get_window(
        self, start: int, end: int, *, split: Split | str = Split.TRAIN
    ) -> DatasetHandle:
        """Return an index window ``[start, end)`` over a split for continuous learning."""

    def subset(
        self,
        split: Split | str,
        fraction: float,
        seed: int,
    ) -> DatasetHandle:
        """Deterministically subsample a fraction of a split (Quick Mode)."""

    def compute_statistics(self, split: Split | str | None = None) -> DataStats:
        """Compute (or return cached) statistics for a split; default train."""

    def checksums(self) -> dict[str, str]:
        """Return partition checksum map from the prepared manifest."""

    def detect_shift(
        self,
        reference: DataStats | DatasetHandle,
        current: DataStats | DatasetHandle,
    ) -> DriftReport:
        """Compare reference vs current distributions for drift."""

    def drift_report(
        self,
        reference: DataStats | DatasetHandle,
        current: DataStats | DatasetHandle,
    ) -> DriftReport:
        """Alias for ``detect_shift`` (idea.md deep contract naming)."""


@runtime_checkable
class IDriftDetector(Protocol):
    """Optional specialized drift detector port."""

    def detect(
        self,
        reference: DataStats,
        current: DataStats,
        *,
        reference_features: object | None = None,
        current_features: object | None = None,
    ) -> DriftReport:
        """Produce a DriftReport from stats and optional raw features."""
