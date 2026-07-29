"""Immutable dataset versioning and lineage metadata (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from evonas.domain.common.hashing import sha256_array, sha256_bytes


@dataclass(frozen=True, slots=True)
class DatasetVersion:
    """Immutable dataset version record."""

    version_id: str
    created_at: str
    parent_version: str | None
    checksum: str
    n_samples: int
    schema_fingerprint: str
    metadata: dict[str, Any] = field(default_factory=dict)
    role: str = "candidate"  # parent | training | candidate | child
    features_uri: str | None = None
    labels_uri: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize version."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetVersion:
        """Deserialize version."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data[k] for k in known if k in data})


@dataclass(slots=True)
class DataVersionManager:
    """Persist immutable dataset versions under an artifact root."""

    root: Path
    versions: dict[str, DatasetVersion] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        index = self.root / "versions_index.json"
        if index.exists():
            payload = json.loads(index.read_text(encoding="utf-8"))
            for item in payload.get("versions", []):
                ver = DatasetVersion.from_dict(item)
                self.versions[ver.version_id] = ver

    def create(
        self,
        features: Any,
        labels: Any,
        *,
        parent_version: str | None = None,
        schema_fingerprint: str = "",
        metadata: dict[str, Any] | None = None,
        role: str = "candidate",
        version_id: str | None = None,
    ) -> DatasetVersion:
        """Create a new immutable version (arrays written to disk)."""
        import numpy as np

        feats = np.asarray(features)
        labs = np.asarray(labels)
        checksum = sha256_bytes(
            (sha256_array(feats) + ":" + sha256_array(labs)).encode("utf-8")
        )
        vid = version_id or f"dv_{uuid4().hex[:12]}"
        created = datetime.now(timezone.utc).isoformat()
        ver_dir = self.root / vid
        ver_dir.mkdir(parents=True, exist_ok=True)
        feat_path = ver_dir / "features.npy"
        lab_path = ver_dir / "labels.npy"
        np.save(feat_path, feats)
        np.save(lab_path, labs)
        version = DatasetVersion(
            version_id=vid,
            created_at=created,
            parent_version=parent_version,
            checksum=checksum,
            n_samples=int(feats.shape[0]),
            schema_fingerprint=schema_fingerprint
            or f"shape={tuple(feats.shape[1:])}|dtype={feats.dtype}",
            metadata=dict(metadata or {}),
            role=role,
            features_uri=str(feat_path),
            labels_uri=str(lab_path),
        )
        self.versions[vid] = version
        self._persist_index()
        (ver_dir / "version.json").write_text(
            json.dumps(version.to_dict(), indent=2), encoding="utf-8"
        )
        return version

    def get(self, version_id: str) -> DatasetVersion | None:
        """Lookup version by id."""
        return self.versions.get(version_id)

    def list_versions(self) -> list[DatasetVersion]:
        """Return versions sorted by creation time."""
        return sorted(self.versions.values(), key=lambda v: v.created_at)

    def load_arrays(self, version_id: str) -> tuple[Any, Any]:
        """Load feature/label arrays for a version."""
        import numpy as np

        ver = self.versions[version_id]
        if not ver.features_uri or not ver.labels_uri:
            raise KeyError(f"version {version_id} missing array URIs")
        return np.load(ver.features_uri), np.load(ver.labels_uri)

    def _persist_index(self) -> None:
        index = self.root / "versions_index.json"
        payload = {
            "versions": [v.to_dict() for v in self.list_versions()],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        index.write_text(json.dumps(payload, indent=2), encoding="utf-8")
