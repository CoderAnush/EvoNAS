"""CLI / use-case smoke for SAPSO and comparison."""

from __future__ import annotations

import json
from pathlib import Path

from evonas.application.compare_optimizers import CompareOptimizersUseCase
from evonas.application.optimize import OptimizeUseCase
from evonas.presentation.cli.main import main


def test_optimize_sapso_mock(tmp_path: Path) -> None:
    summary = OptimizeUseCase().run(
        "configs/pso/adaptive_mock.yaml",
        output_dir=tmp_path / "sapso",
    )
    assert summary["algorithm"] == "sapso"
    run_dir = Path(summary["run_dir"])
    assert (run_dir / "adaptive_history.json").exists()
    assert (run_dir / "adaptive_history.csv").exists()
    assert summary["adaptive_records"] > 0


def test_compare_optimizers_usecase(tmp_path: Path) -> None:
    report = CompareOptimizersUseCase().run(
        "configs/optimization/pso_vs_sapso.yaml",
        output_dir=tmp_path / "cmp",
    )
    assert "winner" in report
    assert Path(report["run_dir"], "comparison.json").exists()


def test_compare_cli(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "compare-optimizers",
            "--config",
            "configs/optimization/pso_vs_sapso.yaml",
            "--out",
            str(tmp_path / "cli_cmp"),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["winner"] in {"sapso", "standard_pso", "tie"}


def test_version_0_8(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"
