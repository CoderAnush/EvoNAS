"""Deterministic feature transforms for the data pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TransformConfig:
    """Configuration for the transform pipeline."""

    normalize: bool = True
    flatten: bool = False
    eps: float = 1e-8


class TransformPipeline:
    """Apply a sequence of deterministic transforms to feature arrays.

    Responsibility: feature transformation only (SRP). Does not load data,
    split data, or compute drift.
    """

    def __init__(self, config: TransformConfig | None = None) -> None:
        self._config = config or TransformConfig()

    @property
    def config(self) -> TransformConfig:
        """Return the active transform configuration."""
        return self._config

    def apply(self, features: np.ndarray) -> np.ndarray:
        """Apply configured transforms and return a new array."""
        out = np.asarray(features, dtype=np.float32)
        if self._config.flatten:
            out = out.reshape(out.shape[0], -1)
            logger.debug("Flattened features to shape %s", out.shape)
        if self._config.normalize:
            out = self._normalize(out)
            logger.debug("Normalized features")
        return out

    def _normalize(self, features: np.ndarray) -> np.ndarray:
        """Per-sample min-max normalize into approximately [0, 1]."""
        flat = features.reshape(features.shape[0], -1)
        mins = flat.min(axis=1, keepdims=True)
        maxs = flat.max(axis=1, keepdims=True)
        denom = np.maximum(maxs - mins, self._config.eps)
        norm = (flat - mins) / denom
        normalized = norm.reshape(features.shape).astype(np.float32, copy=False)
        return np.asarray(normalized, dtype=np.float32)
