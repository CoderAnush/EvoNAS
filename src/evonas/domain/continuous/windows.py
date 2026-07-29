"""Window cursors for simulating continuous data streams (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evonas.domain.common.enums import Split
from evonas.domain.data.models import DataWindow, DatasetHandle
from evonas.ports.dataset import IDatasetManager


@dataclass(slots=True)
class WindowCursor:
    """Index cursor over a static dataset split (stream simulation)."""

    split: Split = Split.TRAIN
    start: int = 0
    end: int = 0
    step: int = 10
    window_size: int = 50
    mode: str = "sliding"  # sliding | expanding
    max_end: int | None = None

    def current(self) -> DataWindow:
        """Return current window descriptor."""
        return DataWindow(
            split=self.split,
            start_idx=self.start,
            end_idx=self.end,
            window_id=f"{self.split.value}:{self.start}:{self.end}",
        )

    def advance(self) -> DataWindow:
        """Advance cursor by ``step`` according to mode."""
        if self.max_end is not None and self.end >= self.max_end:
            return self.current()
        self.end = min(
            self.end + self.step,
            self.max_end if self.max_end is not None else self.end + self.step,
        )
        if self.mode == "sliding":
            self.start = max(0, self.end - self.window_size)
        else:
            # expanding: keep start fixed
            self.start = 0
        return self.current()

    def to_dict(self) -> dict[str, Any]:
        """Serialize cursor."""
        return {
            "split": self.split.value,
            "start": self.start,
            "end": self.end,
            "step": self.step,
            "window_size": self.window_size,
            "mode": self.mode,
            "max_end": self.max_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WindowCursor:
        """Load cursor."""
        split = data.get("split", "train")
        return cls(
            split=Split(str(split)) if not isinstance(split, Split) else split,
            start=int(data.get("start", 0)),
            end=int(data.get("end", 0)),
            step=int(data.get("step", 10)),
            window_size=int(data.get("window_size", 50)),
            mode=str(data.get("mode", "sliding")),
            max_end=data.get("max_end"),
        )


@dataclass(slots=True)
class WindowManager:
    """Coordinate windows via IDatasetManager.get_window (Phase 1 API)."""

    dataset: IDatasetManager
    cursor: WindowCursor = field(default_factory=WindowCursor)

    def bootstrap(self, *, initial_end: int | None = None) -> DataWindow:
        """Initialize cursor bounds from prepared train split size."""
        handle = self.dataset.load(self.cursor.split)
        n = handle.size
        self.cursor.max_end = n
        end = initial_end if initial_end is not None else min(self.cursor.window_size, n)
        self.cursor.start = 0 if self.cursor.mode == "expanding" else max(0, end - self.cursor.window_size)
        self.cursor.end = end
        return self.cursor.current()

    def current_handle(self) -> DatasetHandle:
        """Materialize current window through Phase 1 DatasetManager."""
        w = self.cursor.current()
        return self.dataset.get_window(w.start_idx, w.end_idx, split=w.split)

    def advance_handle(self) -> DatasetHandle:
        """Advance cursor and return the new handle."""
        self.cursor.advance()
        return self.current_handle()
