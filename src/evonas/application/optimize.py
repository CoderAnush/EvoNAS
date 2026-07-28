"""Application use-case: Standard PSO architecture optimization."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from evonas import __version__
from evonas.domain.fitness.types import FitnessConfig
from evonas.domain.optimization.adapter import SearchSpaceAdapter
from evonas.domain.optimization.cache import EvaluationCache
from evonas.domain.optimization.initialization import get_initialization
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
from evonas.domain.search_space.space import SearchSpace
from evonas.domain.training.types import TrainConfig
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.data.factory import create_dataset_manager
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager
from evonas.infrastructure.optimization.architecture_fitness import ArchitectureFitnessEvaluator
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator
from evonas.infrastructure.optimization.visualization import PSOVisualizer

logger = logging.getLogger(__name__)


class OptimizeUseCase:
    """Run Standard PSO from a YAML config and persist reproducible artifacts."""

    def __init__(
        self,
        *,
        config_manager: ConfigurationManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigurationManager()

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Execute optimization; return summary dict."""
        cfg_path = Path(config_path)
        cfg = self._config_manager.load(cfg_path)
        seed = int(cfg.get("seed", 42))
        run_id = str(cfg.get("run_id", "pso_standard"))

        opt_block = dict(cfg.get("optimization", {}))
        pso_cfg = StandardPSOConfig.from_dict(
            {
                **opt_block,
                "seed": seed,
                "w": float(opt_block.get("w", 0.729)),
                "c1": float(opt_block.get("c1", 1.49445)),
                "c2": float(opt_block.get("c2", 1.49445)),
                "kappa": float(opt_block.get("velocity", {}).get("kappa", opt_block.get("kappa", 0.2)))
                if isinstance(opt_block.get("velocity"), dict)
                else float(opt_block.get("kappa", 0.2)),
                "init_velocity_scale": float(opt_block.get("init_velocity_scale", 0.2)),
                "swarm_size": int(opt_block.get("swarm_size", 8)),
                "max_iterations": int(opt_block.get("max_iterations", 5)),
                "maximize": str(cfg.get("fitness", {}).get("sense", "maximize")) == "maximize",
                "target_fitness": opt_block.get("target_fitness"),
                "max_no_improve": opt_block.get("max_no_improve"),
                "checkpoint_every": int(opt_block.get("checkpoint_every", 5)),
                "log_particles": bool(opt_block.get("log_particles", True)),
            }
        )

        space_path = cfg.get("search_space", {}).get("path", "configs/search_spaces/cnn_quick.yaml")
        if isinstance(cfg.get("search_space"), str):
            space_path = cfg["search_space"]
        space = SearchSpace.from_yaml(space_path)

        # Align space with dataset schema when available
        dataset_cfg = cfg.get("dataset", {})
        data_mgr = None
        if isinstance(dataset_cfg, dict) and dataset_cfg.get("config_path") and not dry_run:
            data_mgr = create_dataset_manager(
                str(dataset_cfg["config_path"]),
                treat_as_dataset_config=True,
                config_manager=self._config_manager,
            )
            data_mgr.prepare()
            schema = data_mgr.get_schema()
            space = SearchSpace(
                name=space.name,
                genes=space.genes,
                input_shape=schema.input_shape,
                num_classes=int(schema.num_classes or space.num_classes),
                metadata={**(space.metadata or {}), "aligned": True},
            )

        artifacts_root = output_dir or cfg.get("experiment", {}).get(
            "artifacts_root", "artifacts/optimization"
        )
        artifacts = ArtifactManager(root=artifacts_root)
        run_dir = artifacts.create_run(run_id)
        artifacts.copy_config(run_dir, cfg_path)
        (run_dir / "config.snapshot.json").write_text(
            json.dumps(
                {
                    "evonas_version": __version__,
                    "seed": seed,
                    "config_path": str(cfg_path),
                    "config_hash": self._config_manager.hash(cfg),
                    "pso": {
                        "w": pso_cfg.w,
                        "c1": pso_cfg.c1,
                        "c2": pso_cfg.c2,
                        "swarm_size": pso_cfg.swarm_size,
                        "max_iterations": pso_cfg.max_iterations,
                    },
                    "search_space": space.to_dict(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        init_name = str(opt_block.get("initialization", "random"))
        initializer = get_initialization(init_name)
        adapter = SearchSpaceAdapter(space)

        fitness_mode = str(cfg.get("fitness", {}).get("mode", "architecture")).lower()
        if dry_run:
            fitness_mode = "mock"

        pso = StandardPSO(
            pso_cfg,
            initializer=initializer,
            position_repair=None if fitness_mode == "mock" else adapter.repair_particle,
            checkpoint_dir=run_dir / "checkpoints",
        )

        if fitness_mode == "mock":
            landscape = str(cfg.get("fitness", {}).get("landscape", "sphere"))
            evaluator: Any = MockFitnessEvaluator(
                landscape=landscape,
                maximize=pso_cfg.maximize,
            )
            logger.info("Using mock fitness landscape=%s dry_run=%s", landscape, dry_run)
        else:
            if data_mgr is None:
                data_mgr = create_dataset_manager(
                    str(dataset_cfg.get("config_path", "configs/datasets/toy_quick.yaml")),
                    treat_as_dataset_config=True,
                    config_manager=self._config_manager,
                )
                data_mgr.prepare()
            train_raw = dict(cfg.get("training", {}))
            train_raw.setdefault("seed", seed)
            train_cfg = TrainConfig.from_dict(train_raw)
            cache = EvaluationCache(disk_dir=run_dir / "cache" / "evals")
            evaluator = ArchitectureFitnessEvaluator(
                adapter,
                data_mgr,
                train_config=train_cfg,
                fitness_config=FitnessConfig.from_dict(dict(cfg.get("fitness", {}))),
                cache=cache,
                subset_fraction=float(cfg.get("data", {}).get("subset_fraction", 1.0)),
                subset_seed=int(cfg.get("data", {}).get("subset_seed", seed)),
            )

        pso.set_evaluator(evaluator)
        pso.initialize(space, seed)
        result = pso.run()
        history = result.history
        history.export_json(run_dir / "history.json")
        history.export_jsonl(run_dir / "history.jsonl")
        history.export_csv(run_dir / "history.csv")

        best_spec = None
        if fitness_mode != "mock":
            try:
                best_spec = adapter.decode(result.best_position, name="pso_best")
                (run_dir / "best_architecture.json").write_text(
                    json.dumps(best_spec.to_dict(), indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not decode best architecture: %s", exc)

        plots = PSOVisualizer().plot_all(history, run_dir / "plots")
        summary: dict[str, Any] = {
            "run_id": run_id,
            "algorithm": "standard_pso",
            "dry_run": dry_run,
            "fitness_mode": fitness_mode,
            "best_fitness": result.best_fitness,
            "best_position": result.best_position,
            "iterations": result.iterations,
            "evaluations": result.evaluations,
            "stopped_reason": result.stopped_reason,
            "best_arch_id": best_spec.arch_id() if best_spec else None,
            "best_architecture": best_spec.name if best_spec else None,
            "plots": plots,
            "run_dir": str(run_dir),
            "cache": getattr(evaluator, "cache_stats", lambda: {})(),
            "evonas_version": __version__,
            "seed": seed,
        }
        if verbose:
            logger.info("PSO summary: %s", json.dumps(summary, indent=2, default=str))
        artifacts.write_json(run_dir, "summary.json", summary)
        artifacts.write_json(run_dir, "result.json", result.to_dict())
        return summary
