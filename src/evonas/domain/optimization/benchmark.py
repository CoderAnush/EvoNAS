"""Benchmark runner — multi-seed aggregate statistics for optimizers."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from evonas.domain.optimization.result import SearchResult
from evonas.domain.search_space.space import SearchSpace
from evonas.ports.search import IFitnessEvaluator, ISearchAlgorithm

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RunOutcome:
    """Single seeded optimizer run."""

    seed: int
    algorithm: str
    best_fitness: float
    iterations: int
    evaluations: int
    seconds: float
    stopped_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize outcome."""
        return {
            "seed": self.seed,
            "algorithm": self.algorithm,
            "best_fitness": self.best_fitness,
            "iterations": self.iterations,
            "evaluations": self.evaluations,
            "seconds": self.seconds,
            "stopped_reason": self.stopped_reason,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class AggregateStats:
    """Mean / median / std / best / worst for a metric."""

    mean: float
    median: float
    std: float
    best: float
    worst: float
    n: int

    def to_dict(self) -> dict[str, float | int]:
        """Serialize aggregates."""
        return {
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "best": self.best,
            "worst": self.worst,
            "n": self.n,
        }


def _aggregate(values: list[float], *, maximize: bool = True) -> AggregateStats:
    arr = np.asarray(values, dtype=float)
    return AggregateStats(
        mean=float(arr.mean()),
        median=float(np.median(arr)),
        std=float(arr.std()),
        best=float(arr.max() if maximize else arr.min()),
        worst=float(arr.min() if maximize else arr.max()),
        n=int(arr.size),
    )


class BenchmarkRunner:
    """Run an optimizer factory across multiple seeds and aggregate results."""

    def run(
        self,
        *,
        algorithm_name: str,
        space: SearchSpace,
        evaluator_factory: Callable[[], IFitnessEvaluator],
        optimizer_factory: Callable[[], ISearchAlgorithm],
        seeds: list[int],
        budget: dict[str, Any] | None = None,
        maximize: bool = True,
    ) -> dict[str, Any]:
        """Execute independent runs and return aggregate report."""
        outcomes: list[RunOutcome] = []
        for seed in seeds:
            optimizer = optimizer_factory()
            evaluator = evaluator_factory()
            optimizer.set_evaluator(evaluator)
            started = time.perf_counter()
            optimizer.initialize(space, int(seed))
            result: SearchResult = optimizer.run(budget)
            elapsed = time.perf_counter() - started
            outcomes.append(
                RunOutcome(
                    seed=int(seed),
                    algorithm=algorithm_name,
                    best_fitness=float(result.best_fitness),
                    iterations=int(result.iterations),
                    evaluations=int(result.evaluations),
                    seconds=float(elapsed),
                    stopped_reason=result.stopped_reason,
                )
            )
            logger.info(
                "Benchmark %s seed=%d fitness=%.6f seconds=%.2f",
                algorithm_name,
                seed,
                result.best_fitness,
                elapsed,
            )
        fitnesses = [o.best_fitness for o in outcomes]
        iters = [float(o.iterations) for o in outcomes]
        seconds = [o.seconds for o in outcomes]
        report = {
            "algorithm": algorithm_name,
            "space": space.name,
            "seeds": list(seeds),
            "runs": [o.to_dict() for o in outcomes],
            "aggregates": {
                "best_fitness": _aggregate(fitnesses, maximize=maximize).to_dict(),
                "iterations": _aggregate(iters, maximize=False).to_dict(),
                "seconds": _aggregate(seconds, maximize=False).to_dict(),
            },
        }
        return report

    def export(self, report: dict[str, Any], path: str | Path) -> Path:
        """Write benchmark report JSON."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return file_path
