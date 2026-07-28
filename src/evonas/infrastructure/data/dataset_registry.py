"""Dataset manifest registry — versioned checksum persistence."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evonas.domain.common.errors import DataError
from evonas.domain.data.models import DatasetManifest, Schema

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = "1.0"


class DatasetRegistry:
    """Persist and load dataset manifests under ``artifacts/datasets/``.

    Responsibility: manifest I/O and future versioning hooks (SRP).
    Does not generate samples or compute statistics.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Manifest root directory."""
        return self._root

    def manifest_path(self, name: str) -> Path:
        """Return the canonical manifest path for a dataset name."""
        return self._root / name / "manifest.json"

    def save(self, manifest: DatasetManifest) -> Path:
        """Atomically write a manifest JSON file."""
        path = self.manifest_path(manifest.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        payload = manifest.to_dict()
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
        logger.info("Wrote dataset manifest %s", path)
        return path

    def load(self, name: str) -> DatasetManifest:
        """Load an existing manifest or raise DataError."""
        path = self.manifest_path(name)
        if not path.exists():
            raise DataError(f"manifest not found for dataset '{name}': {path}", code="EN_DATA_001")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DataError(f"corrupt manifest at {path}", code="EN_DATA_001") from exc
        return DatasetManifest(**raw)

    def exists(self, name: str) -> bool:
        """Return True if a manifest exists for ``name``."""
        return self.manifest_path(name).exists()

    def build_manifest(
        self,
        *,
        name: str,
        version: str,
        seed: int,
        schema: Schema,
        split_sizes: dict[str, int],
        checksums: dict[str, str],
        config_hash: str,
        statistics: dict[str, Any] | None = None,
    ) -> DatasetManifest:
        """Construct a manifest dataclass with UTC timestamp."""
        return DatasetManifest(
            schema_version=MANIFEST_SCHEMA_VERSION,
            name=name,
            version=version,
            seed=seed,
            created_at=datetime.now(timezone.utc).isoformat(),
            schema=schema.to_dict(),
            split_sizes=split_sizes,
            checksums=checksums,
            config_hash=config_hash,
            statistics=statistics or {},
        )
