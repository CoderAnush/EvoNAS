"""Learning policy — recommendations only, never triggers optimization (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from evonas.domain.continuous.change_detector import ChangeReport
from evonas.domain.continuous.events import LearningRecommendation


@dataclass(frozen=True, slots=True)
class LearningPolicy:
    """Configurable continuous-learning thresholds."""

    min_new_samples: int = 10
    max_dataset_age_hours: float | None = None
    max_drift_psi: float = 0.25
    retrain_cooldown_hours: float = 0.0
    min_confidence: float = 0.0
    mild_drift_psi: float = 0.1
    optimize_on_schema_change: bool = True
    optimize_on_significant_drift: bool = True
    allow_retrain_on_mild_drift: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningPolicy:
        """Load from YAML mapping."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        nested = dict(data.get("policy", {}) or {})
        flat = {**nested, **{k: v for k, v in data.items() if not isinstance(v, dict)}}
        return cls(**{k: flat[k] for k in known if k in flat})

    @classmethod
    def from_yaml(cls, path: str | Path) -> LearningPolicy:
        """Load policy from YAML file."""
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("learning policy YAML must be a mapping")
        return cls.from_dict(raw)

    def to_dict(self) -> dict[str, Any]:
        """Serialize policy."""
        from dataclasses import asdict

        return asdict(self)

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
        """Produce a recommendation without authorizing lifecycle actions."""
        if not data_availability:
            return LearningRecommendation.HOLD, "no_data_availability"
        if confidence < self.min_confidence:
            return LearningRecommendation.HOLD, "confidence_below_minimum"
        if (
            hours_since_last_retrain is not None
            and hours_since_last_retrain < self.retrain_cooldown_hours
        ):
            return LearningRecommendation.HOLD, "retrain_cooldown"

        if not change.has_changes and not drift_significant and psi < self.mild_drift_psi:
            return LearningRecommendation.HOLD, "no_material_change"

        if change.new_samples < self.min_new_samples and not drift_significant:
            if not change.schema_changed:
                return LearningRecommendation.HOLD, "insufficient_new_samples"

        if self.optimize_on_schema_change and change.schema_changed:
            return LearningRecommendation.OPTIMIZE_ARCH, "schema_changed"

        if self.optimize_on_significant_drift and (
            drift_significant or psi >= self.max_drift_psi
        ):
            return LearningRecommendation.OPTIMIZE_ARCH, "significant_drift"

        if (
            self.allow_retrain_on_mild_drift
            and psi >= self.mild_drift_psi
            and change.new_samples >= self.min_new_samples
        ):
            return LearningRecommendation.RETRAIN_SAME_ARCH, "mild_drift_with_new_data"

        if change.new_samples >= self.min_new_samples:
            return LearningRecommendation.RETRAIN_SAME_ARCH, "enough_new_samples"

        return LearningRecommendation.HOLD, "policy_default_hold"
