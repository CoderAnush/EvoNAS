"""Immutable DecisionContext — sole input to DecisionEngine (idea.md §23)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    """Remaining / used optimization and training budgets."""

    max_optimizations: int = 3
    optimizations_used: int = 0
    max_search_wallclock_minutes: float = 60.0
    search_wallclock_used_minutes: float = 0.0
    max_train_hours: float = 24.0
    train_hours_used: float = 0.0
    cooldown_hours: float = 0.0
    hours_since_last_optimization: float | None = None

    @property
    def optimizations_exhausted(self) -> bool:
        """True when optimization count budget is spent."""
        return self.optimizations_used >= self.max_optimizations

    def to_dict(self) -> dict[str, Any]:
        """Serialize budgets."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BudgetSnapshot:
        """Load budgets from mapping."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data[k] for k in known if k in data})


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Serializable system snapshot for policy evaluation.

    Controllers build this; DecisionEngine never mutates it.
    """

    mode: str = "quick"
    system_mode: str = "monitoring"
    current_model_id: str | None = None
    current_metrics: dict[str, float] = field(default_factory=dict)
    best_metrics: dict[str, float] = field(default_factory=dict)
    candidate_metrics: dict[str, float] | None = None
    candidate_model_id: str | None = None
    dataset_version: str | None = None
    drift_status: str = "unknown"  # unknown | none | mild | significant
    drift_report: dict[str, Any] = field(default_factory=dict)
    optimization_state: str = "idle"  # idle | running | converged | failed
    optimization_history: list[dict[str, Any]] = field(default_factory=list)
    last_optimization_time: str | None = None
    budgets: BudgetSnapshot = field(default_factory=BudgetSnapshot)
    force_optimization: bool = False
    trigger_consider: bool = False
    trigger_reasons: tuple[str, ...] = ()
    accuracy_threshold: float | None = None
    experiment_metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    recent_decisions: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logs and artifacts."""
        payload = asdict(self)
        payload["trigger_reasons"] = list(self.trigger_reasons)
        payload["recent_decisions"] = list(self.recent_decisions)
        payload["budgets"] = self.budgets.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionContext:
        """Deserialize DecisionContext."""
        budgets_raw = data.get("budgets", {})
        budgets = (
            BudgetSnapshot.from_dict(budgets_raw)
            if isinstance(budgets_raw, dict)
            else BudgetSnapshot()
        )
        return cls(
            mode=str(data.get("mode", "quick")),
            system_mode=str(data.get("system_mode", "monitoring")),
            current_model_id=data.get("current_model_id"),
            current_metrics=dict(data.get("current_metrics", {})),
            best_metrics=dict(data.get("best_metrics", {})),
            candidate_metrics=(
                dict(data["candidate_metrics"])
                if isinstance(data.get("candidate_metrics"), dict)
                else None
            ),
            candidate_model_id=data.get("candidate_model_id"),
            dataset_version=data.get("dataset_version"),
            drift_status=str(data.get("drift_status", "unknown")),
            drift_report=dict(data.get("drift_report", {})),
            optimization_state=str(data.get("optimization_state", "idle")),
            optimization_history=list(data.get("optimization_history", [])),
            last_optimization_time=data.get("last_optimization_time"),
            budgets=budgets,
            force_optimization=bool(data.get("force_optimization", False)),
            trigger_consider=bool(data.get("trigger_consider", False)),
            trigger_reasons=tuple(data.get("trigger_reasons", ()) or ()),
            accuracy_threshold=(
                float(data["accuracy_threshold"])
                if data.get("accuracy_threshold") is not None
                else None
            ),
            experiment_metadata=dict(data.get("experiment_metadata", {})),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            recent_decisions=tuple(data.get("recent_decisions", ()) or ()),
        )
