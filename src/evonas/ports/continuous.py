"""Continuous learning ports (Phase 7)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from evonas.domain.continuous.change_detector import ChangeReport
from evonas.domain.continuous.events import LearningRecommendation, LearningResult
from evonas.domain.continuous.versions import DatasetVersion


@runtime_checkable
class ILearningPolicy(Protocol):
    """Configurable recommendation policy (never authorizes optimization)."""

    def recommend(
        self,
        *,
        change: ChangeReport,
        drift_significant: bool,
        psi: float,
        hours_since_last_retrain: float | None = None,
        data_availability: bool = True,
        confidence: float = 1.0,
    ) -> tuple[LearningRecommendation, str]:
        """Return recommendation + reason."""


@runtime_checkable
class IDatasetChangeDetector(Protocol):
    """Detect structural / content dataset changes."""

    def detect(
        self,
        reference_features: Any,
        reference_labels: Any,
        candidate_features: Any,
        candidate_labels: Any,
    ) -> ChangeReport:
        """Return structured change report."""


@runtime_checkable
class IDataVersionManager(Protocol):
    """Immutable dataset version store."""

    def create(
        self,
        features: Any,
        labels: Any,
        *,
        parent_version: str | None = None,
        schema_fingerprint: str = "",
        metadata: dict[str, Any] | None = None,
        role: str = "candidate",
        version_id: str | None = None,
    ) -> DatasetVersion:
        """Create a new immutable version."""

    def get(self, version_id: str) -> DatasetVersion | None:
        """Lookup version."""

    def list_versions(self) -> list[DatasetVersion]:
        """List versions."""


@runtime_checkable
class IContinuousLearningEngine(Protocol):
    """Public continuous-learning contract for controllers and CLI."""

    def run_cycle(self, **kwargs: Any) -> LearningResult:
        """Execute one detect→version→drift→recommend cycle."""

    def recommend(self, **kwargs: Any) -> tuple[LearningRecommendation, str]:
        """Policy recommendation only."""

    def to_observation(self) -> dict[str, Any]:
        """Map last result to ClosedLoop observation fields."""

    def current_window(self) -> dict[str, Any] | None:
        """Current window cursor, if any."""

    @property
    def last_result(self) -> LearningResult | None:
        """Most recent learning result."""
