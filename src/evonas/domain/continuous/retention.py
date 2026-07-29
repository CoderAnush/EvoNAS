"""Retention policy for continuous-learning versions (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evonas.domain.continuous.versions import DataVersionManager, DatasetVersion


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Keep at most ``max_versions`` raw versions; preserve stats via metadata."""

    max_versions: int = 20
    keep_latest: int = 5
    delete_raw_arrays: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetentionPolicy:
        """Load retention config."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data[k] for k in known if k in data})


@dataclass(slots=True)
class RetentionResult:
    """Outcome of applying retention."""

    kept: list[str] = field(default_factory=list)
    pruned: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize."""
        return {"kept": list(self.kept), "pruned": list(self.pruned)}


def apply_retention(
    manager: DataVersionManager,
    policy: RetentionPolicy,
) -> RetentionResult:
    """Prune old versions from the in-memory index (optional array delete)."""
    versions = manager.list_versions()
    if len(versions) <= policy.max_versions:
        return RetentionResult(kept=[v.version_id for v in versions], pruned=[])

    keep_n = max(policy.keep_latest, 1)
    # Keep newest keep_n always; prune oldest beyond max_versions
    ordered = list(versions)
    to_keep = {v.version_id for v in ordered[-keep_n:]}
    overflow = len(ordered) - policy.max_versions
    pruned: list[str] = []
    for ver in ordered:
        if overflow <= 0:
            break
        if ver.version_id in to_keep:
            continue
        pruned.append(ver.version_id)
        del manager.versions[ver.version_id]
        if policy.delete_raw_arrays and ver.features_uri:
            from pathlib import Path

            for uri in (ver.features_uri, ver.labels_uri):
                if uri:
                    path = Path(uri)
                    if path.exists():
                        path.unlink()
        overflow -= 1
    manager._persist_index()  # noqa: SLF001 — intentional retention side-effect
    return RetentionResult(
        kept=[v.version_id for v in manager.list_versions()],
        pruned=pruned,
    )


def summarize_versions(versions: list[DatasetVersion]) -> list[dict[str, Any]]:
    """Compact version summaries for audit (no arrays)."""
    return [
        {
            "version_id": v.version_id,
            "n_samples": v.n_samples,
            "parent_version": v.parent_version,
            "checksum": v.checksum,
            "created_at": v.created_at,
            "role": v.role,
        }
        for v in versions
    ]
