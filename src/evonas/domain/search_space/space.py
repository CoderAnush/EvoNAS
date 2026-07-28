"""Search space definition objects (Phase 3 — decode only, no PSO)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from evonas.domain.search_space.genes import GeneSpec


@dataclass(frozen=True, slots=True)
class SearchSpace:
    """Bounded gene space for architecture genotypes (Quick Mode sized)."""

    name: str
    genes: tuple[GeneSpec, ...]
    input_shape: tuple[int, ...]
    num_classes: int
    metadata: dict[str, Any] | None = None

    @property
    def dimension(self) -> int:
        """Genotype dimensionality."""
        return len(self.genes)

    def bounds(self) -> tuple[list[float], list[float]]:
        """Return (lows, highs) vectors."""
        lows = [g.low for g in self.genes]
        highs = [g.high for g in self.genes]
        return lows, highs

    @classmethod
    def cnn_quick(
        cls,
        *,
        input_shape: tuple[int, ...] = (8, 8, 1),
        num_classes: int = 3,
    ) -> SearchSpace:
        """Small Phase 3 / Quick Mode CNN search space (idea.md)."""
        genes = (
            GeneSpec("n_blocks", "int", 1, 2),
            GeneSpec("ch0", "int", 8, 32, step=8),
            GeneSpec("ch1", "int", 8, 32, step=8),
            GeneSpec("act", "cat", 0.0, 1.0, choices=("relu", "gelu")),
            GeneSpec("dropout", "float", 0.0, 0.4),
            GeneSpec("dense_units", "int", 16, 64, step=16),
        )
        return cls(
            name="cnn_quick",
            genes=genes,
            input_shape=input_shape,
            num_classes=num_classes,
            metadata={"phase": 3},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchSpace:
        """Load SearchSpace from a mapping (YAML/JSON)."""
        genes = tuple(
            GeneSpec(
                name=str(g["name"]),
                kind=str(g["kind"]),
                low=float(g["low"]),
                high=float(g["high"]),
                choices=tuple(g.get("choices", ()) or ()),
                step=float(g["step"]) if g.get("step") is not None else None,
            )
            for g in data.get("genes", [])
        )
        return cls(
            name=str(data.get("name", "unnamed")),
            genes=genes,
            input_shape=tuple(int(x) for x in data["input_shape"]),
            num_classes=int(data["num_classes"]),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> SearchSpace:
        """Load SearchSpace from a YAML file."""
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("search space YAML root must be a mapping")
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize search space."""
        return {
            "name": self.name,
            "input_shape": list(self.input_shape),
            "num_classes": self.num_classes,
            "genes": [
                {
                    "name": g.name,
                    "kind": g.kind,
                    "low": g.low,
                    "high": g.high,
                    "choices": list(g.choices),
                    "step": g.step,
                }
                for g in self.genes
            ],
            "metadata": dict(self.metadata or {}),
        }
