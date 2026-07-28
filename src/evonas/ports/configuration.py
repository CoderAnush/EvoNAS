"""IConfigurationManager port (idea.md §21.2) — minimal Phase 0/1 surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IConfigurationManager(Protocol):
    """Load, validate, and hash configuration documents."""

    def load(self, path: str | Path) -> dict[str, Any]:
        """Load a YAML/JSON config file into a dictionary."""

    def validate(self, config: dict[str, Any]) -> bool:
        """Return True when config passes schema checks."""

    def get(self, key: str, config: dict[str, Any] | None = None) -> Any:
        """Resolve a dotted key from config."""

    def hash(self, config: dict[str, Any]) -> str:
        """Stable hash of canonicalized config JSON."""
