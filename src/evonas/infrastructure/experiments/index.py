"""File-based experiment registry / index (Phase 10)."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evonas import __version__


def git_commit(cwd: Path | None = None) -> str:
    """Best-effort git HEAD SHA."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd or Path.cwd()),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def config_checksum(path: str | Path) -> str:
    """SHA-256 of config file bytes."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def artifact_checksum(path: str | Path) -> str:
    """SHA-256 of an artifact file."""
    return config_checksum(path)


class ExperimentRegistry:
    """Append-only JSONL index under artifacts/research/index.jsonl."""

    def __init__(self, root: str | Path = "artifacts/research") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.jsonl"

    def record(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Append a registry entry and return it."""
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "evonas_version": __version__,
            "git_commit": git_commit(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            **entry,
        }
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
        return payload

    def list_entries(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Newest-first listing."""
        if not self.index_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        rows.reverse()
        return rows[:limit]

    def get(self, experiment_id: str) -> dict[str, Any] | None:
        """Lookup by experiment_id (latest match)."""
        for entry in self.list_entries(limit=10_000):
            if entry.get("experiment_id") == experiment_id:
                return entry
        return None
