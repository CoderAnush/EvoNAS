"""Continuous-learning visualizations (matplotlib optional)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.domain.continuous.history import LearningHistory
from evonas.domain.continuous.lineage import DatasetLineage

logger = logging.getLogger(__name__)


class ContinuousLearningVisualizer:
    """Simple matplotlib plots for CL timelines / drift / events."""

    def plot_all(
        self,
        history: LearningHistory,
        lineage: DatasetLineage,
        out_dir: str | Path,
    ) -> dict[str, str]:
        """Write available plots; skip silently without matplotlib."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        written: dict[str, str] = {}
        for name, fn in (
            ("dataset_timeline.png", lambda p: self._plot_timeline(history, p)),
            ("version_graph.png", lambda p: self._plot_lineage(lineage, p)),
            ("drift_history.png", lambda p: self._plot_drift(history, p)),
            ("learning_events.png", lambda p: self._plot_events(history, p)),
        ):
            path = fn(out / name)
            if path:
                written[name] = str(path)
        return written

    def _pyplot(self) -> Any | None:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            return plt
        except Exception as exc:  # noqa: BLE001
            logger.info("matplotlib unavailable (%s)", exc)
            return None

    def _plot_timeline(self, history: LearningHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.versions:
            return None
        try:
            ns = [int(v.get("n_samples", 0)) for v in history.versions]
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(range(len(ns)), ns, marker="o")
            ax.set_title("Dataset Version Timeline (n_samples)")
            ax.set_xlabel("version index")
            ax.set_ylabel("samples")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("timeline plot failed: %s", exc)
            return None

    def _plot_lineage(self, lineage: DatasetLineage, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not lineage.edges:
            return None
        try:
            labels = [f"{e.parent_id[:8]}→{e.child_id[:8]}" for e in lineage.edges]
            fig, ax = plt.subplots(figsize=(8, max(3, 0.35 * len(labels))))
            ax.barh(labels, [1] * len(labels), color="#1f77b4")
            ax.set_title("Dataset Version Graph (edges)")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("lineage plot failed: %s", exc)
            return None

    def _plot_drift(self, history: LearningHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.drift_reports:
            return None
        try:
            psi = [float(d.get("psi", 0.0)) for d in history.drift_reports]
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(range(len(psi)), psi, marker="s", color="#d62728")
            ax.set_title("Drift History (PSI)")
            ax.set_xlabel("report index")
            ax.set_ylabel("PSI")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("drift plot failed: %s", exc)
            return None

    def _plot_events(self, history: LearningHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.events:
            return None
        try:
            counts: dict[str, int] = {}
            for event in history.events:
                key = str(event.get("event_type", "unknown"))
                counts[key] = counts.get(key, 0) + 1
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.barh(list(counts.keys()), list(counts.values()), color="#2ca02c")
            ax.set_title("Learning Events")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("events plot failed: %s", exc)
            return None
