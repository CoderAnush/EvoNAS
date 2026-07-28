"""Architecture domain package — Phase 3 dynamic model generation."""

from evonas.domain.architecture.complexity import ComplexityReport, estimate_complexity
from evonas.domain.architecture.constraints import (
    ArchitectureLimits,
    ArchitectureValidator,
    ConstraintHandler,
    ValidationResult,
)
from evonas.domain.architecture.factory import ArchitectureFactory
from evonas.domain.architecture.generator import ArchitectureGenerator
from evonas.domain.architecture.layers import LayerSpec
from evonas.domain.architecture.serializer import ArchitectureSerializer
from evonas.domain.architecture.visualization import ArchitectureVisualizer

__all__ = [
    "ArchitectureFactory",
    "ArchitectureGenerator",
    "ArchitectureLimits",
    "ArchitectureSerializer",
    "ArchitectureValidator",
    "ArchitectureVisualizer",
    "ComplexityReport",
    "ConstraintHandler",
    "LayerSpec",
    "ValidationResult",
    "estimate_complexity",
]
