"""Shared domain errors (idea.md exception hierarchy)."""

from __future__ import annotations


class EvoNASError(Exception):
    """Base error for all EvoNAS domain/infrastructure failures."""

    code: str = "EN_GENERIC"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.code = code or self.code
        super().__init__(f"[{self.code}] {message}")


class ConfigError(EvoNASError):
    """Configuration validation or resolution failure."""

    code = "EN_CFG_001"


class DataError(EvoNASError):
    """Dataset load, checksum, schema, or window failure."""

    code = "EN_DATA_001"


class ArchitectureError(EvoNASError):
    """Architecture decode/validate/repair failure."""

    code = "EN_ARCH_001"


class OptimizationError(EvoNASError):
    """SAPSO / search failure."""

    code = "EN_OPT_001"


class TrainingError(EvoNASError):
    """Training backend failure."""

    code = "EN_TRN_001"


class EvaluationError(EvoNASError):
    """Evaluation failure."""

    code = "EN_TRN_002"


class DecisionError(EvoNASError):
    """Decision engine / illegal transition failure."""

    code = "EN_DEC_001"


class DeploymentError(EvoNASError):
    """Deploy / rollback failure."""

    code = "EN_DEP_001"


class CheckpointError(EvoNASError):
    """Checkpoint persistence failure."""

    code = "EN_CKPT_001"
