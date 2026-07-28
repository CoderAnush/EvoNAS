"""Architecture generator — genotype decode/encode (Phase 3, no PSO)."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import numpy as np

from evonas.domain.architecture.complexity import ComplexityReport, estimate_complexity
from evonas.domain.architecture.constraints import (
    ArchitectureValidator,
    ConstraintHandler,
    ValidationResult,
)
from evonas.domain.architecture.layers import activation, conv2d, dense, dropout, flatten, max_pool2d
from evonas.domain.common.enums import TaskType
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.search_space.space import SearchSpace

logger = logging.getLogger(__name__)


class ArchitectureGenerator:
    """Decode continuous genotypes into ArchitectureSpec and encode back.

    Enables future PSO particles to become trainable models without performing
    any optimization in this class.
    """

    def __init__(
        self,
        space: SearchSpace | None = None,
        *,
        validator: ArchitectureValidator | None = None,
        constraints: ConstraintHandler | None = None,
    ) -> None:
        self._space = space or SearchSpace.cnn_quick()
        self._validator = validator or ArchitectureValidator()
        self._constraints = constraints or ConstraintHandler(self._validator)

    @property
    def space(self) -> SearchSpace:
        """Active search space."""
        return self._space

    def random_genotype(self, rng: Any | None = None) -> list[float]:
        """Sample a uniform continuous genotype within gene bounds."""
        generator = rng if rng is not None else np.random.default_rng()
        lows, highs = self._space.bounds()
        return [float(generator.uniform(lo, hi)) for lo, hi in zip(lows, highs, strict=True)]

    def decode(
        self,
        genotype: Sequence[float],
        *,
        name: str = "decoded",
        repair: bool = True,
    ) -> ArchitectureSpec:
        """Decode genotype → ArchitectureSpec (optionally repair)."""
        if len(genotype) != self._space.dimension:
            raise ValueError(
                f"genotype dim {len(genotype)} != space dim {self._space.dimension}"
            )
        decoded = {
            gene.name: gene.decode(float(genotype[i]))
            for i, gene in enumerate(self._space.genes)
        }
        n_blocks = int(decoded.get("n_blocks", 1))
        act = str(decoded.get("act", "relu"))
        drop = float(decoded.get("dropout", 0.0))
        dense_units = int(decoded.get("dense_units", 32))
        channels = [
            int(decoded[key])
            for key in sorted(k for k in decoded if str(k).startswith("ch"))
        ] or [16]
        layers = []
        for i in range(n_blocks):
            ch = channels[min(i, len(channels) - 1)]
            layers.append(conv2d(ch, kernel=3))
            layers.append(activation(act))
            layers.append(max_pool2d(2))
        layers.append(flatten())
        layers.append(dense(dense_units))
        layers.append(activation("relu"))
        if drop > 0:
            layers.append(dropout(drop))
        layers.append(dense(self._space.num_classes))

        spec = ArchitectureSpec(
            name=name,
            version="1.0.0",
            task_type=TaskType.IMAGE_CLASSIFICATION,
            input_shape=self._space.input_shape,
            num_classes=self._space.num_classes,
            layers=tuple(layers),
            dropout=drop,
            schema_version="3.0",
            metadata={"source": "architecture_generator.decode", "genes": decoded},
        )
        if repair:
            return self._constraints.repair(spec)
        return self._validator.require_valid(spec)

    def encode(self, spec: ArchitectureSpec) -> list[float]:
        """Best-effort encode of an ArchitectureSpec into the active space."""
        max_blocks = 2
        for gene in self._space.genes:
            if gene.name == "n_blocks" and gene.kind == "int":
                max_blocks = int(gene.high)
        n_blocks = sum(1 for layer in spec.resolved_layers() if layer.type == "conv2d")
        n_blocks = min(max(n_blocks, 1), max_blocks)
        conv_channels = [
            int(layer.get("out_channels", 16))
            for layer in spec.resolved_layers()
            if layer.type == "conv2d"
        ]
        acts = [
            str(layer.get("name", "relu"))
            for layer in spec.resolved_layers()
            if layer.type == "activation"
        ]
        act = acts[0] if acts else "relu"
        drops = [
            float(layer.get("rate", 0.0))
            for layer in spec.resolved_layers()
            if layer.type == "dropout"
        ]
        drop = drops[0] if drops else 0.0
        dens = [
            int(layer.get("units", 32))
            for layer in spec.resolved_layers()
            if layer.type == "dense"
        ]
        dense_units = dens[-2] if len(dens) >= 2 else (dens[0] if dens else 32)

        values: dict[str, Any] = {
            "n_blocks": n_blocks,
            "act": act,
            "dropout": drop,
            "dense_units": dense_units,
        }
        ch_genes = [g.name for g in self._space.genes if g.name.startswith("ch")]
        for i, name in enumerate(ch_genes):
            values[name] = conv_channels[i] if i < len(conv_channels) else 16
        return [gene.encode(values.get(gene.name, gene.low)) for gene in self._space.genes]

    def validate(self, spec: ArchitectureSpec) -> ValidationResult:
        """Validate architecture structure."""
        return self._validator.validate(spec)

    def repair(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Deterministically repair invalid architectures where possible."""
        return self._constraints.repair(spec)

    def estimate_complexity(self, spec: ArchitectureSpec) -> ComplexityReport:
        """Estimate parameter / depth complexity."""
        return estimate_complexity(spec)

    def arch_id(self, spec: ArchitectureSpec) -> str:
        """Stable architecture hash."""
        return spec.arch_id()
