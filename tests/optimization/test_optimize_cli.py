"""CLI and OptimizeUseCase smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from evonas.application.optimize import OptimizeUseCase
from evonas.presentation.cli.main import main


def test_optimize_mock_usecase(tmp_path: Path) -> None:
    summary = OptimizeUseCase().run(
        "configs/pso/mock_sphere.yaml",
        output_dir=tmp_path / "opt",
        dry_run=False,
    )
    assert summary["algorithm"] == "standard_pso"
    assert summary["evaluations"] > 0
    run_dir = Path(summary["run_dir"])
    assert (run_dir / "history.json").exists()
    assert (run_dir / "history.csv").exists()
    assert (run_dir / "summary.json").exists()


def test_optimize_cli_dry_run(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "optimize",
            "--config",
            "configs/pso/mock_sphere.yaml",
            "--out",
            str(tmp_path / "cli_opt"),
            "--dry-run",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["fitness_mode"] == "mock"


def test_version_updated(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0rc2"
