"""Minimal CLI surface for Phase 0/1 (idea.md)."""

from __future__ import annotations

import argparse
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
    return parser


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
