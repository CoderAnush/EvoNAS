"""Application use-cases for closed-loop CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evonas.application.closed_loop.controller import ClosedLoopController
from evonas.infrastructure.config.manager import ConfigurationManager


class RunClosedLoopUseCase:
    """Load config and execute ClosedLoopController (real or simulate)."""

    def __init__(self, *, config_manager: ConfigurationManager | None = None) -> None:
        self._config_manager = config_manager or ConfigurationManager()

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        simulate: bool = False,
        dry_run: bool = False,
        max_cycles: int | None = None,
    ) -> dict[str, Any]:
        """Run closed-loop from YAML and return summary."""
        path = Path(config_path)
        cfg = self._config_manager.load(path)
        controller = ClosedLoopController(
            cfg,
            config_path=path,
            output_dir=output_dir,
            simulate=simulate,
            dry_run=dry_run or simulate or bool(cfg.get("simulate", False)),
            config_manager=self._config_manager,
        )
        return controller.run(max_cycles=max_cycles)


class InspectClosedLoopUseCase:
    """Inspect a previous closed-loop artifact directory."""

    def inspect(self, run_dir: str | Path) -> dict[str, Any]:
        """Load summary / history from an artifact run."""
        root = Path(run_dir)
        summary_path = root / "summary.json"
        history_path = root / "lifecycle_history.json"
        payload: dict[str, Any] = {"run_dir": str(root)}
        if summary_path.exists():
            payload["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
        if history_path.exists():
            history = json.loads(history_path.read_text(encoding="utf-8"))
            payload["transition_count"] = len(history.get("transitions", []))
            payload["decision_count"] = len(history.get("decisions", []))
            payload["promotion_count"] = len(history.get("promotions", []))
            payload["transitions"] = history.get("transitions", [])[-20:]
            payload["decisions"] = history.get("decisions", [])[-20:]
        decisions_jsonl = root / "decisions.jsonl"
        if decisions_jsonl.exists():
            lines = [
                ln for ln in decisions_jsonl.read_text(encoding="utf-8").splitlines() if ln
            ]
            payload["decisions_jsonl_count"] = len(lines)
        return payload
