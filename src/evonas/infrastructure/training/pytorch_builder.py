"""PyTorch ModelBuilder for ArchitectureSpec (Phase 2)."""

from __future__ import annotations

import logging

from evonas.domain.common.errors import ArchitectureError
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.infrastructure.training.baseline_cnn import BaselineCNN
from evonas.ports.training import ITrainableModel

logger = logging.getLogger(__name__)


class PyTorchModelBuilder:
    """Build PyTorch modules from ArchitectureSpec.

    Phase 2 supports the fixed baseline CNN family. Future builders can register
    additional families without changing TrainingEngine.
    """

    backend_name = "pytorch"

    def build(self, spec: ArchitectureSpec) -> ITrainableModel:
        """Instantiate a trainable model for ``spec``."""
        try:
            model = BaselineCNN(spec)
        except Exception as exc:  # noqa: BLE001
            raise ArchitectureError(f"failed to build model for {spec.name}: {exc}") from exc
        n = self.count_parameters(model)
        logger.info("Built model=%s params=%d arch_id=%s", spec.name, n, spec.arch_id()[:12])
        return model

    def count_parameters(self, model: ITrainableModel) -> int:
        """Count trainable parameters."""
        return int(sum(p.numel() for p in model.parameters() if getattr(p, "requires_grad", True)))
