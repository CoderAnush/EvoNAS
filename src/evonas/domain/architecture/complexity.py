"""Architecture complexity estimates (params proxy)."""

from __future__ import annotations

from dataclasses import dataclass

from evonas.domain.model.architecture_spec import ArchitectureSpec


@dataclass(frozen=True, slots=True)
class ComplexityReport:
    """Estimated complexity for an architecture (framework-agnostic proxy)."""

    estimated_params: int
    depth: int
    n_conv: int
    n_dense: int

    def to_dict(self) -> dict[str, int]:
        """Serialize report."""
        return {
            "estimated_params": self.estimated_params,
            "depth": self.depth,
            "n_conv": self.n_conv,
            "n_dense": self.n_dense,
        }


def estimate_complexity(spec: ArchitectureSpec) -> ComplexityReport:
    """Estimate parameter count from layer IR without instantiating a backend."""
    layers = spec.resolved_layers()
    h, w, c = (spec.input_shape + (1, 1, 1))[:3]
    if len(spec.input_shape) == 3:
        h, w, c = spec.input_shape
    params = 0
    in_features = None
    n_conv = 0
    n_dense = 0
    for layer in layers:
        if layer.type == "conv2d":
            n_conv += 1
            out_c = int(layer.get("out_channels"))
            k = int(layer.get("kernel", 3))
            params += (c * k * k + 1) * out_c
            c = out_c
            stride = int(layer.get("stride", 1))
            pad = int(layer.get("padding", k // 2))
            h = max(1, (h + 2 * pad - k) // stride + 1)
            w = max(1, (w + 2 * pad - k) // stride + 1)
        elif layer.type in {"max_pool2d", "avg_pool2d"}:
            k = int(layer.get("kernel", 2))
            s = int(layer.get("stride", k))
            h = max(1, (h - k) // s + 1)
            w = max(1, (w - k) // s + 1)
        elif layer.type == "flatten":
            in_features = c * h * w
        elif layer.type == "dense":
            n_dense += 1
            units = int(layer.get("units"))
            if in_features is None:
                in_features = c * h * w if len(spec.input_shape) == 3 else int(spec.input_shape[0])
            params += (in_features + 1) * units
            in_features = units
    return ComplexityReport(
        estimated_params=int(params),
        depth=len(layers),
        n_conv=n_conv,
        n_dense=n_dense,
    )
