"""Domain-safe hashing helpers (framework-agnostic)."""

from __future__ import annotations

import hashlib

import numpy as np


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
