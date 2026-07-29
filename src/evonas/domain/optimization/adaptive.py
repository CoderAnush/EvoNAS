"""Self-Adaptive PSO controller, scheduler, and state machine (idea.md §15).

This module NEVER performs optimization. It only maps swarm behaviour statistics
to ``(w, c1, c2)`` using deterministic, configurable rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

import numpy as np

from evonas.domain.optimization.diversity import mean_velocity_magnitude, normalized_diversity
from evonas.domain.optimization.particle import Particle
from evonas.domain.search_space.space import SearchSpace

logger = logging.getLogger(__name__)


class AdaptivePhase(str, Enum):
    """Optimization behavioural phase (adaptive state machine)."""

    EXPLORATION = "exploration"
    BALANCED = "balanced"
    EXPLOITATION = "exploitation"
    STAGNATION_RECOVERY = "stagnation_recovery"


@dataclass(frozen=True, slots=True)
class AdaptiveConfig:
    """All adaptive thresholds and coefficient bounds (nothing hardcoded in rules)."""

    # Inertia bounds and schedule weights (idea.md §15.4 / REQ-OPT-005)
    w_min: float = 0.4
    w_max: float = 0.9
    w_refine: float = 0.35
    alpha: float = 0.5
    beta: float = 0.3
    gamma: float = 0.2
    eta_slow: float = 0.001
    eta_good: float = 0.01
    improvement_window: int = 5

    # Acceleration (idea.md §15.5)
    c_min: float = 0.5
    c_max: float = 2.5
    c_sum: float = 4.1
    delta_collapse: float = 0.05
    delta_high: float = 0.35

    # Stagnation / convergence phase thresholds
    stagnation_iters: int = 8
    converge_eta: float = 0.002
    converge_diversity: float = 0.25

    # Initial coefficients (used at t=0 before first adapt)
    w0: float = 0.729
    c1_0: float = 1.49445
    c2_0: float = 1.49445

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdaptiveConfig:
        """Load from YAML ``adaptation:`` / nested inertia & acceleration blocks."""
        inertia = dict(data.get("inertia", {})) if isinstance(data.get("inertia"), dict) else {}
        accel = (
            dict(data.get("acceleration", {}))
            if isinstance(data.get("acceleration"), dict)
            else {}
        )
        merged = {
            **inertia,
            **accel,
            **{k: v for k, v in data.items() if k not in {"inertia", "acceleration"}},
        }
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: merged[k] for k in known if k in merged}
        return cls(**filtered)


@dataclass(frozen=True, slots=True)
class AdaptiveParams:
    """Coefficients produced by the adaptive controller for one iteration."""

    w: float
    c1: float
    c2: float
    phase: AdaptivePhase
    reasons: tuple[str, ...] = ()
    exploration_pressure: float = 0.0
    improvement_rate: float = 0.0
    normalized_diversity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize adaptive params."""
        return {
            "w": self.w,
            "c1": self.c1,
            "c2": self.c2,
            "phase": self.phase.value,
            "reasons": list(self.reasons),
            "exploration_pressure": self.exploration_pressure,
            "improvement_rate": self.improvement_rate,
            "normalized_diversity": self.normalized_diversity,
        }


@dataclass(slots=True)
class SwarmBehaviorStats:
    """Measurable swarm behaviour inputs for the adaptive controller."""

    iteration: int
    max_iterations: int
    normalized_diversity: float
    mean_fitness: float
    fitness_variance: float
    gbest_fitness: float
    gbest_improvement: float
    mean_pbest_improvement: float
    mean_velocity: float
    improvement_rate: float
    no_improve_count: int
    convergence_rate: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize stats."""
        return {
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "normalized_diversity": self.normalized_diversity,
            "mean_fitness": self.mean_fitness,
            "fitness_variance": self.fitness_variance,
            "gbest_fitness": self.gbest_fitness,
            "gbest_improvement": self.gbest_improvement,
            "mean_pbest_improvement": self.mean_pbest_improvement,
            "mean_velocity": self.mean_velocity,
            "improvement_rate": self.improvement_rate,
            "no_improve_count": self.no_improve_count,
            "convergence_rate": self.convergence_rate,
        }


class AdaptiveStateMachine:
    """Determine optimization phase from measurable conditions.

    Phases
    ------
    EXPLORATION
        High diversity or early search — emphasize roaming.
    BALANCED
        Default mixed exploration/exploitation.
    EXPLOITATION
        Healthy diversity + good recent improvement — refine around gbest.
    STAGNATION_RECOVERY
        No improvement / diversity collapse — force exploration reopen.
    """

    def __init__(self, config: AdaptiveConfig) -> None:
        self._config = config
        self._phase = AdaptivePhase.EXPLORATION
        self.transitions: list[dict[str, Any]] = []

    @property
    def phase(self) -> AdaptivePhase:
        """Current phase."""
        return self._phase

    def update(self, stats: SwarmBehaviorStats) -> AdaptivePhase:
        """Transition phase deterministically; log reason on change."""
        prev = self._phase
        cfg = self._config
        if (
            stats.no_improve_count >= cfg.stagnation_iters
            or stats.normalized_diversity < cfg.delta_collapse
        ):
            nxt = AdaptivePhase.STAGNATION_RECOVERY
            reason = (
                "diversity_collapse"
                if stats.normalized_diversity < cfg.delta_collapse
                else "fitness_stagnation"
            )
        elif (
            stats.improvement_rate >= cfg.eta_good
            and stats.normalized_diversity >= cfg.converge_diversity
            and stats.iteration > cfg.improvement_window
        ):
            nxt = AdaptivePhase.EXPLOITATION
            reason = "stable_improvement"
        elif stats.normalized_diversity >= cfg.delta_high:
            nxt = AdaptivePhase.EXPLORATION
            reason = "high_diversity"
        elif (
            abs(stats.improvement_rate) < cfg.converge_eta
            and stats.normalized_diversity < cfg.converge_diversity
            and stats.iteration > cfg.improvement_window
        ):
            nxt = AdaptivePhase.EXPLOITATION
            reason = "convergence_detected"
        else:
            nxt = AdaptivePhase.BALANCED
            reason = "default_balanced"

        if stats.iteration <= max(1, int(0.1 * max(stats.max_iterations, 1))):
            if nxt != AdaptivePhase.STAGNATION_RECOVERY:
                nxt = AdaptivePhase.EXPLORATION
                reason = "early_iterations"

        if nxt != prev:
            self.transitions.append(
                {
                    "iteration": stats.iteration,
                    "from": prev.value,
                    "to": nxt.value,
                    "reason": reason,
                }
            )
            logger.info(
                "SAPSO phase transition t=%d %s -> %s (%s)",
                stats.iteration,
                prev.value,
                nxt.value,
                reason,
            )
        self._phase = nxt
        return self._phase


class ParameterScheduler:
    """Evolve w, c1, c2 independently from exploration pressure and phase.

    Documented rules (idea.md §15.4–15.5)
    --------------------------------------
    R1 Adaptive inertia
        Purpose: raise momentum when diversity collapses or improvement slows.
        Math: w = w_min + (w_max-w_min)*phi, phi from diversity, eta, progress.
        Effect: low diversity / slow eta → higher w (exploration).
        Advantage: explainable, configurable alpha/beta/gamma.
        Limitation: heuristic weights may need per-domain tuning.

    R2 Diversity-aware c1/c2
        Purpose: balance cognitive vs social learning.
        Math: c1 = c_min + (c_max-c_min)*delta_hat; c2 = C_sum - c1 (clamped).
        Effect: high diversity → higher c1 (personal niches).
        Advantage: preserves C_sum soft invariant when possible.
        Limitation: C_sum clamping can dominate soft diversity schedule.

    R3 Diversity collapse override
        Purpose: prevent premature convergence.
        Math: if delta_hat < delta_collapse → raise w, raise c1, lower c2.
        Effect: reopen exploration around personal bests.
        Advantage: direct response to measurable collapse.
        Limitation: threshold delta_collapse is landscape-sensitive.

    R4 Refinement / exploitation
        Purpose: local polish when converging with adequate diversity.
        Math: set w := w_refine; lower c1; raise c2.
        Effect: stronger social pull toward gbest.
        Advantage: budget spent on polishing good basins.
        Limitation: may trap if false convergence signal.
    """

    def __init__(self, config: AdaptiveConfig) -> None:
        self._config = config

    def schedule(
        self,
        stats: SwarmBehaviorStats,
        phase: AdaptivePhase,
    ) -> AdaptiveParams:
        """Compute bounded (w, c1, c2) for the current stats and phase."""
        cfg = self._config
        reasons: list[str] = []
        delta = float(np.clip(stats.normalized_diversity, 0.0, 1.0))
        eta = float(stats.improvement_rate)
        t = max(stats.iteration, 0)
        tmax = max(stats.max_iterations, 1)

        # psi(eta) — idea.md §15.4
        if eta < cfg.eta_slow:
            psi = 1.0
            reasons.append("R1:slow_improvement→raise_w")
        elif eta < cfg.eta_good:
            psi = 0.5
            reasons.append("R1:moderate_improvement")
        else:
            psi = 0.0
            reasons.append("R1:good_improvement→lower_w_bias")

        phi = float(
            np.clip(
                cfg.alpha * (1.0 - delta)
                + cfg.beta * psi
                + cfg.gamma * (1.0 - t / tmax),
                0.0,
                1.0,
            )
        )
        w = cfg.w_min + (cfg.w_max - cfg.w_min) * phi
        reasons.append(f"R1:phi={phi:.3f}")

        # R2 diversity-aware acceleration
        c1 = cfg.c_min + (cfg.c_max - cfg.c_min) * delta
        c2 = cfg.c_sum - c1
        reasons.append("R2:diversity_aware_c1_c2")

        # R3 collapse override
        if delta < cfg.delta_collapse or phase == AdaptivePhase.STAGNATION_RECOVERY:
            w = max(w, 0.5 * (cfg.w_min + cfg.w_max))
            c1 = min(cfg.c_max, c1 + 0.4)
            c2 = max(cfg.c_min, cfg.c_sum - c1)
            reasons.append("R3:diversity_collapse_override")

        # R4 refinement
        if phase == AdaptivePhase.EXPLOITATION and delta >= cfg.delta_collapse:
            w = cfg.w_refine
            c1 = max(cfg.c_min, c1 - 0.3)
            c2 = min(cfg.c_max, cfg.c_sum - c1)
            reasons.append("R4:refinement_mode")

        if phase == AdaptivePhase.EXPLORATION:
            w = max(w, cfg.w_min + 0.5 * (cfg.w_max - cfg.w_min))
            reasons.append("phase:exploration_floor_w")

        w, c1, c2 = self._clamp(w, c1, c2)
        return AdaptiveParams(
            w=w,
            c1=c1,
            c2=c2,
            phase=phase,
            reasons=tuple(reasons),
            exploration_pressure=phi,
            improvement_rate=eta,
            normalized_diversity=delta,
        )

    def _clamp(self, w: float, c1: float, c2: float) -> tuple[float, float, float]:
        cfg = self._config
        w = float(np.clip(w, cfg.w_min, cfg.w_max))
        c1 = float(np.clip(c1, cfg.c_min, cfg.c_max))
        c2 = float(np.clip(c2, cfg.c_min, cfg.c_max))
        # Soft restore c_sum if both within bounds by adjusting c2 toward remainder
        remainder = cfg.c_sum - c1
        if cfg.c_min <= remainder <= cfg.c_max:
            c2 = float(remainder)
        return w, c1, c2


class AdaptiveController:
    """Compute adaptive ``(w,c1,c2)`` from swarm state — no optimization side effects.

    Implements ``IAdaptiveController``.
    """

    def __init__(self, config: AdaptiveConfig | None = None) -> None:
        self._config = config or AdaptiveConfig()
        self._scheduler = ParameterScheduler(self._config)
        self._state_machine = AdaptiveStateMachine(self._config)
        self._gbest_history: list[float] = []
        self._prev_pbest_mean: float | None = None
        self._last_params = AdaptiveParams(
            w=self._config.w0,
            c1=self._config.c1_0,
            c2=self._config.c2_0,
            phase=AdaptivePhase.EXPLORATION,
            reasons=("init",),
        )

    @property
    def config(self) -> AdaptiveConfig:
        """Active adaptive configuration."""
        return self._config

    @property
    def last_params(self) -> AdaptiveParams:
        """Most recently computed parameters."""
        return self._last_params

    @property
    def state_machine(self) -> AdaptiveStateMachine:
        """Phase state machine."""
        return self._state_machine

    def reset(self) -> None:
        """Clear improvement windows / phase (call on initialize)."""
        self._gbest_history.clear()
        self._prev_pbest_mean = None
        self._state_machine = AdaptiveStateMachine(self._config)
        self._last_params = AdaptiveParams(
            w=self._config.w0,
            c1=self._config.c1_0,
            c2=self._config.c2_0,
            phase=AdaptivePhase.EXPLORATION,
            reasons=("reset",),
        )

    def compute_stats(
        self,
        *,
        particles: Sequence[Particle],
        space: SearchSpace,
        iteration: int,
        max_iterations: int,
        gbest_fitness: float,
        no_improve_count: int,
        previous_gbest: float | None,
        maximize: bool = True,
    ) -> SwarmBehaviorStats:
        """Assemble measurable inputs for adaptation."""
        fits = np.asarray([p.fitness for p in particles], dtype=float) if particles else np.zeros(1)
        pbests = (
            np.asarray([p.pbest_fitness for p in particles], dtype=float)
            if particles
            else np.zeros(1)
        )
        mean_pbest = float(pbests.mean())
        if self._prev_pbest_mean is None:
            pbest_imp = 0.0
        else:
            raw = mean_pbest - self._prev_pbest_mean
            pbest_imp = raw if maximize else -raw
        self._prev_pbest_mean = mean_pbest

        gbest_imp = 0.0
        if previous_gbest is not None:
            raw_g = gbest_fitness - previous_gbest
            gbest_imp = raw_g if maximize else -raw_g

        self._gbest_history.append(float(gbest_fitness))
        eta = self._improvement_rate(maximize=maximize)
        progress = iteration / max(max_iterations, 1)
        # Convergence rate proxy: 1 - normalized recent improvement magnitude
        convergence_rate = float(np.clip(1.0 - abs(eta), 0.0, 1.0))

        return SwarmBehaviorStats(
            iteration=iteration,
            max_iterations=max_iterations,
            normalized_diversity=normalized_diversity(particles, space),
            mean_fitness=float(fits.mean()),
            fitness_variance=float(fits.var()),
            gbest_fitness=float(gbest_fitness),
            gbest_improvement=float(gbest_imp),
            mean_pbest_improvement=float(pbest_imp),
            mean_velocity=mean_velocity_magnitude(particles),
            improvement_rate=float(eta),
            no_improve_count=int(no_improve_count),
            convergence_rate=convergence_rate * progress,
        )

    def update(self, stats: SwarmBehaviorStats) -> AdaptiveParams:
        """Map stats → AdaptiveParams (deterministic)."""
        phase = self._state_machine.update(stats)
        params = self._scheduler.schedule(stats, phase)
        self._last_params = params
        logger.info(
            "SAPSO adapt t=%d phase=%s w=%.3f c1=%.3f c2=%.3f delta=%.4f eta=%.4f reasons=%s",
            stats.iteration,
            params.phase.value,
            params.w,
            params.c1,
            params.c2,
            params.normalized_diversity,
            params.improvement_rate,
            list(params.reasons),
        )
        return params

    def _improvement_rate(self, *, maximize: bool) -> float:
        h = max(1, self._config.improvement_window)
        if len(self._gbest_history) <= h:
            return 0.0
        now = self._gbest_history[-1]
        past = self._gbest_history[-(h + 1)]
        denom = abs(past) + 1e-12
        raw = (now - past) / denom
        return float(raw if maximize else -raw)
