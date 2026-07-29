"""Closed-loop timeline visualization (matplotlib optional)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.domain.lifecycle.history import LifecycleHistory

logger = logging.getLogger(__name__)


class LifecycleVisualizer:
    """Simple matplotlib plots for lifecycle / decision timelines."""

    def plot_all(self, history: LifecycleHistory, out_dir: str | Path) -> dict[str, str]:
        """Write available plots; skip silently without matplotlib."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        written: dict[str, str] = {}
        for name, fn in (
            ("lifecycle_timeline.png", self._plot_timeline),
            ("decision_summary.png", self._plot_decisions),
            ("state_transitions.png", self._plot_state_transitions),
            ("acceptance_history.png", self._plot_acceptance),
            ("optimization_events.png", self._plot_optimizations),
        ):
            path = fn(history, out / name)
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

    def _plot_timeline(self, history: LifecycleHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.transitions:
            return None
        states = [t.target for t in history.transitions]
        labels = sorted(set(states))
        mapping = {s: i for i, s in enumerate(labels)}
        ys = [mapping[s] for s in states]
        try:
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.step(range(len(ys)), ys, where="post")
            ax.set_yticks(list(mapping.values()))
            ax.set_yticklabels(list(mapping.keys()), fontsize=8)
            ax.set_title("Closed-Loop Lifecycle Timeline")
            ax.set_xlabel("transition index")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("timeline plot failed: %s", exc)
            return None

    def _plot_decisions(self, history: LifecycleHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.decisions:
            return None
        yes = sum(1 for d in history.decisions if d.get("outcome"))
        no = len(history.decisions) - yes
        try:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar(["YES", "NO"], [yes, no], color=["#2ca02c", "#d62728"])
            ax.set_title("Decision Outcomes")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("decision plot failed: %s", exc)
            return None

    def _plot_state_transitions(self, history: LifecycleHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.transitions:
            return None
        edges: dict[str, int] = {}
        for t in history.transitions:
            key = f"{t.source}→{t.target}"
            edges[key] = edges.get(key, 0) + 1
        try:
            fig, ax = plt.subplots(figsize=(10, 4))
            labels = list(edges.keys())
            values = list(edges.values())
            ax.barh(labels, values, color="#1f77b4")
            ax.set_title("State Transition Counts")
            ax.set_xlabel("count")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("state transition plot failed: %s", exc)
            return None

    def _plot_acceptance(self, history: LifecycleHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.promotions:
            return None
        accepted = sum(1 for p in history.promotions if p.get("accepted"))
        rejected = len(history.promotions) - accepted
        try:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar(
                ["Accepted", "Rejected"],
                [accepted, rejected],
                color=["#2ca02c", "#d62728"],
            )
            ax.set_title("Acceptance History")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("acceptance plot failed: %s", exc)
            return None

    def _plot_optimizations(self, history: LifecycleHistory, path: Path) -> Path | None:
        plt = self._pyplot()
        if plt is None or not history.optimizations:
            return None
        reqs = sum(1 for o in history.optimizations if o.get("request"))
        results = sum(1 for o in history.optimizations if "result" in o)
        accepted = sum(1 for o in history.optimizations if o.get("accepted") is True)
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(
                ["Requests", "Results", "Accepted"],
                [reqs, results, accepted],
                color=["#9467bd", "#17becf", "#2ca02c"],
            )
            ax.set_title("Optimization Events")
            fig.tight_layout()
            fig.savefig(path, dpi=120)
            plt.close(fig)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.warning("optimization events plot failed: %s", exc)
            return None
