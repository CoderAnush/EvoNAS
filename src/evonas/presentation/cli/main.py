"""EvoNAS CLI — Phase 0–3 commands (idea.md)."""

from __future__ import annotations

import argparse
import json
import logging
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

    if args.command in {"run", "replay"}:
        logger.warning(
            "Command '%s' is specified in idea.md but not implemented until later phases.",
            args.command,
        )
        print(f"'{args.command}' will be available in a later phase (see idea.md roadmap).")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
