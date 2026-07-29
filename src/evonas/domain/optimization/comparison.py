"""Comparison framework — Standard PSO vs SAPSO under identical seeds."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from evonas.domain.optimization.benchmark import BenchmarkRunner
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
from evonas.domain.optimization.sapso import SelfAdaptivePSO
from evonas.domain.optimization.adaptive import AdaptiveConfig
from evonas.domain.search_space.space import SearchSpace
from evonas.ports.search import IFitnessEvaluator

logger = logging.getLogger(__name__)


class OptimizerComparison:
    """Run Standard PSO and SAPSO on the same seeds / space / evaluator factory."""

    def __init__(self, runner: BenchmarkRunner | None = None) -> None:
        self._runner = runner or BenchmarkRunner()

    def compare(
        self,
        *,
        space: SearchSpace,
        evaluator_factory: Callable[[], IFitnessEvaluator],
        seeds: list[int],
        pso_config: StandardPSOConfig | None = None,
        adaptive_config: AdaptiveConfig | None = None,
        budget: dict[str, Any] | None = None,
        maximize: bool = True,
    ) -> dict[str, Any]:
        """Return paired comparison report."""
        cfg = pso_config or StandardPSOConfig(
            swarm_size=12, max_iterations=20, maximize=maximize, log_particles=False
        )
        adap = adaptive_config or AdaptiveConfig()

        def pso_factory() -> StandardPSO:
            return StandardPSO(cfg)

        def sapso_factory() -> SelfAdaptivePSO:
            return SelfAdaptivePSO(cfg, adaptive_config=adap)

        pso_report = self._runner.run(
            algorithm_name="standard_pso",
            space=space,
            evaluator_factory=evaluator_factory,
            optimizer_factory=pso_factory,
            seeds=seeds,
            budget=budget,
            maximize=maximize,
        )
        sapso_report = self._runner.run(
            algorithm_name="sapso",
            space=space,
            evaluator_factory=evaluator_factory,
            optimizer_factory=sapso_factory,
            seeds=seeds,
            budget=budget,
            maximize=maximize,
        )
        pso_mean = float(pso_report["aggregates"]["best_fitness"]["mean"])
        sapso_mean = float(sapso_report["aggregates"]["best_fitness"]["mean"])
        comparison = {
            "seeds": list(seeds),
            "space": space.name,
            "standard_pso": pso_report,
            "sapso": sapso_report,
            "delta_mean_fitness_sapso_minus_pso": sapso_mean - pso_mean,
            "winner": "sapso"
            if (sapso_mean > pso_mean if maximize else sapso_mean < pso_mean)
            else "standard_pso"
            if sapso_mean != pso_mean
            else "tie",
        }
        logger.info(
            "Comparison winner=%s delta_mean=%.6f",
            comparison["winner"],
            comparison["delta_mean_fitness_sapso_minus_pso"],
        )
        return comparison

    def export(self, report: dict[str, Any], path: str | Path) -> Path:
        """Write comparison JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return file_path
