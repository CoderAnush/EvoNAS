"""Optional torchvision dataset bridge (pytorch extra)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from evonas.domain.common.errors import DataError

logger = logging.getLogger(__name__)


def load_torchvision_dataset(config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Load a torchvision vision dataset and return NumPy features/labels.

    Phase 1 keeps this behind an optional dependency so CI remains torch-free.
    """
    try:
        from torchvision import datasets  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise DataError(
            "torchvision is not installed; pip install 'evonas[pytorch]'",
            code="EN_DATA_001",
        ) from exc

    name = str(config["name"]).lower()
    root = str(config.get("root", "artifacts/datasets/torchvision"))
    download = bool(config.get("download", True))
    max_samples = int(config.get("num_samples", 1000))

    mapping = {
        "mnist": datasets.MNIST,
        "fashion_mnist": datasets.FashionMNIST,
        "cifar10": datasets.CIFAR10,
    }
    if name not in mapping:
        raise DataError(f"unsupported torchvision dataset: {name}", code="EN_DATA_001")

    ds = mapping[name](root=root, train=True, download=download)
    n = min(len(ds), max_samples)
    images: list[np.ndarray] = []
    labels: list[int] = []
    for i in range(n):
        img, label = ds[i]
        arr = np.asarray(img, dtype=np.float32)
        if arr.ndim == 2:
            arr = arr[:, :, None]
        if arr.max() > 1.0:
            arr = arr / 255.0
        images.append(arr)
        labels.append(int(label))

    features = np.stack(images, axis=0)
    label_arr = np.asarray(labels, dtype=np.int64)
    logger.info("Loaded torchvision dataset=%s n=%d", name, n)
    return features, label_arr
