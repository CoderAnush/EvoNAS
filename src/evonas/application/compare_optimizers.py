"""Compare Standard PSO vs SAPSO under identical seeds."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas import __version__
from evonas.domain.optimization.adaptive import AdaptiveConfig
from evonas.domain.optimization.comparison import OptimizerComparison
from evonas.domain.optimization.pso import StandardPSOConfig
from evonas.domain.search_space.space import SearchSpace
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator

logger = logging.getLogger(__name__)


class CompareOptimizersUseCase:
    """Benchmark Standard PSO against SAPSO and export a comparison report."""

    def __init__(self, *, config_manager: ConfigurationManager | None = None) -> None:
        self._config_manager = config_manager or ConfigurationManager()

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Execute multi-seed comparison (defaults to mock fitness for speed)."""
        cfg = self._config_manager.load(config_path)
        seed0 = int(cfg.get("seed", 42))
        n_seeds = int(cfg.get("comparison", {}).get("n_seeds", cfg.get("n_seeds", 5)))
        seeds = list(cfg.get("comparison", {}).get("seeds") or [seed0 + i for i in range(n_seeds)])

        space_path = cfg.get("search_space", {}).get(
            "path", "configs/search_spaces/sphere_2d.yaml"
        )
        if isinstance(cfg.get("search_space"), str):
            space_path = cfg["search_space"]
        space = SearchSpace.from_yaml(space_path)

        opt = dict(cfg.get("optimization", {}))
        pso_cfg = StandardPSOConfig(
            swarm_size=int(opt.get("swarm_size", 12)),
            max_iterations=int(opt.get("max_iterations", 20)),
            w=float(opt.get("w", 0.729)),
            c1=float(opt.get("c1", 1.49445)),
            c2=float(opt.get("c2", 1.49445)),
            maximize=str(cfg.get("fitness", {}).get("sense", "maximize")) == "maximize",
            log_particles=False,
            seed=seed0,
        )
        adaptive_cfg = AdaptiveConfig.from_dict(dict(cfg.get("adaptation", {})))
        landscape = str(cfg.get("fitness", {}).get("landscape", "sphere"))
        maximize = pso_cfg.maximize

        def evaluator_factory() -> MockFitnessEvaluator:
            return MockFitnessEvaluator(landscape=landscape, maximize=maximize)

        report = OptimizerComparison().compare(
            space=space,
            evaluator_factory=evaluator_factory,
            seeds=seeds,
            pso_config=pso_cfg,
            adaptive_config=adaptive_cfg,
            maximize=maximize,
        )
        report["evonas_version"] = __version__
        report["config_path"] = str(config_path)

        out_root = output_dir or cfg.get("experiment", {}).get(
            "artifacts_root", "artifacts/optimization"
        )
        artifacts = ArtifactManager(root=out_root)
        run_dir = artifacts.create_run(str(cfg.get("run_id", "pso_vs_sapso")))
        artifacts.copy_config(run_dir, config_path)
        artifacts.write_json(run_dir, "comparison.json", report)
        (run_dir / "comparison_summary.txt").write_text(
            (
                f"winner={report['winner']}\n"
                f"delta_mean_fitness={report['delta_mean_fitness_sapso_minus_pso']:.6f}\n"
                f"pso_mean={report['standard_pso']['aggregates']['best_fitness']['mean']:.6f}\n"
                f"sapso_mean={report['sapso']['aggregates']['best_fitness']['mean']:.6f}\n"
            ),
            encoding="utf-8",
        )
        logger.info("Wrote comparison report to %s", run_dir)
        report["run_dir"] = str(run_dir)
        return report
