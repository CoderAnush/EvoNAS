"""Lifecycle history recorder — transitions, decisions, promotions."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TransitionRecord:
    """One lifecycle state transition."""

    source: str
    target: str
    reason: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize."""
        return {
            "source": self.source,
            "target": self.target,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class LifecycleHistory:
    """Full closed-loop run history with JSON/CSV export."""

    transitions: list[TransitionRecord] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    optimizations: list[dict[str, Any]] = field(default_factory=list)
    promotions: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_transition(self, source: str, target: str, reason: str) -> TransitionRecord:
        """Append a transition."""
        record = TransitionRecord(source=source, target=target, reason=reason)
        self.transitions.append(record)
        return record

    def add_decision(self, decision: dict[str, Any]) -> None:
        """Append a decision dict."""
        self.decisions.append(dict(decision))

    def add_optimization(self, payload: dict[str, Any]) -> None:
        """Append optimization request / result."""
        self.optimizations.append(dict(payload))

    def add_promotion(self, payload: dict[str, Any]) -> None:
        """Append promotion accept/reject."""
        self.promotions.append(dict(payload))

    def add_event(self, kind: str, **payload: Any) -> None:
        """Append a generic event."""
        self.events.append(
            {
                "kind": kind,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **payload,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize full history."""
        return {
            "metadata": dict(self.metadata),
            "transitions": [t.to_dict() for t in self.transitions],
            "decisions": list(self.decisions),
            "optimizations": list(self.optimizations),
            "promotions": list(self.promotions),
            "events": list(self.events),
        }

    def export_json(self, path: str | Path) -> Path:
        """Write history JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return file_path

    def export_csv(self, path: str | Path) -> Path:
        """Write transitions CSV."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["timestamp", "source", "target", "reason"]
        with file_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for t in self.transitions:
                writer.writerow(t.to_dict())
        return file_path

    def export_decisions_jsonl(self, path: str | Path) -> Path:
        """Write one DecisionRecord JSON per line."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as fh:
            for decision in self.decisions:
                fh.write(json.dumps(decision) + "\n")
        return file_path
