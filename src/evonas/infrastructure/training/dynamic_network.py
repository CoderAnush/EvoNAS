"""Dynamic PyTorch network built entirely from ArchitectureSpec layer IR."""

from __future__ import annotations

import torch
from torch import nn

from evonas.domain.architecture.layers import LayerSpec
from evonas.domain.model.architecture_spec import ArchitectureSpec


def _activation_module(name: str) -> nn.Module:
    key = str(name).lower()
    if key == "relu":
        return nn.ReLU(inplace=True)
    if key == "gelu":
        return nn.GELU()
    if key == "tanh":
        return nn.Tanh()
    if key == "sigmoid":
        return nn.Sigmoid()
    if key == "softmax":
        return nn.Softmax(dim=-1)
    if key == "identity":
        return nn.Identity()
    raise ValueError(f"unsupported activation '{name}'")


class DynamicNetwork(nn.Module):
    """Construct an ``nn.Module`` solely from ``ArchitectureSpec.resolved_layers()``.

    No hardcoded layer counts or hidden sizes — every op comes from the IR.
    """

    def __init__(self, spec: ArchitectureSpec) -> None:
        super().__init__()
        self._spec_name = spec.name
        self._arch_id = spec.arch_id()
        modules = self._build_modules(spec)
        self.net = nn.Sequential(*modules)

    @staticmethod
    def _build_modules(spec: ArchitectureSpec) -> list[nn.Module]:
        layers = spec.resolved_layers()
        if not layers:
            raise ValueError("architecture has no layers")

        modules: list[nn.Module] = []
        # Track tensor layout: "nchw" | "features"
        layout = "nchw" if len(spec.input_shape) == 3 else "features"
        if len(spec.input_shape) == 3:
            h, w, c = (int(x) for x in spec.input_shape)
            in_features = c * h * w
        else:
            h = w = 1
            c = 1
            in_features = int(spec.input_shape[0]) if spec.input_shape else 1

        for layer in layers:
            modules.extend(
                DynamicNetwork._materialize(
                    layer,
                    layout=layout,
                    channels=c,
                    height=h,
                    width=w,
                    in_features=in_features,
                )
            )
            # Update tracked dims after materialize
            layout, c, h, w, in_features = DynamicNetwork._update_shape(
                layer, layout=layout, channels=c, height=h, width=w, in_features=in_features
            )
        return modules

    @staticmethod
    def _materialize(
        layer: LayerSpec,
        *,
        layout: str,
        channels: int,
        height: int,
        width: int,
        in_features: int,
    ) -> list[nn.Module]:
        t = layer.type
        if t == "conv2d":
            out_c = int(layer.get("out_channels"))
            k = int(layer.get("kernel", 3))
            stride = int(layer.get("stride", 1))
            pad = int(layer.get("padding", k // 2))
            bias = bool(layer.get("bias", True))
            return [
                nn.Conv2d(channels, out_c, kernel_size=k, stride=stride, padding=pad, bias=bias)
            ]
        if t == "max_pool2d":
            k = int(layer.get("kernel", 2))
            s = int(layer.get("stride", k))
            return [nn.MaxPool2d(kernel_size=k, stride=s)]
        if t == "avg_pool2d":
            k = int(layer.get("kernel", 2))
            s = int(layer.get("stride", k))
            return [nn.AvgPool2d(kernel_size=k, stride=s)]
        if t == "flatten":
            return [nn.Flatten()]
        if t == "dense":
            units = int(layer.get("units"))
            bias = bool(layer.get("bias", True))
            feat = in_features if layout == "features" else channels * height * width
            return [nn.Linear(feat, units, bias=bias)]
        if t == "dropout":
            return [nn.Dropout(float(layer.get("rate", 0.0)))]
        if t == "activation":
            return [_activation_module(str(layer.get("name", "relu")))]
        if t == "batch_norm":
            if layout == "nchw":
                nf = int(layer.get("num_features", channels))
                return [nn.BatchNorm2d(nf)]
            nf = int(layer.get("num_features", in_features))
            return [nn.BatchNorm1d(nf)]
        if t == "layer_norm":
            shape = layer.get("normalized_shape")
            if shape is None:
                shape = in_features if layout == "features" else channels
            return [nn.LayerNorm(int(shape) if isinstance(shape, int) else tuple(shape))]
        if t == "identity":
            return [nn.Identity()]
        raise ValueError(f"unsupported layer type '{t}'")

    @staticmethod
    def _update_shape(
        layer: LayerSpec,
        *,
        layout: str,
        channels: int,
        height: int,
        width: int,
        in_features: int,
    ) -> tuple[str, int, int, int, int]:
        t = layer.type
        if t == "conv2d":
            out_c = int(layer.get("out_channels"))
            k = int(layer.get("kernel", 3))
            stride = int(layer.get("stride", 1))
            pad = int(layer.get("padding", k // 2))
            height = max(1, (height + 2 * pad - k) // stride + 1)
            width = max(1, (width + 2 * pad - k) // stride + 1)
            return layout, out_c, height, width, out_c * height * width
        if t in {"max_pool2d", "avg_pool2d"}:
            k = int(layer.get("kernel", 2))
            s = int(layer.get("stride", k))
            height = max(1, (height - k) // s + 1)
            width = max(1, (width - k) // s + 1)
            return layout, channels, height, width, channels * height * width
        if t == "flatten":
            feat = channels * height * width if layout == "nchw" else in_features
            return "features", channels, 1, 1, feat
        if t == "dense":
            units = int(layer.get("units"))
            return "features", channels, 1, 1, units
        if t == "batch_norm" and layout == "nchw":
            nf = int(layer.get("num_features", channels))
            return layout, nf, height, width, nf * height * width
        return layout, channels, height, width, in_features

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass. Accepts NHWC or NCHW for image inputs."""
        if x.ndim == 4:
            # Domain DatasetHandle stores NHWC; convert to NCHW for convs.
            if x.shape[-1] in (1, 3) and x.shape[1] not in (1, 3):
                x = x.permute(0, 3, 1, 2).contiguous()
        logits = self.net(x)
        return torch.as_tensor(logits)
