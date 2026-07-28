"""Search-space adapter: PSO vectors ↔ ArchitectureSpec (Phase 3 compatible)."""

from __future__ import annotations

import logging
from typing import Sequence

from evonas.domain.architecture.constraints import ArchitectureValidator, ConstraintHandler
from evonas.domain.architecture.generator import ArchitectureGenerator
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.optimization.particle import Particle
from evonas.domain.search_space.space import SearchSpace

logger = logging.getLogger(__name__)


class SearchSpaceAdapter:
    """Bridge continuous PSO positions with ArchitectureSpec encode/decode/repair."""

    def __init__(
        self,
        space: SearchSpace,
        *,
        generator: ArchitectureGenerator | None = None,
        validator: ArchitectureValidator | None = None,
        constraints: ConstraintHandler | None = None,
    ) -> None:
        self._space = space
        self._validator = validator or ArchitectureValidator()
        self._constraints = constraints or ConstraintHandler(self._validator)
        self._generator = generator or ArchitectureGenerator(
            space, validator=self._validator, constraints=self._constraints
        )

    @property
    def space(self) -> SearchSpace:
        """Active search space."""
        return self._space

    @property
    def generator(self) -> ArchitectureGenerator:
        """Underlying architecture generator."""
        return self._generator

    def decode(self, position: Sequence[float], *, name: str = "particle") -> ArchitectureSpec:
        """Decode a PSO position into a validated ArchitectureSpec."""
        return self._generator.decode(position, name=name, repair=True)

    def encode(self, spec: ArchitectureSpec) -> list[float]:
        """Encode ArchitectureSpec into a continuous genotype."""
        return self._generator.encode(spec)

    def validate(self, spec: ArchitectureSpec) -> bool:
        """Return True when architecture is valid."""
        return self._validator.validate(spec).ok

    def repair(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Repair an invalid architecture."""
        return self._constraints.repair(spec)

    def repair_particle(self, particle: Particle) -> None:
        """Project via decode/encode round-trip so the particle stays feasible.

        Never raises — on failure leaves the projected box position unchanged.
        """
        try:
            spec = self.decode(particle.position.as_list(), name=particle.id)
            repaired = self.repair(spec) if not self.validate(spec) else spec
            particle.position.values = self.encode(repaired)
            particle.metadata["arch_id"] = repaired.arch_id()
            particle.metadata["architecture_name"] = repaired.name
        except Exception as exc:  # noqa: BLE001
            logger.warning("particle repair skipped for %s: %s", particle.id, exc)
