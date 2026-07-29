"""Incremental dataset builder — immutable previous versions (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class MergeStrategy(str, Enum):
    """How candidate data is combined with a reference set."""

    APPEND = "append"
    REPLACE = "replace"
    MERGE = "merge"
    ROLLING_WINDOW = "rolling_window"
    SLIDING_WINDOW = "sliding_window"
    SAMPLING = "sampling"


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Built feature/label arrays with strategy metadata."""

    features: np.ndarray
    labels: np.ndarray
    strategy: MergeStrategy
    n_samples: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize without arrays."""
        return {
            "strategy": self.strategy.value,
            "n_samples": self.n_samples,
            "feature_shape": list(self.features.shape),
            "metadata": dict(self.metadata),
        }


class IncrementalDatasetBuilder:
    """Prepare updated datasets without mutating prior arrays."""

    def build(
        self,
        reference_features: np.ndarray | None,
        reference_labels: np.ndarray | None,
        candidate_features: np.ndarray,
        candidate_labels: np.ndarray,
        *,
        strategy: MergeStrategy | str = MergeStrategy.APPEND,
        window_size: int | None = None,
        sample_fraction: float = 1.0,
        seed: int = 42,
    ) -> BuildResult:
        """Build a new immutable dataset view."""
        strategy_enum = (
            strategy if isinstance(strategy, MergeStrategy) else MergeStrategy(str(strategy))
        )
        cand_x = np.asarray(candidate_features).copy()
        cand_y = np.asarray(candidate_labels).copy()
        ref_x = None if reference_features is None else np.asarray(reference_features)
        ref_y = None if reference_labels is None else np.asarray(reference_labels)
        meta: dict[str, Any] = {"seed": seed}

        if strategy_enum == MergeStrategy.REPLACE or ref_x is None or ref_y is None:
            out_x, out_y = cand_x, cand_y
        elif strategy_enum == MergeStrategy.APPEND:
            out_x = np.concatenate([ref_x, cand_x], axis=0)
            out_y = np.concatenate([ref_y, cand_y], axis=0)
        elif strategy_enum == MergeStrategy.MERGE:
            # Deduplicate by appending then keeping first unique row hashes later via sampling
            out_x = np.concatenate([ref_x, cand_x], axis=0)
            out_y = np.concatenate([ref_y, cand_y], axis=0)
            out_x, out_y = self._dedupe(out_x, out_y)
            meta["deduped"] = True
        elif strategy_enum in {MergeStrategy.ROLLING_WINDOW, MergeStrategy.SLIDING_WINDOW}:
            combined_x = np.concatenate([ref_x, cand_x], axis=0)
            combined_y = np.concatenate([ref_y, cand_y], axis=0)
            w = int(window_size or combined_x.shape[0])
            out_x = combined_x[-w:]
            out_y = combined_y[-w:]
            meta["window_size"] = w
        elif strategy_enum == MergeStrategy.SAMPLING:
            combined_x = np.concatenate([ref_x, cand_x], axis=0)
            combined_y = np.concatenate([ref_y, cand_y], axis=0)
            frac = float(np.clip(sample_fraction, 0.0, 1.0))
            n = max(1, int(round(frac * combined_x.shape[0])))
            rng = np.random.default_rng(seed)
            idx = np.sort(rng.choice(combined_x.shape[0], size=n, replace=False))
            out_x = combined_x[idx]
            out_y = combined_y[idx]
            meta["sample_fraction"] = frac
            meta["n_sampled"] = n
        else:
            raise ValueError(f"unsupported merge strategy: {strategy_enum}")

        return BuildResult(
            features=out_x,
            labels=out_y,
            strategy=strategy_enum,
            n_samples=int(out_x.shape[0]),
            metadata=meta,
        )

    @staticmethod
    def _dedupe(features: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Keep first occurrence of each (feature-row, label) pair."""
        from evonas.domain.common.hashing import sha256_array

        seen: set[str] = set()
        keep: list[int] = []
        flat = np.ascontiguousarray(features).reshape(features.shape[0], -1)
        labs = np.ascontiguousarray(labels).reshape(labels.shape[0], -1)
        for i in range(features.shape[0]):
            key = sha256_array(flat[i]) + ":" + sha256_array(labs[i])
            if key not in seen:
                seen.add(key)
                keep.append(i)
        idx = np.asarray(keep, dtype=np.int64)
        return features[idx], labels[idx]
