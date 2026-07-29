"""Safe artifact / JSON / CSV loaders for the dashboard (read-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> dict[str, Any] | list[Any] | None:
    """Load JSON file; return None if missing or invalid."""
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except (OSError, json.JSONDecodeError):
        return None


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL; skip bad lines."""
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    except OSError:
        return []
    return rows


def read_text(path: str | Path, limit: int = 200_000) -> str | None:
    """Load text file with size guard."""
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        data = file_path.read_text(encoding="utf-8")
        return data if len(data) <= limit else data[:limit] + "\n…[truncated]"
    except OSError:
        return None


def list_run_dirs(root: str | Path) -> list[Path]:
    """List immediate subdirectories that look like experiment runs."""
    base = Path(root)
    if not base.exists() or not base.is_dir():
        return []
    runs = [p for p in sorted(base.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True) if p.is_dir()]
    return runs


def find_named(run_dir: Path, *names: str) -> Path | None:
    """Return first existing file among names (relative to run_dir)."""
    for name in names:
        path = run_dir / name
        if path.exists():
            return path
    return None


def discover_artifact_roots(cwd: str | Path | None = None) -> dict[str, Path]:
    """Discover standard artifact roots relative to cwd."""
    base = Path(cwd) if cwd else Path.cwd()
    artifacts = base / "artifacts"
    roots = {
        "artifacts": artifacts,
        "optimization": artifacts / "optimization",
        "closed_loop": artifacts / "closed_loop",
        "continuous_learning": artifacts / "continuous_learning",
        "baselines": artifacts / "baselines",
        "research": artifacts / "research",
        "rc1": artifacts / "rc1",
        "demo": artifacts / "demo",
    }
    return roots


def load_yaml(path: str | Path) -> dict[str, Any] | None:
    """Load YAML mapping."""
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        import yaml

        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None
