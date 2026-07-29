"""IAdaptiveController port (idea.md Phase 5)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from evonas.domain.optimization.adaptive import AdaptiveParams, SwarmBehaviorStats


@runtime_checkable
class IAdaptiveController(Protocol):
    """Compute adaptive PSO coefficients from measurable swarm behaviour."""

    def update(self, stats: SwarmBehaviorStats) -> AdaptiveParams:
        """Return next ``(w, c1, c2)`` package for the given stats."""

    @property
    def last_params(self) -> AdaptiveParams:
        """Most recent adaptive parameters."""
