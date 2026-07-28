"""Architecture summary / text visualization."""

from __future__ import annotations

from evonas.domain.architecture.complexity import estimate_complexity
from evonas.domain.model.architecture_spec import ArchitectureSpec


class ArchitectureVisualizer:
    """Render human-readable architecture summaries (no GUI dependency)."""

    def summarize(self, spec: ArchitectureSpec) -> str:
        """Return a multi-line text diagram of the architecture."""
        lines = [
            f"Architecture: {spec.name} (v{spec.version})",
            f"schema={spec.schema_version}  arch_id={spec.arch_id()[:12]}…",
            f"input={list(spec.input_shape)}  classes={spec.num_classes}",
            "",
            f"Input {list(spec.input_shape)}",
        ]
        for layer in spec.resolved_layers():
            lines.append("↓")
            lines.append(self._format_layer(layer.type, layer.params))
        report = estimate_complexity(spec)
        lines.extend(
            [
                "",
                f"depth={report.depth}  ~params={report.estimated_params}  "
                f"conv={report.n_conv}  dense={report.n_dense}",
            ]
        )
        return "\n".join(lines)

    def export_text(self, spec: ArchitectureSpec, path: str) -> str:
        """Write summary to a text file and return the summary string."""
        text = self.summarize(spec)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
        return text

    @staticmethod
    def _format_layer(layer_type: str, params: dict) -> str:
        if layer_type == "dense":
            return f"Dense {params.get('units')}"
        if layer_type == "dropout":
            return f"Dropout {params.get('rate')}"
        if layer_type == "activation":
            return str(params.get("name", "activation")).upper()
        if layer_type == "conv2d":
            return (
                f"Conv2D out={params.get('out_channels')} "
                f"k={params.get('kernel')} s={params.get('stride', 1)}"
            )
        if layer_type == "max_pool2d":
            return f"MaxPool2D k={params.get('kernel')}"
        if layer_type == "avg_pool2d":
            return f"AvgPool2D k={params.get('kernel')}"
        if layer_type == "batch_norm":
            return "BatchNorm"
        if layer_type == "flatten":
            return "Flatten"
        return f"{layer_type} {params}"
