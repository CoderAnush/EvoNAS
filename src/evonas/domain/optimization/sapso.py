"""Self-Adaptive PSO — extends StandardPSO with AdaptiveController (Phase 5)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from evonas.domain.optimization.adaptive import AdaptiveConfig, AdaptiveController, AdaptiveParams
from evonas.domain.optimization.initialization import InitializationStrategy
from evonas.domain.optimization.particle import Particle
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
from evonas.domain.optimization.stopping import CompositeStopping
from evonas.domain.optimization.swarm import SwarmState
from evonas.domain.search_space.space import SearchSpace

logger = logging.getLogger(__name__)


class SelfAdaptivePSO(StandardPSO):
    """Standard PSO velocity equation with adaptive ``w,c1,c2`` each iteration.

    Behaviour of the fixed-coefficient parent remains unchanged when the
    adaptive controller is not used; this class only overrides the coefficient
    hook and records adaptive history.
    """

    algorithm_name = "sapso"

    def __init__(
        self,
        config: StandardPSOConfig | None = None,
        *,
        adaptive_config: AdaptiveConfig | None = None,
        controller: AdaptiveController | None = None,
        initializer: InitializationStrategy | None = None,
        stopping: CompositeStopping | None = None,
        position_repair: Callable[[Particle], None] | None = None,
        checkpoint_dir: str | Path | None = None,
    ) -> None:
        super().__init__(
            config,
            initializer=initializer,
            stopping=stopping,
            position_repair=position_repair,
            checkpoint_dir=checkpoint_dir,
        )
        self._adaptive_config = adaptive_config or AdaptiveConfig()
        self._controller = controller or AdaptiveController(self._adaptive_config)
        self._adaptive_records: list[dict[str, Any]] = []
        self._current_params = self._controller.last_params
        self._prev_gbest: float | None = None

    @property
    def adaptive_controller(self) -> AdaptiveController:
        """Expose adaptive controller for tests / analysis."""
        return self._controller

    @property
    def adaptive_history(self) -> list[dict[str, Any]]:
        """Per-iteration adaptive records."""
        return list(self._adaptive_records)

    def initialize(self, space: SearchSpace, seed: int) -> None:
        """Initialize swarm then seed adaptive state."""
        self._controller.reset()
        self._adaptive_records.clear()
        self._prev_gbest = None
        super().initialize(space, seed)
        # Adapt once after initial evaluation so recorded coeffs are adaptive.
        self._adapt()
        # Rewrite last history entry with adapted coeffs
        if self._history.records:
            last = self._history.records[-1]
            last.w = self._current_params.w
            last.c1 = self._current_params.c1
            last.c2 = self._current_params.c2
            last.metadata = {
                **last.metadata,
                "adaptive": self._current_params.to_dict(),
            }
        self._history.metadata["algorithm"] = self.algorithm_name
        self._history.metadata["adaptive_config"] = {
            "w_min": self._adaptive_config.w_min,
            "w_max": self._adaptive_config.w_max,
            "c_min": self._adaptive_config.c_min,
            "c_max": self._adaptive_config.c_max,
            "delta_collapse": self._adaptive_config.delta_collapse,
        }

    def step(self) -> SwarmState:
        """Adapt coefficients, then run one StandardPSO step with those coeffs."""
        self._adapt()
        state = super().step()
        # Annotate recorded iteration with adaptive metadata
        if self._history.records:
            last = self._history.records[-1]
            last.metadata = {
                **last.metadata,
                "adaptive": self._current_params.to_dict(),
                "phase": self._current_params.phase.value,
            }
        return state

    def _get_velocity_coeffs(self) -> tuple[float, float, float]:
        """Return latest adaptive coefficients."""
        p = self._current_params
        return p.w, p.c1, p.c2

    def _adapt(self) -> AdaptiveParams:
        self._require_ready()
        assert self._space is not None
        gbest = float(self._swarm.gbest_fitness or 0.0)
        stats = self._controller.compute_stats(
            particles=self._swarm.particles,
            space=self._space,
            iteration=self._swarm.iteration,
            max_iterations=self._config.max_iterations,
            gbest_fitness=gbest,
            no_improve_count=self._no_improve,
            previous_gbest=self._prev_gbest,
            maximize=self._config.maximize,
        )
        params = self._controller.update(stats)
        self._current_params = params
        self._prev_gbest = gbest
        record = {
            "iteration": stats.iteration,
            **params.to_dict(),
            "stats": stats.to_dict(),
        }
        self._adaptive_records.append(record)
        return params

    def export_adaptive_history(self) -> dict[str, Any]:
        """Export w/c1/c2/diversity/phase trajectories."""
        return {
            "algorithm": self.algorithm_name,
            "records": list(self._adaptive_records),
            "transitions": list(self._controller.state_machine.transitions),
            "curves": {
                "w": [r["w"] for r in self._adaptive_records],
                "c1": [r["c1"] for r in self._adaptive_records],
                "c2": [r["c2"] for r in self._adaptive_records],
                "diversity": [r["normalized_diversity"] for r in self._adaptive_records],
                "phase": [r["phase"] for r in self._adaptive_records],
                "gbest": [
                    r.get("stats", {}).get("gbest_fitness") for r in self._adaptive_records
                ],
            },
        }
