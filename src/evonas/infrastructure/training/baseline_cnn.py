"""Simple fixed baseline CNN for Phase 2 benchmarks (not searched / not evolved)."""

from __future__ import annotations

import torch
from torch import nn

from evonas.domain.model.architecture_spec import ArchitectureSpec


def _activation(name: str) -> nn.Module:
    key = name.lower()
    if key == "relu":
        return nn.ReLU(inplace=True)
    if key == "gelu":
        return nn.GELU()
    if key == "tanh":
        return nn.Tanh()
    return nn.ReLU(inplace=True)


class BaselineCNN(nn.Module):
    """Intentionally simple convolutional classifier used as the Phase 2 baseline.

    This model is a fixed benchmark. It must train correctly but is never the
    subject of architecture search in this phase.
    """

    def __init__(self, spec: ArchitectureSpec) -> None:
        super().__init__()
        if len(spec.input_shape) != 3:
            raise ValueError("BaselineCNN expects input_shape (H, W, C)")
        height, width, in_channels = spec.input_shape
        layers: list[nn.Module] = []
        channels = int(in_channels)
        h, w = int(height), int(width)
        for block in spec.conv_blocks:
            padding = block.kernel // 2
            layers.append(
                nn.Conv2d(
                    channels,
                    block.out_channels,
                    kernel_size=block.kernel,
                    stride=block.stride,
                    padding=padding,
                )
            )
            layers.append(_activation(block.activation))
            h = max(1, (h + 2 * padding - block.kernel) // block.stride + 1)
            w = max(1, (w + 2 * padding - block.kernel) // block.stride + 1)
            channels = block.out_channels
            if block.pool:
                layers.append(nn.MaxPool2d(block.pool))
                h = max(1, h // block.pool)
                w = max(1, w // block.pool)
        self.features = nn.Sequential(*layers)
        flat_dim = channels * h * w
        head: list[nn.Module] = [nn.Flatten()]
        prev = flat_dim
        for units in spec.dense_units:
            head.append(nn.Linear(prev, units))
            head.append(_activation("relu"))
            if spec.dropout > 0:
                head.append(nn.Dropout(spec.dropout))
            prev = units
        if spec.dropout > 0 and not spec.dense_units:
            head.append(nn.Dropout(spec.dropout))
        head.append(nn.Linear(prev, spec.num_classes))
        self.classifier = nn.Sequential(*head)
        self._spec_name = spec.name

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass. Accepts NHWC or NCHW float tensors."""
        if x.ndim != 4:
            raise ValueError(f"expected 4D image batch, got shape {tuple(x.shape)}")
        # Domain DatasetHandle stores NHWC; convert to NCHW for convs.
        if x.shape[-1] in (1, 3) and x.shape[1] not in (1, 3):
            x = x.permute(0, 3, 1, 2).contiguous()
        feats = self.features(x)
        logits = self.classifier(feats)
        return torch.as_tensor(logits)
