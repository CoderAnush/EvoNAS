"""Framework-agnostic architecture specification (Phase 2 + Phase 3 layer IR)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from evonas.domain.architecture.layers import LayerSpec, layers_from_legacy_blocks
from evonas.domain.common.enums import TaskType


@dataclass(frozen=True, slots=True)
class ConvBlockSpec:
    """Single convolution block in the legacy Architecture IR (Phase 2)."""

    out_channels: int
    kernel: int = 3
    stride: int = 1
    activation: str = "relu"
    pool: int | None = 2


@dataclass(frozen=True, slots=True)
class ArchitectureSpec:
    """Framework-agnostic neural architecture description.

    Phase 2 used ``conv_blocks`` + ``dense_units``. Phase 3 prefers an explicit
    ``layers`` list. When ``layers`` is empty, ``resolved_layers()`` synthesizes
    an equivalent layer sequence for the dynamic builder (backward compatible).
    """

    name: str
    version: str
    task_type: TaskType
    input_shape: tuple[int, ...]
    num_classes: int
    conv_blocks: tuple[ConvBlockSpec, ...] = ()
    dense_units: tuple[int, ...] = ()
    dropout: float = 0.0
    layers: tuple[LayerSpec, ...] = ()
    schema_version: str = "3.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolved_layers(self) -> tuple[LayerSpec, ...]:
        """Return explicit layers, or synthesize from legacy Phase 2 fields."""
        if self.layers:
            return self.layers
        return layers_from_legacy_blocks(
            conv_blocks=self.conv_blocks,
            dense_units=self.dense_units,
            dropout_rate=self.dropout,
            num_classes=self.num_classes,
        )

    @property
    def depth(self) -> int:
        """Number of resolved layers (including activations / dropout)."""
        return len(self.resolved_layers())

    def to_dict(self) -> dict[str, Any]:
        """Serialize for manifests, YAML/JSON, and experiment records."""
        payload = asdict(self)
        payload["task_type"] = self.task_type.value
        payload["input_shape"] = list(self.input_shape)
        payload["conv_blocks"] = [asdict(b) for b in self.conv_blocks]
        payload["dense_units"] = list(self.dense_units)
        payload["layers"] = [layer.to_dict() for layer in self.layers]
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchitectureSpec:
        """Deserialize from YAML/JSON mapping (Phase 2 and Phase 3 formats)."""
        blocks = tuple(
            ConvBlockSpec(**b) if isinstance(b, dict) else b for b in data.get("conv_blocks", [])
        )
        raw_layers = data.get("layers", []) or []
        layers = tuple(
            LayerSpec.from_dict(layer) if isinstance(layer, dict) else layer for layer in raw_layers
        )
        return cls(
            name=str(data["name"]),
            version=str(data.get("version", "1.0.0")),
            task_type=TaskType(str(data.get("task_type", TaskType.IMAGE_CLASSIFICATION.value))),
            input_shape=tuple(int(x) for x in data["input_shape"]),
            num_classes=int(data["num_classes"]),
            conv_blocks=blocks,
            dense_units=tuple(int(x) for x in data.get("dense_units", [])),
            dropout=float(data.get("dropout", 0.0)),
            layers=layers,
            schema_version=str(data.get("schema_version", "3.0" if layers else "2.0")),
            metadata=dict(data.get("metadata", {})),
        )

    def arch_id(self) -> str:
        """Stable hash of the discrete architecture (resolved layers)."""
        core = {
            "name": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "task_type": self.task_type.value,
            "input_shape": list(self.input_shape),
            "num_classes": self.num_classes,
            "layers": [layer.to_dict() for layer in self.resolved_layers()],
        }
        blob = json.dumps(core, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArchitectureSpec):
            return NotImplemented
        return self.arch_id() == other.arch_id()

    def __hash__(self) -> int:
        return hash(self.arch_id())
