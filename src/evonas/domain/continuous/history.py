"""Continuous-learning history recorder (Phase 7)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evonas.domain.continuous.events import LearningEvent


@dataclass(slots=True)
class LearningHistory:
    """Record versions, events, drift, and policy decisions."""

    events: list[dict[str, Any]] = field(default_factory=list)
    versions: list[dict[str, Any]] = field(default_factory=list)
    drift_reports: list[dict[str, Any]] = field(default_factory=list)
    policy_decisions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: LearningEvent | dict[str, Any]) -> None:
        """Append a learning event."""
        self.events.append(event.to_dict() if isinstance(event, LearningEvent) else dict(event))

    def add_version(self, version: dict[str, Any]) -> None:
        """Append a dataset version record."""
        self.versions.append(dict(version))

    def add_drift(self, report: dict[str, Any]) -> None:
        """Append a drift report snapshot."""
        payload = dict(report)
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.drift_reports.append(payload)

    def add_policy_decision(
        self, recommendation: str, reason: str, **extra: Any
    ) -> None:
        """Append a policy recommendation (not a DecisionEngine record)."""
        self.policy_decisions.append(
            {
                "recommendation": recommendation,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **extra,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize full history."""
        return {
            "metadata": dict(self.metadata),
            "events": list(self.events),
            "versions": list(self.versions),
            "drift_reports": list(self.drift_reports),
            "policy_decisions": list(self.policy_decisions),
        }

    def export_json(self, path: str | Path) -> Path:
        """Write history JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return file_path

    def export_csv(self, path: str | Path) -> Path:
        """Write events CSV."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["timestamp", "event_type", "dataset_version", "recommendation", "event_id"]
        with file_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for event in self.events:
                writer.writerow(event)
        return file_path
