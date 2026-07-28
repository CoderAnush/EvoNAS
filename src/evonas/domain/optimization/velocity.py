"""Standard PSO velocity update and clamping (idea.md §14.1 / §14.3)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from evonas.domain.optimization.particle import Particle, ParticlePosition, ParticleVelocity


@dataclass(frozen=True, slots=True)
class VelocityConfig:
    """Fixed Standard PSO velocity coefficients (no adaptive updates)."""

    w: float = 0.729
    c1: float = 1.49445
    c2: float = 1.49445
    kappa: float = 0.2  # Vmax = kappa * (U - L)


def update_velocity(
    particle: Particle,
    gbest: ParticlePosition,
    lows: list[float],
    highs: list[float],
    config: VelocityConfig,
    rng: np.random.Generator,
) -> ParticleVelocity:
    """Apply classical velocity update + clamp. Returns new velocity (also mutates particle)."""
    x = np.asarray(particle.position.as_list(), dtype=float)
    v = np.asarray(particle.velocity.as_list(), dtype=float)
    pbest = np.asarray(particle.pbest_position.as_list(), dtype=float)
    g = np.asarray(gbest.as_list(), dtype=float)
    r1 = rng.random(size=x.shape)
    r2 = rng.random(size=x.shape)
    v_new = (
        config.w * v
        + config.c1 * r1 * (pbest - x)
        + config.c2 * r2 * (g - x)
    )
    spans = np.maximum(np.asarray(highs, dtype=float) - np.asarray(lows, dtype=float), 1e-12)
    vmax = config.kappa * spans
    v_new = np.clip(v_new, -vmax, vmax)
    particle.velocity = ParticleVelocity(v_new.tolist())
    return particle.velocity
