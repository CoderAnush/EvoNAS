"""Checksum and deterministic split helpers."""

from __future__ import annotations

import hashlib
import logging

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.common.errors import DataError

logger = logging.getLogger(__name__)


def sha256_array(array: np.ndarray) -> str:
    """Compute a SHA-256 hex digest over a NumPy array's raw bytes + shape/dtype."""
    arr = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(str(arr.shape).encode("utf-8"))
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(arr.tobytes())
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex digest of arbitrary bytes."""
    return hashlib.sha256(data).hexdigest()


def make_splits(
    n_samples: int,
    ratios: dict[str, float],
    *,
    seed: int,
    shuffle: bool = True,
) -> dict[Split, np.ndarray]:
    """Create deterministic, disjoint train/val/test index arrays.

    Raises
    ------
    DataError
        If ratios are invalid or produce an empty required split.
    """
    if n_samples <= 0:
        raise DataError("n_samples must be positive", code="EN_DATA_002")

    required = {Split.TRAIN.value, Split.VAL.value, Split.TEST.value}
    if set(ratios) != required:
        raise DataError(
            f"splits must define exactly {sorted(required)}, got {sorted(ratios)}",
            code="EN_DATA_001",
        )
    total = sum(ratios.values())
    if abs(total - 1.0) > 1e-6:
        raise DataError(f"split ratios must sum to 1.0, got {total}", code="EN_DATA_001")

    rng = np.random.default_rng(seed)
    indices = np.arange(n_samples, dtype=np.int64)
    if shuffle:
        rng.shuffle(indices)

    n_train = int(ratios[Split.TRAIN.value] * n_samples)
    n_val = int(ratios[Split.VAL.value] * n_samples)
    # Remainder goes to test to preserve exact coverage
    n_test = n_samples - n_train - n_val
    if min(n_train, n_val, n_test) <= 0:
        raise DataError(
            f"degenerate split sizes for n={n_samples}: train={n_train}, val={n_val}, test={n_test}",
            code="EN_DATA_002",
        )

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]
    splits = {
        Split.TRAIN: np.sort(train_idx),
        Split.VAL: np.sort(val_idx),
        Split.TEST: np.sort(test_idx),
    }
    logger.info(
        "Created splits seed=%s train=%d val=%d test=%d",
        seed,
        len(train_idx),
        len(val_idx),
        len(test_idx),
    )
    return splits
