"""Layer configuration IR — expandable for Dense, Conv, Attention, etc."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Known layer types (Phase 3). Future: attention, transformer blocks.
LAYER_TYPES = frozenset(
    {
        "dense",
        "dropout",
        "batch_norm",
        "layer_norm",
        "activation",
        "conv2d",
        "max_pool2d",
        "avg_pool2d",
        "flatten",
        "identity",
    }
)

ACTIVATIONS = frozenset({"relu", "gelu", "tanh", "sigmoid", "identity", "softmax"})


@dataclass(frozen=True, slots=True)
class LayerSpec:
    """Independent layer configuration used by the dynamic builder.

    Parameters are stored in ``params`` so new layer families can be added
    without changing the dataclass schema.
    """

    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", str(self.type).lower())
        object.__setattr__(self, "params", dict(self.params))

    def to_dict(self) -> dict[str, Any]:
        """Serialize layer to a plain mapping."""
        return {"type": self.type, "params": dict(self.params)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LayerSpec:
        """Deserialize a layer mapping."""
        if "type" not in data:
            raise ValueError("layer requires 'type'")
        params = data.get("params")
        if params is None:
            # Allow flat YAML style: {type: dense, units: 128}
            params = {k: v for k, v in data.items() if k != "type"}
        return cls(type=str(data["type"]), params=dict(params or {}))

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch a parameter with default."""
        return self.params.get(key, default)


def dense(units: int, *, bias: bool = True) -> LayerSpec:
    """Helper: Dense / Linear layer."""
    return LayerSpec("dense", {"units": int(units), "bias": bool(bias)})


def dropout(rate: float) -> LayerSpec:
    """Helper: Dropout layer."""
    return LayerSpec("dropout", {"rate": float(rate)})


def batch_norm(num_features: int | None = None) -> LayerSpec:
    """Helper: BatchNorm (features inferred at build if None for 1d after flatten)."""
    params: dict[str, Any] = {}
    if num_features is not None:
        params["num_features"] = int(num_features)
    return LayerSpec("batch_norm", params)


def activation(name: str) -> LayerSpec:
    """Helper: Activation layer."""
    return LayerSpec("activation", {"name": str(name).lower()})


def conv2d(
    out_channels: int,
    *,
    kernel: int = 3,
    stride: int = 1,
    padding: int | None = None,
    bias: bool = True,
) -> LayerSpec:
    """Helper: Conv2D layer."""
    return LayerSpec(
        "conv2d",
        {
            "out_channels": int(out_channels),
            "kernel": int(kernel),
            "stride": int(stride),
            "padding": int(kernel // 2 if padding is None else padding),
            "bias": bool(bias),
        },
    )


def max_pool2d(kernel: int = 2, stride: int | None = None) -> LayerSpec:
    """Helper: MaxPool2D."""
    return LayerSpec(
        "max_pool2d",
        {"kernel": int(kernel), "stride": int(stride if stride is not None else kernel)},
    )


def flatten() -> LayerSpec:
    """Helper: Flatten."""
    return LayerSpec("flatten", {})


def layers_from_legacy_blocks(
    *,
    conv_blocks: tuple[Any, ...],
    dense_units: tuple[int, ...],
    dropout_rate: float,
    num_classes: int,
) -> tuple[LayerSpec, ...]:
    """Convert Phase 2 conv_blocks/dense_units into an explicit layer list."""
    out: list[LayerSpec] = []
    for block in conv_blocks:
        out.append(
            conv2d(
                int(block.out_channels),
                kernel=int(block.kernel),
                stride=int(block.stride),
            )
        )
        out.append(activation(str(getattr(block, "activation", "relu"))))
        pool = getattr(block, "pool", None)
        if pool:
            out.append(max_pool2d(int(pool)))
    out.append(flatten())
    for units in dense_units:
        out.append(dense(int(units)))
        out.append(activation("relu"))
        if dropout_rate > 0:
            out.append(dropout(dropout_rate))
    if dropout_rate > 0 and not dense_units:
        out.append(dropout(dropout_rate))
    out.append(dense(int(num_classes)))
    return tuple(out)
