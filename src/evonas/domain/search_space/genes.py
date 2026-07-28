"""Gene specifications for continuous search-space encodings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GeneSpec:
    """One continuous gene dimension in the search space."""

    name: str
    kind: str  # int | float | cat
    low: float
    high: float
    choices: tuple[Any, ...] = ()
    step: float | None = None

    def decode(self, value: float) -> Any:
        """Decode a continuous value into a discrete/typed gene."""
        x = min(max(float(value), self.low), self.high)
        if self.kind == "cat":
            if not self.choices:
                raise ValueError(f"categorical gene {self.name} has no choices")
            span = self.high - self.low
            if span <= 0:
                return self.choices[0]
            ratio = (x - self.low) / span
            idx = int(ratio * len(self.choices))
            idx = min(max(idx, 0), len(self.choices) - 1)
            return self.choices[idx]
        if self.kind == "int":
            if self.step:
                k = round((x - self.low) / self.step)
                return int(self.low + k * self.step)
            return int(round(x))
        return float(x)

    def encode(self, discrete: Any) -> float:
        """Encode a discrete gene back to a continuous representative."""
        if self.kind == "cat":
            try:
                idx = list(self.choices).index(discrete)
            except ValueError:
                idx = 0
            if len(self.choices) <= 1:
                return float(self.low)
            return float(self.low + (idx + 0.5) * (self.high - self.low) / len(self.choices))
        return float(min(max(float(discrete), self.low), self.high))
