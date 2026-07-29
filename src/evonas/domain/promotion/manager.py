"""Local promotion manager — accept/reject metadata only (no deployment)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PromotionRecord:
    """Record of a local accept/reject decision (Phase 8 deploy hook)."""

    accepted: bool
    model_id: str
    previous_model_id: str | None
    reason: str
    metrics: dict[str, float] = field(default_factory=dict)
    promotion_id: str = field(default_factory=lambda: f"promo_{uuid4().hex[:10]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    deployment_prepared: bool = False  # future Phase 8 hook

    def to_dict(self) -> dict[str, Any]:
        """Serialize promotion record."""
        return {
            "promotion_id": self.promotion_id,
            "accepted": self.accepted,
            "model_id": self.model_id,
            "previous_model_id": self.previous_model_id,
            "reason": self.reason,
            "metrics": dict(self.metrics),
            "timestamp": self.timestamp,
            "deployment_prepared": self.deployment_prepared,
        }


class PromotionManager:
    """Accept or reject candidates and store promotion metadata locally."""

    def __init__(self) -> None:
        self._history: list[PromotionRecord] = []
        self._current_model_id: str | None = None

    @property
    def current_model_id(self) -> str | None:
        """Locally promoted model id (not deployed)."""
        return self._current_model_id

    @property
    def history(self) -> list[PromotionRecord]:
        """Promotion history."""
        return list(self._history)

    def accept(
        self,
        model_id: str,
        *,
        previous_model_id: str | None,
        reason: str,
        metrics: dict[str, float] | None = None,
    ) -> PromotionRecord:
        """Mark candidate as accepted champion (local only)."""
        record = PromotionRecord(
            accepted=True,
            model_id=model_id,
            previous_model_id=previous_model_id,
            reason=reason,
            metrics=dict(metrics or {}),
            deployment_prepared=True,  # hook flag for Phase 8
        )
        self._current_model_id = model_id
        self._history.append(record)
        logger.info("Promoted locally model=%s reason=%s", model_id, reason)
        return record

    def reject(
        self,
        model_id: str,
        *,
        previous_model_id: str | None,
        reason: str,
        metrics: dict[str, float] | None = None,
    ) -> PromotionRecord:
        """Reject candidate; retain previous champion."""
        record = PromotionRecord(
            accepted=False,
            model_id=model_id,
            previous_model_id=previous_model_id,
            reason=reason,
            metrics=dict(metrics or {}),
            deployment_prepared=False,
        )
        self._history.append(record)
        logger.info("Rejected candidate model=%s reason=%s", model_id, reason)
        return record
