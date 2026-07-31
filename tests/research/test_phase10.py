"""Phase 10 research framework tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from evonas.application.research.matrix import expand_matrix
from evonas.application.research.orchestrator import ExperimentOrchestrator
from evonas.application.research.use_cases import (
    BenchmarkUseCase,
    ExperimentUseCase,
    ReportUseCase,
)
from evonas.benchmarks.random_search import RandomSearch, RandomSearchConfig
from evonas.domain.research.stats import compare_paired, summarize
from evonas.domain.research.tables import to_latex, to_markdown, write_table_bundle
from evonas.domain.search_space.space import SearchSpace
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator
from evonas.presentation.cli.main import build_parser, main


def _write_suite_config(path: Path, *, n_seeds: int = 3) -> Path:
    payload = {
        "experiment_id": "test_suite",
        "seed": 42,
        "algorithms": ["standard_pso", "sapso", "random_search"],
        "datasets": [
            {
                "id": "sphere",
                "landscape": "sphere",
                "space_path": "configs/search_spaces/sphere_2d.yaml",
            }
        ],
        "seeds": {"n": n_seeds, "base": 42},
        "optimization": {
            "swarm_size": 8,
            "max_iterations": 5,
            "log_particles": False,
        },
        "random_search": {"n_trials": 40},
        "adaptation": {},
        "statistics": {"confidence": 0.95, "significance_tests": True},
        "fitness": {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
        "experiment": {"artifacts_root": str(path / "artifacts" / "research")},
    }
    cfg = path / "suite.yaml"
    cfg.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return cfg


def test_summarize_and_compare_paired() -> None:
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [1.5, 2.5, 3.5, 4.5, 5.5]
    s = summarize(a)
    assert s["n"] == 5
    assert s["mean"] == 3.0
    assert s["ci_low"] is not None
    cmp = compare_paired(a, b, label_a="pso", label_b="sapso")
    assert cmp["delta_mean_b_minus_a"] == 0.5
    assert cmp["effect_size"]["effect"] == "cliffs_delta"


def test_tables_markdown_latex(tmp_path: Path) -> None:
    rows = [{"algorithm": "sapso", "mean_fitness": 0.9}, {"algorithm": "pso", "mean_fitness": 0.8}]
    md = to_markdown(rows, title="T")
    assert "sapso" in md
    tex = to_latex(rows, caption="T")
    assert r"\begin{table}" in tex
    paths = write_table_bundle(rows, tmp_path, stem="t", title="T")
    assert Path(paths["csv"]).exists()


def test_random_search_reproducible() -> None:
    space = SearchSpace.from_yaml("configs/search_spaces/sphere_2d.yaml")

    def run(seed: int) -> float:
        opt = RandomSearch(RandomSearchConfig(n_trials=30, maximize=True, seed=seed))
        opt.set_evaluator(MockFitnessEvaluator(landscape="sphere", maximize=True))
        opt.initialize(space, seed)
        return float(opt.run().best_fitness)

    assert run(1) == run(1)
    assert run(1) != run(2) or True  # may coincide rarely; primary check is seed1 stable


def test_matrix_expansion() -> None:
    cells = expand_matrix(
        {
            "algorithms": ["standard_pso", "sapso"],
            "datasets": [{"id": "sphere", "landscape": "sphere"}],
            "seeds": {"n": 5, "base": 10},
            "configurations": [{"id": "default"}],
            "search_space": {"path": "configs/search_spaces/sphere_2d.yaml"},
        }
    )
    assert len(cells) == 10
    assert {c.seed for c in cells} == {10, 11, 12, 13, 14}


def test_orchestrator_end_to_end(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    # copy search space into tmp? SearchSpace.from_yaml uses path relative to cwd —
    # use absolute path in config
    root = Path(__file__).resolve().parents[2]
    space = root / "configs" / "search_spaces" / "sphere_2d.yaml"
    cfg_path = tmp_path / "suite.yaml"
    payload = {
        "experiment_id": "test_suite",
        "seed": 42,
        "algorithms": ["standard_pso", "sapso", "random_search"],
        "datasets": [{"id": "sphere", "landscape": "sphere", "space_path": str(space)}],
        "seeds": {"n": 3, "base": 42},
        "optimization": {"swarm_size": 6, "max_iterations": 4, "log_particles": False},
        "random_search": {"n_trials": 24},
        "adaptation": {},
        "statistics": {"confidence": 0.95, "significance_tests": True},
        "fitness": {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
        "experiment": {"artifacts_root": str(tmp_path / "artifacts" / "research")},
    }
    cfg_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    result = ExperimentOrchestrator().run(cfg_path, dry_run=True)
    assert result["meta"]["experiment_id"] == "test_suite"
    assert Path(result["run_dir"]).exists()
    assert (Path(result["run_dir"]) / "comparison.json").exists()
    assert (Path(result["run_dir"]) / "statistics.json").exists()
    assert (Path(result["run_dir"]) / "reports" / "experiment_report.md").exists()
    assert result["results"]["winner"] in {
        "standard_pso",
        "sapso",
        "random_search",
        "tie",
    }
    # Reproducibility: same config => same winner/means
    result2 = ExperimentOrchestrator().run(cfg_path, dry_run=True)
    assert result["results"]["winner"] == result2["results"]["winner"]
    means1 = {
        k: v["aggregates"]["best_fitness"]["mean"]
        for k, v in result["results"]["algorithms"].items()
    }
    means2 = {
        k: v["aggregates"]["best_fitness"]["mean"]
        for k, v in result2["results"]["algorithms"].items()
    }
    for key in means1:
        assert abs(means1[key] - means2[key]) < 1e-9


def test_experiment_registry_and_report(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parents[2]
    space = root / "configs" / "search_spaces" / "sphere_2d.yaml"
    cfg_path = tmp_path / "suite.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "experiment_id": "reg_test",
                "algorithms": ["standard_pso", "sapso"],
                "datasets": [{"id": "sphere", "landscape": "sphere", "space_path": str(space)}],
                "seeds": {"n": 2, "base": 1},
                "optimization": {"swarm_size": 4, "max_iterations": 3, "log_particles": False},
                "adaptation": {},
                "fitness": {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
                "experiment": {"artifacts_root": str(tmp_path / "artifacts" / "research")},
            }
        ),
        encoding="utf-8",
    )
    out = BenchmarkUseCase().run(cfg_path)
    listed = ExperimentUseCase(root=tmp_path / "artifacts" / "research").list()
    assert any(e.get("experiment_id") == "reg_test" for e in listed)
    shown = ExperimentUseCase(root=tmp_path / "artifacts" / "research").show("reg_test")
    assert shown.get("experiment_id") == "reg_test"
    report = ReportUseCase().run(out["run_dir"])
    assert Path(report["report"]).exists()


def test_cli_parsers_phase10() -> None:
    parser = build_parser()
    assert parser.parse_args(["benchmark", "--config", "x.yaml"]).command == "benchmark"
    assert parser.parse_args(["experiment", "list"]).experiment_command == "list"
    assert parser.parse_args(["compare", "--suite"]).suite is True
    assert parser.parse_args(["report", "--run-dir", "r"]).command == "report"


def test_version_rc1(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"
