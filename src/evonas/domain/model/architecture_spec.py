"""Framework-agnostic architecture specification (Phase 2 baseline + future NAS)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from evonas.domain.common.enums import TaskType


@dataclass(frozen=True, slots=True)
class ConvBlockSpec:
    """Single convolution block in the Architecture IR."""

    out_channels: int
    kernel: int = 3
    stride: int = 1
    activation: str = "relu"
    pool: int | None = 2


@dataclass(frozen=True, slots=True)
class ArchitectureSpec:
    """Framework-agnostic neural architecture description.

    Phase 2 uses a fixed baseline instance. Later phases decode genotypes into
    the same IR so builders remain interchangeable.
    """

    name: str
    version: str
    task_type: TaskType
    input_shape: tuple[int, ...]
    num_classes: int
    conv_blocks: tuple[ConvBlockSpec, ...]
    dense_units: tuple[int, ...] = ()
    dropout: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for manifests and experiment records."""
        payload = asdict(self)
        payload["task_type"] = self.task_type.value
        payload["input_shape"] = list(self.input_shape)
        payload["conv_blocks"] = [asdict(b) for b in self.conv_blocks]
        payload["dense_units"] = list(self.dense_units)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchitectureSpec:
        """Deserialize from YAML/JSON mapping."""
        blocks = tuple(
            ConvBlockSpec(**b) if isinstance(b, dict) else b for b in data.get("conv_blocks", [])
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
            metadata=dict(data.get("metadata", {})),
        )

    def arch_id(self) -> str:
        """Stable hash of the discrete architecture (excludes free-form metadata noise)."""
        core = {
            "name": self.name,
            "version": self.version,
            "task_type": self.task_type.value,
            "input_shape": list(self.input_shape),
            "num_classes": self.num_classes,
            "conv_blocks": [asdict(b) for b in self.conv_blocks],
            "dense_units": list(self.dense_units),
            "dropout": self.dropout,
        }
        blob = json.dumps(core, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
