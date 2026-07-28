"""Architecture ports — generator and constraint handler (idea.md §21.8 / §232)."""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from evonas.domain.architecture.complexity import ComplexityReport
from evonas.domain.architecture.constraints import ValidationResult
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.search_space.space import SearchSpace


@runtime_checkable
class IArchitectureGenerator(Protocol):
    """Decode genotypes into ArchitectureSpec (Phase 3; PSO uses this in Phase 4+)."""

    @property
    def space(self) -> SearchSpace:
        """Active search space."""

    def random_genotype(self, rng: Any | None = None) -> list[float]:
        """Sample a random continuous genotype within bounds."""

    def decode(self, genotype: Sequence[float], *, name: str = "decoded") -> ArchitectureSpec:
        """Decode genotype → ArchitectureSpec."""

    def encode(self, spec: ArchitectureSpec) -> list[float]:
        """Encode ArchitectureSpec → continuous vector."""

    def validate(self, spec: ArchitectureSpec) -> ValidationResult:
        """Validate architecture structure."""

    def repair(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Deterministically repair invalid architectures where possible."""

    def estimate_complexity(self, spec: ArchitectureSpec) -> ComplexityReport:
        """Estimate parameter / depth complexity."""

    def arch_id(self, spec: ArchitectureSpec) -> str:
        """Stable architecture hash."""


@runtime_checkable
class IConstraintHandler(Protocol):
    """Repair / constrain architectures before training."""

    def repair(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Return a validated (possibly repaired) architecture."""
