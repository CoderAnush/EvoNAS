"""Dashboard service unit tests (no Streamlit server required)."""

from __future__ import annotations

import json
from pathlib import Path

from evonas.presentation.cli.main import build_parser, main
from evonas.presentation.dashboard.services.demo_data import (
    demo_adaptive_history,
    demo_landing,
    demo_lifecycle,
)
from evonas.presentation.dashboard.services.facade import DashboardContext, DashboardService
from evonas.presentation.dashboard.services.loaders import read_json, read_jsonl
from evonas.presentation.dashboard.views.pages import RENDERERS


def test_demo_landing_fields() -> None:
    data = demo_landing()
    assert data["version"]
    assert data["demo"] is True
    assert data["optimizer"] == "sapso"


def test_demo_adaptive_and_lifecycle() -> None:
    adaptive = demo_adaptive_history()
    assert len(adaptive["records"]) > 0
    assert adaptive["transitions"]
    life = demo_lifecycle()
    assert life["transitions"]
    assert life["decisions"]


def test_facade_demo_mode(tmp_path: Path) -> None:
    svc = DashboardService(DashboardContext(cwd=tmp_path, demo_mode=True))
    landing = svc.landing()
    assert landing["demo"] is True
    opt = svc.optimization_summary()
    assert opt["stats"]["iterations"] > 0
    sapso = svc.sapso_analytics()
    assert sapso["adaptive"]["records"]
    life = svc.lifecycle()
    assert life["history"]["transitions"]
    cl = svc.continuous()
    assert cl["history"]["events"]
    arch = svc.architecture()
    assert "mermaid" in arch
    assert svc.comparison()["winner"]
    assert svc.replay_steps("lifecycle")
    assert svc.health()["version"]
    assert svc.settings()["configs"]


def test_loaders_json_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    path.write_text(json.dumps({"x": 1}), encoding="utf-8")
    assert read_json(path) == {"x": 1}
    jl = tmp_path / "b.jsonl"
    jl.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
    assert len(read_jsonl(jl)) == 2


def test_facade_reads_artifacts(tmp_path: Path) -> None:
    opt = tmp_path / "artifacts" / "optimization" / "run1"
    opt.mkdir(parents=True)
    (opt / "summary.json").write_text(
        json.dumps({"run_id": "run1", "algorithm": "sapso", "best_fitness": -0.1, "iterations": 3}),
        encoding="utf-8",
    )
    (opt / "history.json").write_text(
        json.dumps(
            {
                "records": [
                    {"iteration": 1, "gbest_fitness": -1.0, "mean_fitness": -1.2, "diversity": 0.4, "evaluations": 8},
                    {"iteration": 2, "gbest_fitness": -0.5, "mean_fitness": -0.8, "diversity": 0.3, "evaluations": 16},
                ]
            }
        ),
        encoding="utf-8",
    )
    loop = tmp_path / "artifacts" / "closed_loop" / "loop1"
    loop.mkdir(parents=True)
    (loop / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "loop1",
                "state": "completed",
                "algorithm": "sapso",
                "current_metrics": {"accuracy": 0.8},
                "cycles": 1,
                "optimizations_used": 1,
            }
        ),
        encoding="utf-8",
    )
    (loop / "lifecycle_history.json").write_text(
        json.dumps({"transitions": [{"source": "idle", "target": "monitoring", "reason": "start"}]}),
        encoding="utf-8",
    )
    svc = DashboardService(DashboardContext(cwd=tmp_path, demo_mode=False))
    landing = svc.landing()
    assert landing["lifecycle_state"] == "completed"
    assert landing["optimizer"] == "sapso"
    opt_data = svc.optimization_summary()
    assert opt_data["summary"]["algorithm"] == "sapso"
    assert opt_data["stats"]["iterations"] == 2
    rows = svc.experiments()
    assert any(r["kind"] == "optimization" for r in rows)


def test_all_renderers_registered() -> None:
    assert "Landing" in RENDERERS
    assert "SAPSO Analytics" in RENDERERS
    assert len(RENDERERS) >= 14


def test_cli_dashboard_parser() -> None:
    parser = build_parser()
    args = parser.parse_args(["dashboard", "--port", "8502", "--demo", "--headless"])
    assert args.command == "dashboard"
    assert args.port == 8502
    assert args.demo is True
    assert args.headless is True


def test_dashboard_version_0_8(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0rc2"
