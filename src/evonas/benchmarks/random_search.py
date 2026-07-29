"""Random Search baseline — implements ISearchAlgorithm for research only."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from evonas.domain.common.errors import OptimizationError
from evonas.domain.fitness.types import Fitness
from evonas.domain.optimization.history import IterationRecord, SwarmHistory
from evonas.domain.optimization.particle import (
    Particle,
    ParticlePosition,
    ParticleVelocity,
    PersonalBest,
)
from evonas.domain.optimization.result import SearchResult
from evonas.domain.optimization.swarm import SwarmState
from evonas.domain.search_space.space import SearchSpace
from evonas.ports.search import IFitnessEvaluator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RandomSearchConfig:
    """Uniform random sampling budget (matched to PSO evaluation counts)."""

    n_trials: int = 240  # default ≈ swarm_size(12) * max_iterations(20)
    maximize: bool = True
    seed: int = 42
    log_every: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RandomSearchConfig:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class RandomSearch:
    """Sample genotypes uniformly in bounds; keep the best (research baseline)."""

    algorithm_name = "random_search"

    def __init__(self, config: RandomSearchConfig | None = None) -> None:
        self._config = config or RandomSearchConfig()
        self._space: SearchSpace | None = None
        self._evaluator: IFitnessEvaluator | None = None
        self._rng: np.random.Generator | None = None
        self._history = SwarmHistory(metadata={"algorithm": self.algorithm_name})
        self._best: Particle | None = None
        self._evaluations = 0
        self._initialized = False

    @property
    def config(self) -> RandomSearchConfig:
        return self._config

    def set_evaluator(self, fn: IFitnessEvaluator) -> None:
        self._evaluator = fn

    def initialize(self, space: SearchSpace, seed: int) -> None:
        self._space = space
        self._rng = np.random.default_rng(int(seed))
        self._history = SwarmHistory(
            metadata={"algorithm": self.algorithm_name, "seed": int(seed)}
        )
        self._best = None
        self._evaluations = 0
        self._initialized = True

    def step(self) -> SwarmState:
        """One random trial (compatible with ISearchAlgorithm.step)."""
        particle = self._sample_and_eval()
        return SwarmState(
            t=self._evaluations,
            particles=[particle],
            gbest_position=particle.position,
            gbest_fitness=particle.fitness,
            w=0.0,
            c1=0.0,
            c2=0.0,
            diversity=0.0,
            metadata={"algorithm": self.algorithm_name},
        )

    def run(self, budget: dict[str, Any] | None = None) -> SearchResult:
        if not self._initialized or self._space is None or self._rng is None:
            raise OptimizationError("RandomSearch not initialized", code="EN_OPT_001")
        if self._evaluator is None:
            raise OptimizationError("RandomSearch evaluator not set", code="EN_OPT_002")

        budget = budget or {}
        n_trials = int(budget.get("max_evaluations") or budget.get("n_trials") or self._config.n_trials)
        log_every = int(budget.get("log_every", self._config.log_every))

        for trial in range(1, n_trials + 1):
            particle = self._sample_and_eval()
            if log_every > 0 and (trial % log_every == 0 or trial == n_trials):
                assert self._best is not None
                self._history.append(
                    IterationRecord(
                        iteration=trial,
                        gbest_fitness=self._best.fitness,
                        gbest_position=self._best.position.as_list(),
                        mean_fitness=particle.fitness,
                        diversity=0.0,
                        evaluations=self._evaluations,
                        w=0.0,
                        c1=0.0,
                        c2=0.0,
                        particles=[],
                        metadata={"trial": trial},
                    )
                )

        assert self._best is not None
        return SearchResult(
            best_particle=self._best,
            best_fitness=float(self._best.fitness),
            best_position=self._best.position.as_list(),
            history=self._history,
            iterations=n_trials,
            evaluations=self._evaluations,
            stopped_reason="budget_exhausted",
            metadata={"algorithm": self.algorithm_name},
        )

    def get_best(self) -> Particle:
        if self._best is None:
            raise OptimizationError("No evaluations yet", code="EN_OPT_003")
        return self._best

    def get_history(self) -> SwarmHistory:
        return self._history

    def _sample_and_eval(self) -> Particle:
        assert self._space is not None and self._rng is not None and self._evaluator is not None
        lows, highs = self._space.bounds()
        values = [
            float(self._rng.uniform(lo, hi)) for lo, hi in zip(lows, highs, strict=True)
        ]
        fitness_obj = self._evaluator.evaluate(values, particle_id=f"rs_{self._evaluations}")
        value = float(fitness_obj.value) if isinstance(fitness_obj, Fitness) else float(fitness_obj)
        self._evaluations += 1
        particle = Particle(
            id=f"rs_{self._evaluations}",
            position=ParticlePosition(values),
            velocity=ParticleVelocity([0.0] * len(values)),
            fitness=value,
            personal_best=PersonalBest(ParticlePosition(values), value),
        )
        if self._best is None:
            self._best = particle
        else:
            better = (
                value > self._best.fitness
                if self._config.maximize
                else value < self._best.fitness
            )
            if better:
                self._best = particle
        return particle
