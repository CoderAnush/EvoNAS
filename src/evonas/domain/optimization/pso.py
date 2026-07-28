"""Standard Particle Swarm Optimization — fixed w, c1, c2 (idea.md Phase 4)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from evonas.domain.common.errors import OptimizationError
from evonas.domain.fitness.types import Fitness
from evonas.domain.optimization.history import IterationRecord, SwarmHistory
from evonas.domain.optimization.initialization import (
    InitializationStrategy,
    RandomInitialization,
)
from evonas.domain.optimization.particle import Particle
from evonas.domain.optimization.position import project_to_bounds, update_position
from evonas.domain.optimization.result import SearchResult
from evonas.domain.optimization.stopping import CompositeStopping, StoppingContext
from evonas.domain.optimization.swarm import Swarm, SwarmState
from evonas.domain.optimization.velocity import VelocityConfig, update_velocity
from evonas.domain.search_space.space import SearchSpace
from evonas.ports.search import IFitnessEvaluator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StandardPSOConfig:
    """Fixed-coefficient Standard PSO configuration (Clerc-style defaults)."""

    swarm_size: int = 10
    max_iterations: int = 20
    w: float = 0.729
    c1: float = 1.49445
    c2: float = 1.49445
    kappa: float = 0.2
    init_velocity_scale: float = 0.2
    maximize: bool = True
    target_fitness: float | None = None
    max_no_improve: int | None = None
    checkpoint_every: int = 5
    log_particles: bool = True
    seed: int = 42

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StandardPSOConfig:
        """Load from optimization YAML block."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class StandardPSO:
    """Classical PSO with fixed inertia and acceleration coefficients.

    Does **not** adapt w/c1/c2 — that is Phase 5 (SAPSO).
    Never touches neural networks; only vectors + injected evaluator.
    """

    algorithm_name = "standard_pso"

    def __init__(
        self,
        config: StandardPSOConfig | None = None,
        *,
        initializer: InitializationStrategy | None = None,
        stopping: CompositeStopping | None = None,
        position_repair: Callable[[Particle], None] | None = None,
        checkpoint_dir: str | Path | None = None,
    ) -> None:
        self._config = config or StandardPSOConfig()
        self._initializer = initializer or RandomInitialization()
        self._stopping = stopping or CompositeStopping()
        self._position_repair = position_repair
        self._checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self._space: SearchSpace | None = None
        self._swarm = Swarm()
        self._evaluator: IFitnessEvaluator | None = None
        self._rng: np.random.Generator | None = None
        self._history = SwarmHistory(metadata={"algorithm": self.algorithm_name})
        self._evaluations = 0
        self._no_improve = 0
        self._initialized = False

    @property
    def config(self) -> StandardPSOConfig:
        """Active PSO config."""
        return self._config

    def set_evaluator(self, fn: IFitnessEvaluator) -> None:
        """Inject fitness evaluator."""
        self._evaluator = fn

    def initialize(self, space: SearchSpace, seed: int) -> None:
        """Initialize swarm for ``space`` with ``seed``."""
        self._space = space
        self._rng = np.random.default_rng(int(seed))
        self._history = SwarmHistory(
            metadata={
                "algorithm": self.algorithm_name,
                "seed": seed,
                "space": space.name,
                "config": {
                    "swarm_size": self._config.swarm_size,
                    "max_iterations": self._config.max_iterations,
                    "w": self._config.w,
                    "c1": self._config.c1,
                    "c2": self._config.c2,
                },
            }
        )
        self._evaluations = 0
        self._no_improve = 0
        particles = self._initializer.initialize(
            space,
            self._config.swarm_size,
            seed=seed,
            init_velocity_scale=self._config.init_velocity_scale,
        )
        self._swarm = Swarm(particles)
        self._evaluate_all()
        for particle in self._swarm.particles:
            particle.update_personal_best(maximize=self._config.maximize)
        self._swarm.update_global_best(maximize=self._config.maximize)
        self._initialized = True
        self._record_state()
        logger.info(
            "Initialized StandardPSO space=%s size=%d gbest=%.6f",
            space.name,
            self._swarm.size,
            self._swarm.gbest_fitness,
        )

    def step(self) -> SwarmState:
        """Execute one velocity/position/evaluate/update cycle."""
        self._require_ready()
        assert self._space is not None and self._rng is not None
        assert self._swarm.gbest_position is not None
        lows, highs = self._space.bounds()
        vel_cfg = VelocityConfig(
            w=self._config.w,
            c1=self._config.c1,
            c2=self._config.c2,
            kappa=self._config.kappa,
        )
        prev_best = float(self._swarm.gbest_fitness or float("-inf"))
        for particle in self._swarm.particles:
            update_velocity(
                particle,
                self._swarm.gbest_position,
                lows,
                highs,
                vel_cfg,
                self._rng,
            )
            update_position(particle)
            project_to_bounds(particle, lows, highs)
            if self._position_repair is not None:
                try:
                    self._position_repair(particle)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("position repair failed for %s: %s", particle.id, exc)
            fitness = self._evaluate_particle(particle)
            particle.fitness = fitness.value
            particle.update_personal_best(maximize=self._config.maximize)
        self._swarm.update_global_best(maximize=self._config.maximize)
        self._swarm.advance()
        new_best = float(self._swarm.gbest_fitness or prev_best)
        improved = (
            new_best > prev_best + 1e-15
            if self._config.maximize
            else new_best < prev_best - 1e-15
        )
        self._no_improve = 0 if improved else self._no_improve + 1
        state = self._record_state()
        if (
            self._checkpoint_dir is not None
            and self._config.checkpoint_every > 0
            and state.t % self._config.checkpoint_every == 0
        ):
            self._write_checkpoint(state)
        return state

    def run(self, budget: dict[str, Any] | None = None) -> SearchResult:
        """Run until stopping criteria (optionally overridden by budget)."""
        self._require_ready()
        budget = budget or {}
        max_iters = int(budget.get("max_iterations", self._config.max_iterations))
        target = budget.get("target_fitness", self._config.target_fitness)
        max_no_improve = budget.get("max_no_improve", self._config.max_no_improve)
        reason = "max_iterations"
        while True:
            ctx = StoppingContext(
                iteration=self._swarm.iteration,
                max_iterations=max_iters,
                best_fitness=float(self._swarm.gbest_fitness or 0.0),
                evaluations=self._evaluations,
                no_improve_count=self._no_improve,
                target_fitness=float(target) if target is not None else None,
                max_no_improve=int(max_no_improve) if max_no_improve is not None else None,
            )
            decision = self._stopping.evaluate(ctx)
            if decision.stop:
                reason = decision.reason
                break
            if self._swarm.iteration >= max_iters:
                reason = "max_iterations"
                break
            self.step()
        best = self.get_best()
        return SearchResult(
            best_particle=best,
            best_fitness=float(self._swarm.gbest_fitness or best.fitness),
            best_position=(
                self._swarm.gbest_position.as_list()
                if self._swarm.gbest_position
                else best.position.as_list()
            ),
            history=self._history,
            iterations=self._swarm.iteration,
            evaluations=self._evaluations,
            stopped_reason=reason,
            metadata={"algorithm": self.algorithm_name},
        )

    def get_best(self) -> Particle:
        """Return a particle representing the global best."""
        self._require_ready()
        if self._swarm.gbest_position is None or self._swarm.gbest_fitness is None:
            raise OptimizationError("global best unavailable")
        # Prefer live particle matching gbest fitness; else synthesize.
        for particle in self._swarm.particles:
            if abs(particle.pbest_fitness - self._swarm.gbest_fitness) < 1e-15:
                return particle
        return Particle.from_vectors(
            "gbest",
            self._swarm.gbest_position.as_list(),
            [0.0] * len(self._swarm.gbest_position),
            fitness=self._swarm.gbest_fitness,
        )

    def get_history(self) -> SwarmHistory:
        """Return swarm history."""
        return self._history

    def _evaluate_all(self) -> None:
        for particle in self._swarm.particles:
            fitness = self._evaluate_particle(particle)
            particle.fitness = fitness.value

    def _evaluate_particle(self, particle: Particle) -> Fitness:
        if self._evaluator is None:
            raise OptimizationError("fitness evaluator not set")
        try:
            fitness = self._evaluator.evaluate(
                particle.position.as_list(), particle_id=particle.id
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("evaluation failed for %s: %s", particle.id, exc)
            fitness = Fitness(
                value=float("-inf") if self._config.maximize else float("inf"),
                components={"fail": 1.0},
                sense="maximize" if self._config.maximize else "minimize",
                metadata={"error": str(exc)},
            )
        self._evaluations += 1
        particle.metadata["last_fitness"] = fitness.to_dict()
        return fitness

    def _record_state(self) -> SwarmState:
        state = self._swarm.snapshot(
            w=self._config.w, c1=self._config.c1, c2=self._config.c2
        )
        self._history.append(
            IterationRecord.from_swarm_state(
                state,
                evaluations=self._evaluations,
                include_particles=self._config.log_particles,
            )
        )
        return state

    def _write_checkpoint(self, state: SwarmState) -> None:
        assert self._checkpoint_dir is not None
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        path = self._checkpoint_dir / f"swarm_iter_{state.t:04d}.json"
        import json

        path.write_text(json.dumps(state.to_dict(), indent=2, default=str), encoding="utf-8")
        logger.info("Wrote swarm checkpoint %s", path)

    def _require_ready(self) -> None:
        if not self._initialized or self._space is None:
            raise OptimizationError("StandardPSO.initialize() must be called first")
        if self._evaluator is None:
            raise OptimizationError("StandardPSO.set_evaluator() must be called first")
