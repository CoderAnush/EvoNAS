"""Architecture validation and constraint repair hooks."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from evonas.domain.architecture.layers import ACTIVATIONS, LAYER_TYPES, LayerSpec
from evonas.domain.common.errors import ArchitectureError
from evonas.domain.model.architecture_spec import ArchitectureSpec

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ArchitectureLimits:
    """Soft/hard limits for architecture validation (config-driven later)."""

    min_layers: int = 1
    max_layers: int = 64
    min_dense_units: int = 1
    max_dense_units: int = 4096
    min_channels: int = 1
    max_channels: int = 1024
    min_dropout: float = 0.0
    max_dropout: float = 0.9
    require_output_dense: bool = True


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of architecture validation."""

    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def error_message(self) -> str:
        """Joined error string."""
        return "; ".join(self.errors)


class ArchitectureValidator:
    """Validate ArchitectureSpec structural and numeric constraints."""

    def __init__(self, limits: ArchitectureLimits | None = None) -> None:
        self._limits = limits or ArchitectureLimits()

    def validate(self, spec: ArchitectureSpec) -> ValidationResult:
        """Validate ``spec`` and return errors/warnings without raising."""
        errors: list[str] = []
        warnings: list[str] = []

        if not spec.name:
            errors.append("name must be non-empty")
        if not spec.input_shape or any(d <= 0 for d in spec.input_shape):
            errors.append("input_shape must contain positive dimensions")
        if spec.num_classes < 2:
            errors.append("num_classes must be >= 2")
        if not (self._limits.min_dropout <= spec.dropout <= self._limits.max_dropout):
            errors.append(
                f"dropout {spec.dropout} outside "
                f"[{self._limits.min_dropout}, {self._limits.max_dropout}]"
            )

        layers = spec.resolved_layers()
        if len(layers) < self._limits.min_layers:
            errors.append(f"too few layers: {len(layers)} < {self._limits.min_layers}")
        if len(layers) > self._limits.max_layers:
            errors.append(f"too many layers: {len(layers)} > {self._limits.max_layers}")

        for i, layer in enumerate(layers):
            errors.extend(self._validate_layer(i, layer))

        if self._limits.require_output_dense:
            if not layers or layers[-1].type != "dense":
                errors.append("final layer must be dense (classification logits)")
            elif int(layers[-1].get("units", -1)) != spec.num_classes:
                errors.append(
                    f"final dense units must equal num_classes "
                    f"({layers[-1].get('units')} != {spec.num_classes})"
                )

        # Spatial consistency warnings for conv stacks
        if len(spec.input_shape) == 3:
            h, w, _ = spec.input_shape
            for layer in layers:
                if layer.type in {"max_pool2d", "avg_pool2d"}:
                    k = int(layer.get("kernel", 2))
                    h, w = max(1, h // k), max(1, w // k)
            if h < 1 or w < 1:
                errors.append("pooling reduces spatial size below 1")

        ok = not errors
        if not ok:
            logger.warning("Architecture validation failed for %s: %s", spec.name, errors)
        return ValidationResult(ok=ok, errors=tuple(errors), warnings=tuple(warnings))

    def require_valid(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Raise ArchitectureError when validation fails; else return spec."""
        result = self.validate(spec)
        if not result.ok:
            raise ArchitectureError(result.error_message)
        return spec

    def _validate_layer(self, index: int, layer: LayerSpec) -> list[str]:
        errors: list[str] = []
        prefix = f"layers[{index}]"
        if layer.type not in LAYER_TYPES:
            errors.append(f"{prefix}: unknown type '{layer.type}'")
            return errors
        if layer.type == "dense":
            units = layer.get("units")
            if units is None:
                errors.append(f"{prefix}.dense: units required")
            else:
                u = int(units)
                if not (self._limits.min_dense_units <= u <= self._limits.max_dense_units):
                    errors.append(f"{prefix}.dense: units {u} out of range")
        elif layer.type == "dropout":
            rate = float(layer.get("rate", -1))
            if not (self._limits.min_dropout <= rate <= self._limits.max_dropout):
                errors.append(f"{prefix}.dropout: rate {rate} out of range")
        elif layer.type == "activation":
            name = str(layer.get("name", "")).lower()
            if name not in ACTIVATIONS:
                errors.append(f"{prefix}.activation: invalid '{name}'")
        elif layer.type == "conv2d":
            ch = layer.get("out_channels")
            if ch is None:
                errors.append(f"{prefix}.conv2d: out_channels required")
            else:
                c = int(ch)
                if not (self._limits.min_channels <= c <= self._limits.max_channels):
                    errors.append(f"{prefix}.conv2d: out_channels {c} out of range")
            k = int(layer.get("kernel", 3))
            if k < 1 or k % 2 == 0:
                warnings_note = f"{prefix}.conv2d: unusual kernel {k}"
                logger.debug(warnings_note)
        return errors


class ConstraintHandler:
    """Initial constraint handler — repair obvious issues where deterministic."""

    def __init__(self, validator: ArchitectureValidator | None = None) -> None:
        self._validator = validator or ArchitectureValidator()

    def repair(self, spec: ArchitectureSpec) -> ArchitectureSpec:
        """Attempt deterministic repairs; validate afterward."""
        layers = list(spec.resolved_layers())
        # Ensure final dense matches num_classes
        if layers and layers[-1].type == "dense":
            if int(layers[-1].get("units", -1)) != spec.num_classes:
                layers[-1] = LayerSpec("dense", {**layers[-1].params, "units": spec.num_classes})
        elif not layers or layers[-1].type != "dense":
            layers.append(LayerSpec("dense", {"units": spec.num_classes, "bias": True}))

        repaired = ArchitectureSpec(
            name=spec.name,
            version=spec.version,
            task_type=spec.task_type,
            input_shape=spec.input_shape,
            num_classes=spec.num_classes,
            conv_blocks=spec.conv_blocks,
            dense_units=spec.dense_units,
            dropout=min(max(spec.dropout, 0.0), 0.9),
            layers=tuple(layers),
            schema_version="3.0",
            metadata={**spec.metadata, "repaired": True},
        )
        return self._validator.require_valid(repaired)
