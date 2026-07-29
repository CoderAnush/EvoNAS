"""Adaptive history export helpers (JSON / CSV)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class AdaptiveHistoryRecorder:
    """Persist SAPSO adaptation trajectories and state transitions."""

    def export_json(self, payload: dict[str, Any], path: str | Path) -> Path:
        """Write full adaptive history JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return file_path

    def export_csv(self, payload: dict[str, Any], path: str | Path) -> Path:
        """Write flat per-iteration adaptive CSV."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        records = list(payload.get("records", []))
        fields = [
            "iteration",
            "w",
            "c1",
            "c2",
            "phase",
            "exploration_pressure",
            "improvement_rate",
            "normalized_diversity",
        ]
        with file_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                writer.writerow({k: record.get(k) for k in fields})
        return file_path

    def export_transitions_csv(self, payload: dict[str, Any], path: str | Path) -> Path:
        """Write state-transition log CSV."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        transitions = list(payload.get("transitions", []))
        fields = ["iteration", "from", "to", "reason"]
        with file_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for row in transitions:
                writer.writerow({k: row.get(k) for k in fields})
        return file_path
