"""In-process event hub for WebSocket fan-out."""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)


class EventHub:
    """Thread-safe event bus bridging sync job workers → async WebSockets."""

    def __init__(self, *, history: int = 64) -> None:
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self._lock = threading.Lock()
        self._history: deque[dict[str, Any]] = deque(maxlen=history)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the running asyncio loop (call from FastAPI startup)."""
        self._loop = loop

    def publish(self, event: dict[str, Any]) -> None:
        """Publish from any thread."""
        with self._lock:
            self._history.append(event)
            subs = list(self._subscribers)
            loop = self._loop
        if loop is None or not loop.is_running():
            return
        for queue in subs:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception:  # noqa: BLE001
                logger.debug("Dropping event for dead subscriber", exc_info=True)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """Register an async subscriber queue."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        with self._lock:
            self._subscribers.append(queue)
            recent = list(self._history)
        for item in recent:
            try:
                queue.put_nowait(item)
            except asyncio.QueueFull:
                break
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove a subscriber."""
        with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent events for REST polling."""
        with self._lock:
            items = list(self._history)
        return items[-limit:]
