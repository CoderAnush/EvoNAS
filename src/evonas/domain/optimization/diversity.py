"""Swarm diversity metrics for SAPSO (idea.md §15.2)."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from evonas.domain.optimization.particle import Particle
from evonas.domain.search_space.space import SearchSpace


def raw_diversity(particles: Sequence[Particle]) -> float:
    """Mean Euclidean deviation from the swarm centroid."""
    if not particles:
        return 0.0
    xs = np.asarray([p.position.as_list() for p in particles], dtype=float)
    centroid = xs.mean(axis=0)
    return float(np.linalg.norm(xs - centroid, axis=1).mean())


def space_diagonal(space: SearchSpace) -> float:
    """Euclidean length of the search-space bounding box diagonal."""
    lows, highs = space.bounds()
    spans = np.asarray(highs, dtype=float) - np.asarray(lows, dtype=float)
    return float(np.linalg.norm(spans) + 1e-12)


def normalized_diversity(
    particles: Sequence[Particle],
    space: SearchSpace,
    *,
    eps: float = 1e-12,
) -> float:
    """Normalized diversity \\(\\hat{\\delta}\\) in roughly [0, 1]."""
    delta = raw_diversity(particles)
    diag = space_diagonal(space)
    return float(delta / (diag + eps))


def mean_velocity_magnitude(particles: Sequence[Particle]) -> float:
    """Mean L2 norm of particle velocities."""
    if not particles:
        return 0.0
    vs = np.asarray([p.velocity.as_list() for p in particles], dtype=float)
    return float(np.linalg.norm(vs, axis=1).mean())
