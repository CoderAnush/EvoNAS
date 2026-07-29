"""Immutable continuous-learning events (Phase 7)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class LearningEventType(str, Enum):
    """Serializable learning event kinds."""

    NEW_DATA_DETECTED = "NewDataDetected"
    DATASET_MERGED = "DatasetMerged"
    DATASET_REJECTED = "DatasetRejected"
    DATASET_VERSION_CREATED = "DatasetVersionCreated"
    RETRAINING_RECOMMENDED = "RetrainingRecommended"
    RETRAINING_SKIPPED = "RetrainingSkipped"
    OPTIMIZE_RECOMMENDED = "OptimizeRecommended"
    DRIFT_COMPUTED = "DriftComputed"
    WINDOW_ADVANCED = "WindowAdvanced"
    RETENTION_APPLIED = "RetentionApplied"
    REPLAY_STEP = "ReplayStep"


class LearningRecommendation(str, Enum):
    """Recommendations only — Decision Engine authorizes (idea.md §166)."""

    HOLD = "HOLD"
    RETRAIN_SAME_ARCH = "RETRAIN_SAME_ARCH"
    OPTIMIZE_ARCH = "OPTIMIZE_ARCH"


@dataclass(frozen=True, slots=True)
class LearningEvent:
    """Immutable, serializable continuous-learning audit event."""

    event_type: LearningEventType
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"cle_{uuid4().hex[:12]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dataset_version: str | None = None
    recommendation: LearningRecommendation | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize event."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "dataset_version": self.dataset_version,
            "recommendation": self.recommendation.value if self.recommendation else None,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningEvent:
        """Deserialize event."""
        rec = data.get("recommendation")
        return cls(
            event_type=LearningEventType(str(data["event_type"])),
            payload=dict(data.get("payload", {})),
            event_id=str(data.get("event_id", f"cle_{uuid4().hex[:12]}")),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            dataset_version=data.get("dataset_version"),
            recommendation=(
                LearningRecommendation(str(rec)) if rec is not None else None
            ),
        )


@dataclass(frozen=True, slots=True)
class LearningResult:
    """Structured output returned to ClosedLoopController / CLI."""

    recommendation: LearningRecommendation
    events: tuple[LearningEvent, ...]
    dataset_version: str | None
    parent_version: str | None
    drift_status: str
    drift_report: dict[str, Any]
    change_report: dict[str, Any]
    training_candidate: dict[str, Any]
    data_availability: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize learning result."""
        return {
            "recommendation": self.recommendation.value,
            "events": [e.to_dict() for e in self.events],
            "dataset_version": self.dataset_version,
            "parent_version": self.parent_version,
            "drift_status": self.drift_status,
            "drift_report": dict(self.drift_report),
            "change_report": dict(self.change_report),
            "training_candidate": dict(self.training_candidate),
            "data_availability": self.data_availability,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }

    def to_observation(self) -> dict[str, Any]:
        """Map to ClosedLoopController ``observation`` fields (Phase 6 contract)."""
        report = dict(self.drift_report)
        if "psi" in report and "psi_max" not in report:
            report["psi_max"] = report["psi"]
        return {
            "drift_status": self.drift_status,
            "drift_report": report,
            "force_optimization": self.recommendation
            == LearningRecommendation.OPTIMIZE_ARCH,
            "dataset_version": self.dataset_version,
            "cl_recommendation": self.recommendation.value,
            "cl_reason": self.reason,
            "data_availability": self.data_availability,
            "training_candidate": dict(self.training_candidate),
            "change_report": dict(self.change_report),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningResult:
        """Deserialize learning result."""
        events = tuple(
            LearningEvent.from_dict(e) for e in data.get("events", []) if isinstance(e, dict)
        )
        return cls(
            recommendation=LearningRecommendation(str(data["recommendation"])),
            events=events,
            dataset_version=data.get("dataset_version"),
            parent_version=data.get("parent_version"),
            drift_status=str(data.get("drift_status", "unknown")),
            drift_report=dict(data.get("drift_report", {})),
            change_report=dict(data.get("change_report", {})),
            training_candidate=dict(data.get("training_candidate", {})),
            data_availability=bool(data.get("data_availability", False)),
            reason=str(data.get("reason", "")),
            metadata=dict(data.get("metadata", {})),
        )


# Keep asdict import used only if needed for typing clarity
_ = asdict
