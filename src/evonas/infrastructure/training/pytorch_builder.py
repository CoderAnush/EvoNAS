"""PyTorch ModelBuilder — constructs models from ArchitectureSpec (Phase 3 dynamic)."""

from __future__ import annotations

import logging

from evonas.domain.architecture.constraints import ArchitectureValidator
from evonas.domain.common.errors import ArchitectureError
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.infrastructure.training.dynamic_network import DynamicNetwork
from evonas.ports.training import ITrainableModel

logger = logging.getLogger(__name__)


class PyTorchModelBuilder:
    """Build PyTorch modules from ArchitectureSpec via the dynamic layer IR.

    Phase 2 legacy ``conv_blocks`` / ``dense_units`` specs remain supported
    through ``ArchitectureSpec.resolved_layers()``. Trainers depend only on
    ``ITrainableModel`` — no BaselineCNN dependency in this path.
    """

    backend_name = "pytorch"

    def __init__(self, *, validator: ArchitectureValidator | None = None) -> None:
        self._validator = validator or ArchitectureValidator()

    def build(self, spec: ArchitectureSpec) -> ITrainableModel:
        """Instantiate a trainable model for ``spec``."""
        result = self._validator.validate(spec)
        if not result.ok:
            raise ArchitectureError(result.error_message)
        try:
            model = DynamicNetwork(spec)
        except Exception as exc:  # noqa: BLE001
            raise ArchitectureError(f"failed to build model for {spec.name}: {exc}") from exc
        n = self.count_parameters(model)
        logger.info(
            "Built model=%s params=%d arch_id=%s layers=%d",
            spec.name,
            n,
            spec.arch_id()[:12],
            spec.depth,
        )
        return model

    def count_parameters(self, model: ITrainableModel) -> int:
        """Count trainable parameters."""
        return int(sum(p.numel() for p in model.parameters() if getattr(p, "requires_grad", True)))
