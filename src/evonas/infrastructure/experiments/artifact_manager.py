"""Artifact manager — reproducible experiment file layout."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Create and manage experiment artifact directories.

    Layout (Phase 2)::
        artifacts/baselines/<run_id>/
          config.resolved.yaml / .json
          metrics.json
          history.json
          checkpoints/
          logs/
          reports/
    """

    def __init__(self, root: str | Path = "artifacts/baselines") -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Artifacts root."""
        return self._root

    def create_run(self, run_id: str | None = None) -> Path:
        """Allocate a new run directory and standard subfolders."""
        if run_id is None:
            run_id = datetime.now(timezone.utc).strftime("baseline_%Y%m%d_%H%M%S")
        path = self._root / run_id
        for sub in ("checkpoints", "logs", "reports", "plots"):
            (path / sub).mkdir(parents=True, exist_ok=True)
        logger.info("Created artifact run dir=%s", path)
        return path

    def write_json(self, run_dir: Path, name: str, payload: dict[str, Any]) -> Path:
        """Write a JSON artifact under ``run_dir``."""
        path = run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(path)
        return path

    def copy_config(
        self, run_dir: Path, source: str | Path, dest_name: str = "config.resolved.yaml"
    ) -> Path:
        """Copy a config file into the run directory for reproducibility."""
        dest = run_dir / dest_name
        shutil.copy2(source, dest)
        return dest
