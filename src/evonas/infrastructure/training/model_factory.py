"""Model factory — instantiate models from configuration (Phase 2+)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.domain.common.errors import ConfigError
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.training.pytorch_builder import PyTorchModelBuilder
from evonas.ports.training import IModelBuilder, ITrainableModel

logger = logging.getLogger(__name__)


class ModelFactory:
    """Create models from ArchitectureSpec or YAML config paths.

    Future phases reuse this factory; new families register additional builders.
    """

    def __init__(
        self,
        *,
        builders: dict[str, IModelBuilder] | None = None,
        config_manager: ConfigurationManager | None = None,
        default_backend: str = "pytorch",
    ) -> None:
        self._config_manager = config_manager or ConfigurationManager()
        self._builders: dict[str, IModelBuilder] = builders or {
            "pytorch": PyTorchModelBuilder(),
        }
        self._default_backend = default_backend

    def register_builder(self, backend: str, builder: IModelBuilder) -> None:
        """Register or replace a backend builder."""
        self._builders[backend] = builder
        logger.info("Registered model builder backend=%s", backend)

    def load_spec(self, config: dict[str, Any] | str | Path) -> ArchitectureSpec:
        """Load an ArchitectureSpec from a mapping or YAML path."""
        if isinstance(config, (str, Path)):
            data = self._config_manager.load(config)
        else:
            data = dict(config)
        # Allow nested `model:` block in training configs.
        if "model" in data and isinstance(data["model"], dict) and "name" in data["model"]:
            # Prefer dedicated architecture file when referenced.
            arch_path = data["model"].get("architecture_path")
            if arch_path:
                data = self._config_manager.load(arch_path)
            else:
                data = data["model"]
        try:
            return ArchitectureSpec.from_dict(data)
        except Exception as exc:  # noqa: BLE001
            raise ConfigError(f"invalid architecture config: {exc}", code="EN_CFG_001") from exc

    def create(
        self,
        spec_or_config: ArchitectureSpec | dict[str, Any] | str | Path,
        *,
        backend: str | None = None,
    ) -> tuple[ITrainableModel, ArchitectureSpec]:
        """Create ``(model, spec)`` for the requested backend."""
        if isinstance(spec_or_config, ArchitectureSpec):
            spec = spec_or_config
        else:
            spec = self.load_spec(spec_or_config)
        backend_name = backend or self._default_backend
        if backend_name not in self._builders:
            raise ConfigError(
                f"unknown model backend '{backend_name}'. known={sorted(self._builders)}",
                code="EN_CFG_002",
            )
        model = self._builders[backend_name].build(spec)
        return model, spec

    def builder(self, backend: str | None = None) -> IModelBuilder:
        """Return a registered builder."""
        name = backend or self._default_backend
        if name not in self._builders:
            raise ConfigError(f"unknown model backend '{name}'", code="EN_CFG_002")
        return self._builders[name]
