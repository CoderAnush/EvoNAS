"""Architecture serialization — JSON / YAML / dict with schema versioning."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from evonas.domain.common.errors import ArchitectureError
from evonas.domain.model.architecture_spec import ArchitectureSpec

logger = logging.getLogger(__name__)

SUPPORTED_SCHEMA_VERSIONS = frozenset({"2.0", "3.0"})


class ArchitectureSerializer:
    """Save / load ArchitectureSpec with version awareness."""

    def to_dict(self, spec: ArchitectureSpec) -> dict[str, Any]:
        """Convert to dictionary."""
        return spec.to_dict()

    def from_dict(self, data: dict[str, Any]) -> ArchitectureSpec:
        """Load from dictionary; reject unknown future major schemas softly."""
        version = str(data.get("schema_version", "2.0"))
        if version not in SUPPORTED_SCHEMA_VERSIONS and not version.startswith(("2.", "3.")):
            raise ArchitectureError(f"unsupported architecture schema_version '{version}'")
        return ArchitectureSpec.from_dict(data)

    def to_json(self, spec: ArchitectureSpec, *, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(spec), indent=indent, sort_keys=True)

    def from_json(self, text: str) -> ArchitectureSpec:
        """Deserialize from JSON string."""
        return self.from_dict(json.loads(text))

    def to_yaml(self, spec: ArchitectureSpec) -> str:
        """Serialize to YAML string."""
        return yaml.safe_dump(self.to_dict(spec), sort_keys=False)

    def from_yaml(self, text: str) -> ArchitectureSpec:
        """Deserialize from YAML string."""
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ArchitectureError("YAML architecture root must be a mapping")
        return self.from_dict(data)

    def save(self, spec: ArchitectureSpec, path: str | Path) -> Path:
        """Save to ``.json`` or ``.yaml``/``.yml`` based on suffix."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            file_path.write_text(self.to_json(spec), encoding="utf-8")
        elif suffix in {".yaml", ".yml"}:
            file_path.write_text(self.to_yaml(spec), encoding="utf-8")
        else:
            raise ArchitectureError(f"unsupported architecture file suffix: {suffix}")
        logger.info("Saved architecture name=%s path=%s", spec.name, file_path)
        return file_path

    def load(self, path: str | Path) -> ArchitectureSpec:
        """Load from a JSON or YAML file."""
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8")
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return self.from_json(text)
        if suffix in {".yaml", ".yml"}:
            return self.from_yaml(text)
        raise ArchitectureError(f"unsupported architecture file suffix: {suffix}")
