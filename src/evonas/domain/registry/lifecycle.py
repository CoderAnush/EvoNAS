"""Lifecycle transition manager — configurable, audited, metadata-only."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from evonas.domain.common.errors import EvoNASError
from evonas.domain.registry.types import LifecycleState, ModelStage


class LifecycleError(EvoNASError):
    """Illegal lifecycle or stage transition."""

    code = "EN_REG_001"


class LifecycleManager:
    """Enforce configurable lifecycle and stage transitions."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        life = dict(cfg.get("lifecycle", {}))
        stages = dict(cfg.get("stages", {}))
        self.initial = str(life.get("initial", LifecycleState.CREATED.value))
        self._life_transitions: dict[str, list[str]] = {
            str(k): [str(x) for x in v]
            for k, v in dict(life.get("transitions", {})).items()
        }
        if not self._life_transitions:
            self._life_transitions = self._default_lifecycle()
        self._stage_transitions: dict[str, list[str]] = {
            str(k): [str(x) for x in v]
            for k, v in dict(stages.get("transitions", {})).items()
        }
        if not self._stage_transitions:
            self._stage_transitions = self._default_stages()

    def can_transition(self, current: str, target: str) -> bool:
        return target in self._life_transitions.get(current, [])

    def transition(
        self,
        current: str,
        target: str,
        *,
        object_id: str,
        reason: str = "",
    ) -> dict[str, Any]:
        if not self.can_transition(current, target):
            raise LifecycleError(
                f"Illegal lifecycle transition {current} → {target} for {object_id}"
            )
        return {
            "event_id": f"life_{uuid4().hex[:10]}",
            "object_id": object_id,
            "from_state": current,
            "to_state": target,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": "lifecycle_event",
        }

    def can_set_stage(self, current: str, target: str) -> bool:
        return target in self._stage_transitions.get(current, [])

    def set_stage(
        self,
        current: str,
        target: str,
        *,
        model_id: str,
        version: str,
        reason: str = "",
    ) -> dict[str, Any]:
        if target not in {s.value for s in ModelStage}:
            raise LifecycleError(f"Unknown stage: {target}")
        if not self.can_set_stage(current, target):
            raise LifecycleError(
                f"Illegal stage transition {current} → {target} for {model_id}@{version}"
            )
        return {
            "event_id": f"stage_{uuid4().hex[:10]}",
            "model_id": model_id,
            "version": version,
            "from_stage": current,
            "to_stage": target,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": "stage_event",
        }

    def graph(self) -> dict[str, Any]:
        """Lifecycle + stage graphs for visualization."""
        return {
            "lifecycle": self._life_transitions,
            "stages": self._stage_transitions,
            "initial": self.initial,
        }

    def mermaid_lifecycle(self) -> str:
        lines = ["stateDiagram-v2"]
        for src, targets in self._life_transitions.items():
            for dst in targets:
                lines.append(f"    {src} --> {dst}")
        return "\n".join(lines)

    def mermaid_stages(self) -> str:
        lines = ["stateDiagram-v2"]
        for src, targets in self._stage_transitions.items():
            for dst in targets:
                lines.append(f"    {src} --> {dst}")
        return "\n".join(lines)

    @staticmethod
    def _default_lifecycle() -> dict[str, list[str]]:
        return {
            "created": ["training", "evaluating", "archived", "deleted"],
            "training": ["evaluating", "failed", "archived"],
            "evaluating": ["candidate", "rejected", "archived"],
            "candidate": ["validated", "rejected", "archived"],
            "validated": ["promoted", "archived", "deprecated"],
            "promoted": ["archived", "deprecated", "rolled_back"],
            "rejected": ["archived", "deleted"],
            "failed": ["archived", "deleted"],
            "archived": ["deprecated", "deleted"],
            "deprecated": ["deleted"],
            "rolled_back": ["archived", "deprecated", "candidate"],
            "deleted": [],
        }

    @staticmethod
    def _default_stages() -> dict[str, list[str]]:
        return {
            "none": ["staging", "archived"],
            "staging": ["production", "archived", "none"],
            "production": ["archived", "staging"],
            "archived": ["none"],
        }
