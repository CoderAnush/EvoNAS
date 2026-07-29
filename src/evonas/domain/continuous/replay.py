"""Deterministic continuous-learning replay (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas.domain.continuous.events import LearningEvent, LearningResult


@dataclass(slots=True)
class ReplaySupport:
    """Replay historical learning results / events deterministically."""

    steps: list[dict[str, Any]] = field(default_factory=list)
    cursor: int = 0

    @classmethod
    def from_history_json(cls, path: str | Path) -> ReplaySupport:
        """Load replay steps from a learning history export."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        steps: list[dict[str, Any]] = []
        # Prefer recorded policy decisions + events as ordered steps
        for decision in payload.get("policy_decisions", []):
            steps.append({"kind": "policy", **decision})
        if not steps:
            for event in payload.get("events", []):
                steps.append({"kind": "event", **event})
        return cls(steps=steps, cursor=0)

    @classmethod
    def from_results(cls, results: list[LearningResult]) -> ReplaySupport:
        """Build replay from in-memory LearningResult list."""
        return cls(steps=[r.to_dict() for r in results], cursor=0)

    def reset(self) -> None:
        """Reset cursor to start."""
        self.cursor = 0

    def has_next(self) -> bool:
        """True when more steps remain."""
        return self.cursor < len(self.steps)

    def next_step(self) -> dict[str, Any] | None:
        """Return next step and advance cursor."""
        if not self.has_next():
            return None
        step = dict(self.steps[self.cursor])
        self.cursor += 1
        return step

    def replay_all(self) -> list[dict[str, Any]]:
        """Consume all remaining steps."""
        out: list[dict[str, Any]] = []
        while self.has_next():
            step = self.next_step()
            if step is not None:
                out.append(step)
        return out

    def to_events(self) -> list[LearningEvent]:
        """Materialize LearningEvent objects from event-shaped steps."""
        events: list[LearningEvent] = []
        for step in self.steps:
            if "event_type" in step:
                events.append(LearningEvent.from_dict(step))
        return events

    def export_json(self, path: str | Path) -> Path:
        """Persist replay script."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            json.dumps({"steps": self.steps, "cursor": self.cursor}, indent=2),
            encoding="utf-8",
        )
        return file_path
