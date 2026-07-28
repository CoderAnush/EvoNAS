"""Dataset materialization loaders (synthetic + optional torchvision)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from evonas.domain.common.enums import DatasetSource, TaskType
from evonas.domain.common.errors import DataError
from evonas.domain.data.models import Schema

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Materialize feature/label arrays from a dataset configuration.

    Responsibility: raw sample generation / loading only (SRP).
    """

    def load_raw(self, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, Schema]:
        """Return ``(features, labels, schema)`` for the configured source."""
        source = str(config.get("source", DatasetSource.SYNTHETIC.value))
        seed = int(config.get("seed", 42))
        input_shape = tuple(int(x) for x in config["input_shape"])
        num_classes = int(config.get("num_classes", 2))
        num_samples = int(config.get("num_samples", 300))
        dtype = str(config.get("dtype", "float32"))
        name = str(config["name"])
        version = str(config.get("version", "1.0.0"))
        task_type = TaskType(str(config.get("task_type", TaskType.IMAGE_CLASSIFICATION.value)))

        if source == DatasetSource.TORCHVISION.value:
            features, labels = self._load_torchvision(config)
        else:
            features, labels = self._load_synthetic(
                source=source,
                seed=seed,
                input_shape=input_shape,
                num_classes=num_classes,
                num_samples=num_samples,
                dtype=dtype,
            )

        feature_dim = int(np.prod(input_shape))
        schema = Schema(
            name=name,
            version=version,
            task_type=task_type,
            input_shape=input_shape,
            num_classes=num_classes,
            dtype=dtype,
            feature_dim=feature_dim,
            metadata={"source": source, "num_samples": int(features.shape[0])},
        )
        logger.info(
            "Loaded raw dataset name=%s source=%s n=%d shape=%s",
            name,
            source,
            features.shape[0],
            features.shape[1:],
        )
        return features, labels, schema

    def _load_synthetic(
        self,
        *,
        source: str,
        seed: int,
        input_shape: tuple[int, ...],
        num_classes: int,
        num_samples: int,
        dtype: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate deterministic class-conditional synthetic images."""
        import hashlib

        rng = np.random.default_rng(seed)
        # Stable source bias (never use built-in hash() — it is process-randomized).
        source_bias = (
            int(hashlib.sha256(source.encode("utf-8")).hexdigest()[:8], 16) % 1000
        ) / 1000.0
        labels = rng.integers(0, num_classes, size=num_samples, dtype=np.int64)
        features = rng.normal(loc=0.0, scale=0.3, size=(num_samples, *input_shape)).astype(dtype)
        for i, y in enumerate(labels):
            features[i] = features[i] + (0.15 * float(y) + 0.05 * source_bias)
        features = np.clip(features, 0.0, 1.0).astype(dtype, copy=False)
        return features, labels

    def _load_torchvision(self, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
        """Optional torchvision path — requires ``evonas[pytorch]`` extra."""
        try:
            from evonas.infrastructure.data.torchvision_loader import load_torchvision_dataset
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise DataError(
                "torchvision loader unavailable; install evonas[pytorch] or use synthetic source",
                code="EN_DATA_001",
            ) from exc
        return load_torchvision_dataset(config)
