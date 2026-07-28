"""Filesystem checkpoint manager (idea.md ICheckpointManager)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import torch

from evonas.domain.common.errors import CheckpointError

logger = logging.getLogger(__name__)


class FileCheckpointManager:
    """Save / load training checkpoints under an experiment directory.

    Stores best model, latest model, and JSON sidecar metadata so future
    phases can resume or compare runs.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Checkpoint root directory."""
        return self._root

    def save(self, name: str, state: dict[str, Any]) -> str:
        """Atomically save a checkpoint dict; return path string."""
        path = self._root / f"{name}.pt"
        tmp = path.with_suffix(".pt.tmp")
        try:
            torch.save(state, tmp)
            tmp.replace(path)
        except Exception as exc:  # noqa: BLE001
            raise CheckpointError(f"failed to save checkpoint {name}: {exc}") from exc
        meta = {k: v for k, v in state.items() if k not in {"model_state", "optimizer_state"}}
        meta_path = self._root / f"{name}.meta.json"
        meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
        logger.info("Saved checkpoint name=%s path=%s", name, path)
        return str(path)

    def load(self, uri: str) -> dict[str, Any]:
        """Load a checkpoint from a path/URI."""
        path = Path(uri)
        if not path.exists():
            raise CheckpointError(f"checkpoint not found: {path}")
        try:
            state = torch.load(path, map_location="cpu", weights_only=False)
        except TypeError:
            # Older torch without weights_only
            state = torch.load(path, map_location="cpu")
        except Exception as exc:  # noqa: BLE001
            raise CheckpointError(f"failed to load checkpoint {path}: {exc}") from exc
        if not isinstance(state, dict):
            raise CheckpointError("checkpoint payload must be a dict")
        return state

    def list(self) -> list[str]:
        """List checkpoint file paths."""
        return sorted(str(p) for p in self._root.glob("*.pt"))
