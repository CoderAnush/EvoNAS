"""Decision records — immutable audit of DecisionEngine outcomes (idea.md)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """Authorized lifecycle decision (REQ-DEC-010)."""

    question: str
    outcome: bool
    action: str
    rationale: dict[str, Any] = field(default_factory=dict)
    policy_version: str = "1.0.0"
    decision_id: str = field(default_factory=lambda: f"dec_{uuid4().hex[:12]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    experiment_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize record."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionRecord:
        """Deserialize record."""
        return cls(
            question=str(data["question"]),
            outcome=bool(data["outcome"]),
            action=str(data["action"]),
            rationale=dict(data.get("rationale", {})),
            policy_version=str(data.get("policy_version", "1.0.0")),
            decision_id=str(data.get("decision_id", f"dec_{uuid4().hex[:12]}")),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            experiment_id=data.get("experiment_id"),
        )


@dataclass(frozen=True, slots=True)
class TriggerDecision:
    """Outcome of OptimizationTrigger.evaluate (idea.md §229)."""

    consider: bool
    reasons: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)
    trigger_type: str = "composite"

    def to_dict(self) -> dict[str, Any]:
        """Serialize trigger decision."""
        return {
            "consider": self.consider,
            "reasons": list(self.reasons),
            "scores": dict(self.scores),
            "trigger_type": self.trigger_type,
        }
