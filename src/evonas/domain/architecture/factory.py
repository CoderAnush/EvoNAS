"""Architecture factory — baseline, random, YAML/JSON, future PSO genotypes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from evonas.domain.architecture.constraints import ArchitectureValidator
from evonas.domain.architecture.layers import (
    activation,
    conv2d,
    dense,
    dropout,
    flatten,
    max_pool2d,
)
from evonas.domain.architecture.serializer import ArchitectureSerializer
from evonas.domain.common.enums import TaskType
from evonas.domain.model.architecture_spec import ArchitectureSpec, ConvBlockSpec

logger = logging.getLogger(__name__)


class ArchitectureFactory:
    """Create ArchitectureSpec instances from templates, files, or RNG.

    Random generation is for Phase 3 builder smoke tests and future PSO
    genotype decoding — it is **not** architecture search.
    """

    def __init__(
        self,
        *,
        validator: ArchitectureValidator | None = None,
        serializer: ArchitectureSerializer | None = None,
    ) -> None:
        self._validator = validator or ArchitectureValidator()
        self._serializer = serializer or ArchitectureSerializer()

    def baseline(
        self,
        *,
        input_shape: tuple[int, ...] = (8, 8, 1),
        num_classes: int = 3,
        name: str = "baseline_cnn",
    ) -> ArchitectureSpec:
        """Return the fixed Phase 2-equivalent baseline architecture."""
        spec = ArchitectureSpec(
            name=name,
            version="1.0.0",
            task_type=TaskType.IMAGE_CLASSIFICATION,
            input_shape=input_shape,
            num_classes=num_classes,
            conv_blocks=(
                ConvBlockSpec(out_channels=16, kernel=3, activation="relu", pool=2),
                ConvBlockSpec(out_channels=32, kernel=3, activation="relu", pool=2),
            ),
            dense_units=(64,),
            dropout=0.1,
            schema_version="2.0",
            metadata={"family": "baseline_cnn", "source": "factory.baseline"},
        )
        return self._validator.require_valid(spec)

    def from_dict(self, data: dict[str, Any]) -> ArchitectureSpec:
        """Build from a dictionary."""
        return self._validator.require_valid(self._serializer.from_dict(data))

    def from_yaml(self, text_or_path: str | Path) -> ArchitectureSpec:
        """Build from YAML text or file path."""
        path = Path(str(text_or_path))
        if path.exists() and path.suffix.lower() in {".yaml", ".yml"}:
            return self._validator.require_valid(self._serializer.load(path))
        return self._validator.require_valid(self._serializer.from_yaml(str(text_or_path)))

    def from_json(self, text_or_path: str | Path) -> ArchitectureSpec:
        """Build from JSON text or file path."""
        path = Path(str(text_or_path))
        if path.exists() and path.suffix.lower() == ".json":
            return self._validator.require_valid(self._serializer.load(path))
        return self._validator.require_valid(self._serializer.from_json(str(text_or_path)))

    def random(
        self,
        *,
        input_shape: tuple[int, ...] = (8, 8, 1),
        num_classes: int = 3,
        seed: int = 0,
        name: str | None = None,
        n_conv: int | None = None,
        n_dense: int | None = None,
    ) -> ArchitectureSpec:
        """Sample a small random valid CNN+MLP architecture (not PSO)."""
        rng = np.random.default_rng(seed)
        n_conv = int(n_conv if n_conv is not None else rng.integers(1, 3))
        n_dense = int(n_dense if n_dense is not None else rng.integers(0, 3))
        layers = []
        channels_choices = [8, 16, 32]
        for _ in range(n_conv):
            ch = int(rng.choice(channels_choices))
            layers.append(conv2d(ch, kernel=3))
            layers.append(activation(str(rng.choice(["relu", "gelu"]))))
            layers.append(max_pool2d(2))
        layers.append(flatten())
        for _ in range(n_dense):
            units = int(rng.choice([32, 64, 128]))
            layers.append(dense(units))
            layers.append(activation("relu"))
            rate = float(rng.choice([0.0, 0.1, 0.25]))
            if rate > 0:
                layers.append(dropout(rate))
        layers.append(dense(num_classes))
        spec = ArchitectureSpec(
            name=name or f"random_{seed}",
            version="1.0.0",
            task_type=TaskType.IMAGE_CLASSIFICATION,
            input_shape=input_shape,
            num_classes=num_classes,
            layers=tuple(layers),
            schema_version="3.0",
            metadata={"source": "factory.random", "seed": seed},
        )
        return self._validator.require_valid(spec)

    def from_genotype(
        self,
        genotype: list[float] | tuple[float, ...],
        *,
        space: Any,
        name: str = "from_genotype",
    ) -> ArchitectureSpec:
        """Decode a continuous genotype via a SearchSpace (Phase 3/4 hook)."""
        from evonas.domain.architecture.generator import ArchitectureGenerator

        return ArchitectureGenerator(space=space, validator=self._validator).decode(
            genotype, name=name
        )
