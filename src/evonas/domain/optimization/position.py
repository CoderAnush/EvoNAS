"""Position update and box projection (idea.md §14.2)."""

from __future__ import annotations

import numpy as np

from evonas.domain.optimization.particle import Particle, ParticlePosition


def update_position(particle: Particle) -> ParticlePosition:
    """x <- x + v (mutates particle)."""
    x = np.asarray(particle.position.as_list(), dtype=float)
    v = np.asarray(particle.velocity.as_list(), dtype=float)
    particle.position = ParticlePosition((x + v).tolist())
    return particle.position


def project_to_bounds(
    particle: Particle,
    lows: list[float],
    highs: list[float],
) -> ParticlePosition:
    """Project position onto the feasible box [L, U]^D."""
    x = np.asarray(particle.position.as_list(), dtype=float)
    lo = np.asarray(lows, dtype=float)
    hi = np.asarray(highs, dtype=float)
    particle.position = ParticlePosition(np.clip(x, lo, hi).tolist())
    return particle.position
