"""Application research use-cases (Phase 10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evonas.application.compare_optimizers import CompareOptimizersUseCase
from evonas.application.research.orchestrator import ExperimentOrchestrator
from evonas.application.platform.artifact_loaders import read_json
from evonas.domain.research.report import generate_report
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.experiments.index import ExperimentRegistry


class BenchmarkUseCase:
    """Run scientific benchmark suite (orchestrator)."""

    def __init__(self, *, config_manager: ConfigurationManager | None = None) -> None:
        self._orch = ExperimentOrchestrator(config_manager=config_manager)

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        return self._orch.run(config_path, output_dir=output_dir, dry_run=dry_run)


class ExperimentUseCase:
    """List / show registered experiments."""

    def __init__(self, *, root: str | Path = "artifacts/research") -> None:
        self._registry = ExperimentRegistry(root=root)

    def list(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self._registry.list_entries(limit=limit)

    def show(self, experiment_id: str) -> dict[str, Any]:
        entry = self._registry.get(experiment_id)
        if entry is None:
            return {"error": "not_found", "experiment_id": experiment_id}
        run_dir = Path(str(entry.get("run_dir", "")))
        payload = dict(entry)
        if run_dir.exists():
            for name in ("meta.json", "results.json", "statistics.json", "comparison.json"):
                data = read_json(run_dir / name)
                if data is not None:
                    payload[name.replace(".json", "")] = data
        return payload


class CompareResearchUseCase:
    """Compare via legacy PSO-vs-SAPSO config OR multi-algo suite config."""

    def __init__(self, *, config_manager: ConfigurationManager | None = None) -> None:
        self._config_manager = config_manager or ConfigurationManager()
        self._legacy = CompareOptimizersUseCase(config_manager=self._config_manager)
        self._benchmark = BenchmarkUseCase(config_manager=self._config_manager)

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        suite: bool = False,
    ) -> dict[str, Any]:
        cfg = self._config_manager.load(config_path)
        if suite or cfg.get("algorithms") or cfg.get("matrix"):
            return self._benchmark.run(config_path, output_dir=output_dir, dry_run=True)
        return self._legacy.run(config_path, output_dir=output_dir)


class ReportUseCase:
    """Regenerate or print a report from an existing run directory."""

    def run(self, run_dir: str | Path, *, out: str | Path | None = None) -> dict[str, Any]:
        path = Path(run_dir)
        meta = read_json(path / "meta.json") or {}
        results = read_json(path / "results.json") or {}
        statistics = read_json(path / "statistics.json") or {}
        target = Path(out) if out else path / "reports" / "experiment_report.md"
        report = generate_report(
            {"meta": meta, "results": results, "statistics": statistics},
            target,
        )
        return {"report": str(report), "meta": meta, "results": results}


def dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, default=str)
