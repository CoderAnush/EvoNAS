"""Convert Phase 1 DatasetHandle into torch DataLoaders."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from evonas.domain.data.models import DatasetHandle


class HandleDataset(Dataset):
    """Torch Dataset wrapping a Phase 1 DatasetHandle (NHWC float features)."""

    def __init__(self, handle: DatasetHandle) -> None:
        self._x = np.asarray(handle.features, dtype=np.float32)
        self._y = np.asarray(handle.labels, dtype=np.int64).ravel()

    def __len__(self) -> int:
        return int(self._x.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.from_numpy(self._x[index].copy())
        y = torch.tensor(self._y[index], dtype=torch.long)
        return x, y


def make_dataloader(
    handle: DatasetHandle,
    *,
    batch_size: int,
    shuffle: bool,
    num_workers: int = 0,
) -> DataLoader:
    """Create a DataLoader for a DatasetHandle."""
    ds = HandleDataset(handle)
    return DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        drop_last=False,
    )
