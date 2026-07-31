"""EvoNAS CLI — Phase 0–3 commands (idea.md)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from evonas import __version__
from evonas.infrastructure.data import DatasetManager
from evonas.infrastructure.logging.setup import setup_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="evonas",
        description="EvoNAS — Autonomous Closed-Loop AutoML Platform",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Print package version")
    sub.add_parser("doctor", help="Basic environment sanity checks")

    run_p = sub.add_parser("run", help="Run closed-loop modes (available in later phases)")
    run_p.add_argument("--mode", choices=["research", "quick", "replay"], default="quick")
    run_p.add_argument("--config", default="configs/default.yaml")

    replay_p = sub.add_parser("replay", help="Replay an experiment (later phases)")
    replay_p.add_argument("--experiment-id", required=False)

    prep = sub.add_parser("prepare-dataset", help="Prepare a dataset and write its manifest")
    prep.add_argument(
        "--config",
        default="configs/datasets/toy_quick.yaml",
        help="Path to dataset YAML config",
    )

    train = sub.add_parser("train", help="Train a model from a training YAML config")
    train.add_argument(
        "--config",
        default="configs/training/baseline.yaml",
        help="Path to training YAML (default: baseline)",
    )

    train_b = sub.add_parser(
        "train-baseline",
        help="Train the Phase 2 baseline model (alias of train with baseline config)",
    )
    train_b.add_argument(
        "--config",
        default="configs/training/baseline.yaml",
        help="Path to baseline training YAML",
    )

    build_m = sub.add_parser(
        "build-model",
        help="Build a PyTorch model from an architecture YAML/JSON (no training)",
    )
    build_m.add_argument(
        "--config",
        default="configs/models/baseline.yaml",
        help="Path to architecture YAML/JSON",
    )
    build_m.add_argument(
        "--out",
        default=None,
        help="Optional path to save architecture summary text",
    )

    inspect_m = sub.add_parser(
        "inspect-model",
        help="Print a text diagram of an architecture YAML/JSON",
    )
    inspect_m.add_argument(
        "--config",
        default="configs/models/baseline.yaml",
        help="Path to architecture YAML/JSON",
    )
    inspect_m.add_argument(
        "--out",
        default=None,
        help="Optional path to export the summary",
    )

    validate_m = sub.add_parser(
        "validate-model",
        help="Validate an architecture YAML/JSON against Phase 3 constraints",
    )
    validate_m.add_argument(
        "--config",
        default="configs/models/baseline.yaml",
        help="Path to architecture YAML/JSON",
    )

    opt = sub.add_parser(
        "optimize",
        help="Run Standard PSO or SAPSO from YAML (algorithm selected in config)",
    )
    opt.add_argument(
        "--config",
        default="configs/pso/standard.yaml",
        help="Path to PSO YAML config",
    )
    opt.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory (overrides config experiment.artifacts_root)",
    )
    opt.add_argument(
        "--dry-run",
        action="store_true",
        help="Use mock fitness (no neural training)",
    )
    opt.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose progress logging",
    )

    cmp = sub.add_parser(
        "compare-optimizers",
        help="Compare Standard PSO vs SAPSO under identical seeds (Phase 5)",
    )
    cmp.add_argument(
        "--config",
        default="configs/optimization/pso_vs_sapso.yaml",
        help="Comparison YAML config",
    )
    cmp.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )

    run_loop = sub.add_parser(
        "run-loop",
        help="Run the closed-loop controller (Phase 6)",
    )
    run_loop.add_argument(
        "--config",
        default="configs/closed_loop/default.yaml",
        help="Closed-loop YAML config",
    )
    run_loop.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )
    run_loop.add_argument(
        "--dry-run",
        action="store_true",
        help="Force mock fitness (no neural training)",
    )
    run_loop.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Override closed_loop.max_cycles",
    )

    sim_loop = sub.add_parser(
        "simulate-loop",
        help="Simulate full closed-loop lifecycle without deployment (Phase 6)",
    )
    sim_loop.add_argument(
        "--config",
        default="configs/closed_loop/simulate.yaml",
        help="Simulation YAML config",
    )
    sim_loop.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )
    sim_loop.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Override closed_loop.max_cycles",
    )

    inspect_loop = sub.add_parser(
        "inspect-loop",
        help="Inspect a closed-loop artifact run (Phase 6)",
    )
    inspect_loop.add_argument(
        "--run-dir",
        required=True,
        help="Path to closed-loop artifact directory",
    )

    dash = sub.add_parser(
        "dashboard",
        help="Launch the AI Operations Dashboard (Streamlit, Phase 8)",
    )
    dash.add_argument("--port", type=int, default=8501, help="Streamlit server port")
    dash.add_argument(
        "--demo",
        action="store_true",
        help="Start in Demo Mode (synthetic/replay data, no training)",
    )
    dash.add_argument(
        "--headless",
        action="store_true",
        help="Run Streamlit headless (CI / remote)",
    )

    api_p = sub.add_parser("api", help="Start FastAPI control plane (Phase 9)")
    api_p.add_argument("--host", default=None, help="Bind host (default from config)")
    api_p.add_argument("--port", type=int, default=None, help="Bind port (default 8000)")
    api_p.add_argument("--reload", action="store_true", help="Auto-reload (dev)")
    api_p.add_argument(
        "--config",
        default="configs/api/default.yaml",
        help="API YAML config",
    )

    serve_p = sub.add_parser(
        "serve",
        help="Start API + dashboard together (Phase 9)",
    )
    serve_p.add_argument("--api-port", type=int, default=8000, help="API port")
    serve_p.add_argument("--dashboard-port", type=int, default=8501, help="Dashboard port")
    serve_p.add_argument("--demo", action="store_true", help="Enable demo mode")
    serve_p.add_argument("--headless", action="store_true", help="Headless Streamlit")
    serve_p.add_argument(
        "--api-only",
        action="store_true",
        help="Start API only (no dashboard process)",
    )

    status_p = sub.add_parser("status", help="Query API /api/v1/status (Phase 9)")
    status_p.add_argument(
        "--api-url",
        default=None,
        help="API base URL (default EVONAS_API_URL or http://127.0.0.1:8000)",
    )

    learn = sub.add_parser(
        "learn",
        help="Run continuous learning cycle(s) — recommendations only (Phase 7)",
    )
    learn.add_argument(
        "--config",
        default="configs/continuous_learning/default.yaml",
        help="Continuous learning YAML config",
    )
    learn.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )
    learn.add_argument(
        "--cycles",
        type=int,
        default=2,
        help="Number of simulation cycles",
    )

    detect = sub.add_parser(
        "detect-data",
        help="Detect dataset changes (Phase 7 simulation)",
    )
    detect.add_argument(
        "--config",
        default="configs/continuous_learning/default.yaml",
        help="Continuous learning YAML config",
    )
    detect.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )

    replay_l = sub.add_parser(
        "replay-learning",
        help="Deterministically replay a learning history JSON (Phase 7)",
    )
    replay_l.add_argument(
        "--history",
        required=True,
        help="Path to learning_history.json",
    )
    replay_l.add_argument(
        "--out",
        default=None,
        help="Output artifacts directory",
    )

    bench = sub.add_parser(
        "benchmark",
        help="Run scientific benchmark suite (Phase 10)",
    )
    bench.add_argument(
        "--config",
        default="configs/benchmarks/default.yaml",
        help="Benchmark suite YAML",
    )
    bench.add_argument("--out", default=None, help="Output artifacts directory")
    bench.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Use mock fitness (default true for research CI)",
    )

    exp = sub.add_parser("experiment", help="List/show research experiments (Phase 10)")
    exp_sub = exp.add_subparsers(dest="experiment_command")
    exp_list = exp_sub.add_parser("list", help="List registered experiments")
    exp_list.add_argument("--limit", type=int, default=50)
    exp_show = exp_sub.add_parser("show", help="Show one experiment")
    exp_show.add_argument("experiment_id", help="Experiment id")

    cmp_r = sub.add_parser(
        "compare",
        help="Compare optimizers (legacy PSO vs SAPSO or research suite)",
    )
    cmp_r.add_argument(
        "--config",
        default="configs/optimization/pso_vs_sapso.yaml",
        help="Comparison or suite YAML",
    )
    cmp_r.add_argument("--out", default=None, help="Output directory")
    cmp_r.add_argument(
        "--suite",
        action="store_true",
        help="Force multi-algorithm research suite mode",
    )

    report_p = sub.add_parser(
        "report",
        help="Generate research report from a run directory (Phase 10)",
    )
    report_p.add_argument("--run-dir", required=True, help="Research run directory")
    report_p.add_argument("--out", default=None, help="Optional report output path")

    reg = sub.add_parser("registry", help="Governance registry (Phase 11)")
    reg_sub = reg.add_subparsers(dest="registry_command")
    reg_sub.add_parser("sync", help="Index existing artifacts into the registry")
    reg_sub.add_parser("overview", help="Show registry counts / graphs")
    reg_search = reg_sub.add_parser("search", help="Search registry metadata")
    reg_search.add_argument("--q", default=None)
    reg_search.add_argument("--kind", default=None)
    reg_search.add_argument("--optimizer", default=None)
    reg_search.add_argument("--limit", type=int, default=50)

    models = sub.add_parser("models", help="Model registry commands (Phase 11)")
    models_sub = models.add_subparsers(dest="models_command")
    models_list = models_sub.add_parser("list", help="List models")
    models_list.add_argument("--limit", type=int, default=50)
    models_show = models_sub.add_parser("show", help="Show a model")
    models_show.add_argument("model_id")
    models_show.add_argument("--version", default=None)
    models_stage = models_sub.add_parser("stage", help="Set model stage")
    models_stage.add_argument("model_id")
    models_stage.add_argument("version")
    models_stage.add_argument("stage", choices=["none", "staging", "production", "archived"])
    models_stage.add_argument("--reason", default="")

    # Alias: experiments registry list (governance)
    gov_exp = sub.add_parser("experiments", help="List governance experiment records (Phase 11)")
    gov_exp.add_argument("--limit", type=int, default=50)

    lin = sub.add_parser("lineage", help="Show lineage graph for an object id (Phase 11)")
    lin.add_argument("object_id")

    arts = sub.add_parser("artifacts", help="List governed artifacts (Phase 11)")
    arts.add_argument("--limit", type=int, default=50)

    return parser


def _load_architecture(path: str):
    from evonas.domain.architecture.factory import ArchitectureFactory

    return ArchitectureFactory().from_yaml(path) if path.endswith(
        (".yaml", ".yml")
    ) else ArchitectureFactory().from_json(path)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(level="INFO", json_logs=False)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        print(__version__)
        return 0

    if args.command == "doctor":
        print(f"evonas {__version__}")
        print(f"cwd ok: {Path('.').resolve()}")
        print(f"configs present: {(Path('configs') / 'default.yaml').exists()}")
        try:
            import torch

            print(f"torch: {torch.__version__}")
        except ImportError:
            print("torch: not installed (pip install 'evonas[pytorch]')")
        return 0

    if args.command == "prepare-dataset":
        manager = DatasetManager(args.config)
        manager.prepare()
        checksums = manager.checksums()
        schema = manager.get_schema()
        print(f"prepared dataset={manager.name}")
        print(f"schema={schema.name}@{schema.version} shape={schema.input_shape}")
        print(f"raw_features_checksum={checksums['raw_features']}")
        return 0

    if args.command in {"train", "train-baseline"}:
        from evonas.application.train_baseline import TrainBaselineUseCase

        summary = TrainBaselineUseCase().run(args.config)
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "build-model":
        from evonas.domain.architecture.complexity import estimate_complexity
        from evonas.domain.architecture.visualization import ArchitectureVisualizer
        from evonas.infrastructure.training.model_factory import ModelFactory

        model, spec = ModelFactory().create(args.config)
        report = estimate_complexity(spec)
        diagram = ArchitectureVisualizer().summarize(spec)
        if args.out:
            ArchitectureVisualizer().export_text(spec, args.out)
        print(diagram)
        print(
            json.dumps(
                {
                    "name": spec.name,
                    "arch_id": spec.arch_id(),
                    "params": ModelFactory().builder().count_parameters(model),
                    "complexity": report.to_dict(),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "inspect-model":
        from evonas.domain.architecture.visualization import ArchitectureVisualizer

        spec = _load_architecture(args.config)
        viz = ArchitectureVisualizer()
        text = viz.export_text(spec, args.out) if args.out else viz.summarize(spec)
        print(text)
        return 0

    if args.command == "validate-model":
        from evonas.domain.architecture.constraints import ArchitectureValidator
        from evonas.domain.architecture.serializer import ArchitectureSerializer

        path = Path(args.config)
        spec = ArchitectureSerializer().load(path)
        result = ArchitectureValidator().validate(spec)
        payload = {
            "ok": result.ok,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "name": spec.name,
            "arch_id": spec.arch_id() if result.ok or spec.name else None,
            "depth": spec.depth,
        }
        print(json.dumps(payload, indent=2))
        return 0 if result.ok else 1

    if args.command == "optimize":
        from evonas.application.optimize import OptimizeUseCase

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        summary = OptimizeUseCase().run(
            args.config,
            output_dir=args.out,
            dry_run=bool(args.dry_run),
            verbose=bool(args.verbose),
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0

    if args.command == "compare-optimizers":
        from evonas.application.compare_optimizers import CompareOptimizersUseCase

        comparison = CompareOptimizersUseCase().run(args.config, output_dir=args.out)
        print(json.dumps(comparison, indent=2, default=str))
        return 0

    if args.command == "run-loop":
        from evonas.application.closed_loop.use_cases import RunClosedLoopUseCase

        summary = RunClosedLoopUseCase().run(
            args.config,
            output_dir=args.out,
            dry_run=bool(args.dry_run),
            max_cycles=args.max_cycles,
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0

    if args.command == "simulate-loop":
        from evonas.application.closed_loop.use_cases import RunClosedLoopUseCase

        summary = RunClosedLoopUseCase().run(
            args.config,
            output_dir=args.out,
            simulate=True,
            dry_run=True,
            max_cycles=args.max_cycles,
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0

    if args.command == "inspect-loop":
        from evonas.application.closed_loop.use_cases import InspectClosedLoopUseCase

        payload = InspectClosedLoopUseCase().inspect(args.run_dir)
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "dashboard":
        from evonas.presentation.dashboard.launcher import launch_dashboard

        return launch_dashboard(
            port=int(args.port),
            demo=bool(args.demo),
            headless=bool(args.headless),
        )

    if args.command == "api":
        from evonas.presentation.api.launcher import launch_api

        return launch_api(
            host=args.host,
            port=args.port,
            reload=bool(args.reload),
            config=args.config,
        )

    if args.command == "serve":
        from evonas.presentation.api.launcher import launch_serve

        return launch_serve(
            api_port=int(args.api_port),
            dashboard_port=int(args.dashboard_port),
            demo=bool(args.demo),
            headless=bool(args.headless),
            skip_dashboard=bool(args.api_only),
        )

    if args.command == "status":
        from evonas.presentation.api.launcher import fetch_status

        try:
            payload = fetch_status(args.api_url)
        except Exception as exc:  # noqa: BLE001
            print(f"status unavailable: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "learn":
        from evonas.application.continuous.use_cases import ContinuousLearningUseCase

        summary = ContinuousLearningUseCase().learn(
            args.config,
            output_dir=args.out,
            cycles=int(args.cycles),
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0

    if args.command == "detect-data":
        from evonas.application.continuous.use_cases import ContinuousLearningUseCase

        payload = ContinuousLearningUseCase().detect_data(
            args.config,
            output_dir=args.out,
        )
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "replay-learning":
        from evonas.application.continuous.use_cases import ContinuousLearningUseCase

        payload = ContinuousLearningUseCase().replay_learning(
            args.history,
            output_dir=args.out,
        )
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "benchmark":
        from evonas.application.research.use_cases import BenchmarkUseCase

        payload = BenchmarkUseCase().run(
            args.config,
            output_dir=args.out,
            dry_run=bool(args.dry_run),
        )
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "experiment":
        from evonas.application.research.use_cases import ExperimentUseCase

        uc = ExperimentUseCase()
        if args.experiment_command == "list":
            print(json.dumps(uc.list(limit=int(args.limit)), indent=2, default=str))
            return 0
        if args.experiment_command == "show":
            print(json.dumps(uc.show(args.experiment_id), indent=2, default=str))
            return 0
        print("Usage: evonas experiment list|show <id>")
        return 1

    if args.command == "compare":
        from evonas.application.research.use_cases import CompareResearchUseCase

        payload = CompareResearchUseCase().run(
            args.config,
            output_dir=args.out,
            suite=bool(args.suite),
        )
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "report":
        from evonas.application.research.use_cases import ReportUseCase

        payload = ReportUseCase().run(args.run_dir, out=args.out)
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.command == "registry":
        from evonas.application.registry.service import GovernanceService

        gov = GovernanceService()
        if args.registry_command == "sync":
            print(json.dumps(gov.sync(), indent=2, default=str))
            return 0
        if args.registry_command == "overview":
            print(json.dumps(gov.overview(), indent=2, default=str))
            return 0
        if args.registry_command == "search":
            print(
                json.dumps(
                    gov.search(
                        q=args.q,
                        kind=args.kind,
                        optimizer=args.optimizer,
                        limit=int(args.limit),
                    ),
                    indent=2,
                    default=str,
                )
            )
            return 0
        print("Usage: evonas registry sync|overview|search")
        return 1

    if args.command == "models":
        from evonas.application.registry.service import GovernanceService

        gov = GovernanceService()
        if args.models_command == "list":
            print(json.dumps(gov.list_models(limit=int(args.limit)), indent=2, default=str))
            return 0
        if args.models_command == "show":
            rec = gov.get_model(args.model_id, args.version)
            if rec is None:
                print(json.dumps({"error": "not_found"}, indent=2))
                return 1
            print(json.dumps(rec, indent=2, default=str))
            return 0
        if args.models_command == "stage":
            rec = gov.set_stage(
                args.model_id, args.version, args.stage, reason=str(args.reason)
            )
            print(json.dumps(rec, indent=2, default=str))
            return 0
        print("Usage: evonas models list|show|stage")
        return 1

    if args.command == "experiments":
        from evonas.application.registry.service import GovernanceService

        print(
            json.dumps(
                GovernanceService().list_experiments(limit=int(args.limit)),
                indent=2,
                default=str,
            )
        )
        return 0

    if args.command == "lineage":
        from evonas.application.registry.service import GovernanceService

        print(json.dumps(GovernanceService().lineage(args.object_id), indent=2, default=str))
        return 0

    if args.command == "artifacts":
        from evonas.application.registry.service import GovernanceService

        print(
            json.dumps(
                GovernanceService().list_artifacts(limit=int(args.limit)),
                indent=2,
                default=str,
            )
        )
        return 0

    if args.command in {"run", "replay"}:
        logger.warning(
            "Command '%s' is specified in idea.md; prefer run-loop / simulate-loop "
            "in Phase 6 (full mode wiring continues in later phases).",
            args.command,
        )
        print(
            f"'{args.command}' maps to Phase 6+ modes — use "
            "`evonas run-loop` / `evonas simulate-loop` (see idea.md)."
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
