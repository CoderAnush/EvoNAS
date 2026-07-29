"""Versioned decision policy configuration (idea.md §24)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    """Configurable thresholds for DecisionEngine questions."""

    policy_version: str = "1.0.0"
    # Degradation / accuracy
    accuracy_floor: float = 0.0
    accuracy_drop_abs: float = 0.02
    min_expected_improvement: float = 0.005
    # Drift
    psi_threshold: float = 0.2
    treat_unknown_drift_as_ok: bool = True
    # Optimization control
    cooldown_hours: float = 0.0
    max_optimizations: int = 3
    max_search_wallclock_minutes: float = 180.0
    force_initial_search: bool = True
    # Validation / promote (Phase 6 local promotion; not deploy)
    min_improvement_abs: float = 0.005
    max_complexity_params: int | None = None
    max_train_seconds: float | None = None
    allow_parity_promote: bool = False
    # Phase 8 stubs
    allow_deploy: bool = False
    allow_rollback: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionPolicy:
        """Load policy from YAML mapping (supports nested idea.md layout)."""
        degradation = dict(data.get("degradation", {}) or {})
        drift = dict(data.get("drift", {}) or {})
        optimization = dict(data.get("optimization", {}) or {})
        deployment = dict(data.get("deployment", {}) or {})
        budgets = dict(data.get("budgets", {}) or {})
        validation = dict(data.get("validation", {}) or {})
        flat = {
            **degradation,
            **drift,
            **optimization,
            **deployment,
            **budgets,
            **validation,
            **{k: v for k, v in data.items() if not isinstance(v, dict)},
        }
        # aliases
        if "min_improvement_abs" in deployment:
            flat["min_improvement_abs"] = deployment["min_improvement_abs"]
        if "max_search_wallclock_minutes" in budgets:
            flat["max_search_wallclock_minutes"] = budgets["max_search_wallclock_minutes"]
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: flat[k] for k in known if k in flat}
        if "policy_version" in data:
            filtered["policy_version"] = data["policy_version"]
        return cls(**filtered)

    @classmethod
    def from_yaml(cls, path: str | Path) -> DecisionPolicy:
        """Load policy from a YAML file."""
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("policy YAML root must be a mapping")
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize policy."""
        from dataclasses import asdict

        return asdict(self)
