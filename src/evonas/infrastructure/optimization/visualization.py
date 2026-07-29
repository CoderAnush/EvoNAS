"""PSO / SAPSO visualization (matplotlib Agg, optional)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.domain.optimization.history import SwarmHistory

logger = logging.getLogger(__name__)


class PSOVisualizer:
    """Generate convergence and adaptive-coefficient plots."""

    def plot_convergence(self, history: SwarmHistory, path: str | Path) -> Path | None:
        """Plot global-best fitness over iterations."""
        return self._plot(
            history.best_fitness_curve(),
            path,
            title="PSO Global Best Fitness",
            ylabel="gbest fitness",
            label="gbest",
        )

    def plot_mean_fitness(self, history: SwarmHistory, path: str | Path) -> Path | None:
        """Plot mean swarm fitness over iterations."""
        return self._plot(
            history.mean_fitness_curve(),
            path,
            title="PSO Mean Swarm Fitness",
            ylabel="mean fitness",
            label="mean",
        )

    def plot_all(self, history: SwarmHistory, out_dir: str | Path) -> dict[str, str]:
        """Write standard fitness plot set."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        written: dict[str, str] = {}
        for name, fn in (
            ("convergence.png", self.plot_convergence),
            ("mean_fitness.png", self.plot_mean_fitness),
        ):
            path = fn(history, out / name)
            if path is not None:
                written[name] = str(path)
        combined = self._plot_combined(history, out / "fitness_history.png")
        if combined is not None:
            written["fitness_history.png"] = str(combined)
        return written

    def plot_adaptive(
        self, adaptive_payload: dict[str, Any], out_dir: str | Path
    ) -> dict[str, str]:
        """Plot w/c1/c2/diversity and phase timeline from SAPSO adaptive history."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        curves = adaptive_payload.get("curves", {})
        written: dict[str, str] = {}
        for key, ylabel, fname in (
            ("w", "inertia w", "inertia.png"),
            ("c1", "c1", "c1.png"),
            ("c2", "c2", "c2.png"),
            ("diversity", "normalized diversity", "diversity.png"),
        ):
            values = curves.get(key) or []
            if not values:
                continue
            path = self._plot(
                list(values),
                out / fname,
                title=f"SAPSO {ylabel}",
                ylabel=ylabel,
                label=key,
            )
            if path is not None:
                written[fname] = str(path)
        combo = self._plot_coeffs(curves, out / "coefficients.png")
        if combo is not None:
            written["coefficients.png"] = str(combo)
        phases = curves.get("phase") or []
        if phases:
            phase_path = self._plot_phases(list(phases), out / "state_transitions.png")
            if phase_path is not None:
                written["state_transitions.png"] = str(phase_path)
        return written

    def _plot(
        self,
        values: list[float],
        path: str | Path,
        *,
        title: str,
        ylabel: str,
        label: str,
    ) -> Path | None:
        plt = self._pyplot()
        if plt is None:
            return None
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(range(len(values)), values, label=label)
            ax.set_title(title)
            ax.set_xlabel("iteration")
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(file_path, dpi=120)
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to write plot %s: %s", file_path, exc)
            return None
        return file_path

    def _plot_combined(self, history: SwarmHistory, path: str | Path) -> Path | None:
        plt = self._pyplot()
        if plt is None:
            return None
        file_path = Path(path)
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(history.best_fitness_curve(), label="gbest")
            ax.plot(history.mean_fitness_curve(), label="mean")
            ax.set_title("PSO Fitness History")
            ax.set_xlabel("iteration")
            ax.set_ylabel("fitness")
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(file_path, dpi=120)
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to write combined plot: %s", exc)
            return None
        return file_path

    def _plot_coeffs(self, curves: dict[str, Any], path: str | Path) -> Path | None:
        plt = self._pyplot()
        if plt is None:
            return None
        file_path = Path(path)
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            for key in ("w", "c1", "c2"):
                vals = curves.get(key) or []
                if vals:
                    ax.plot(vals, label=key)
            ax.set_title("SAPSO Coefficient Trajectories")
            ax.set_xlabel("adaptation step")
            ax.set_ylabel("value")
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(file_path, dpi=120)
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed coeffs plot: %s", exc)
            return None
        return file_path

    def _plot_phases(self, phases: list[str], path: str | Path) -> Path | None:
        plt = self._pyplot()
        if plt is None:
            return None
        mapping = {
            "exploration": 0,
            "balanced": 1,
            "exploitation": 2,
            "stagnation_recovery": 3,
        }
        ys = [mapping.get(p, -1) for p in phases]
        file_path = Path(path)
        try:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.step(range(len(ys)), ys, where="post")
            ax.set_yticks(list(mapping.values()))
            ax.set_yticklabels(list(mapping.keys()))
            ax.set_title("SAPSO Adaptive Phase")
            ax.set_xlabel("adaptation step")
            fig.tight_layout()
            fig.savefig(file_path, dpi=120)
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed phase plot: %s", exc)
            return None
        return file_path

    @staticmethod
    def _pyplot() -> Any | None:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            return plt
        except Exception as exc:  # noqa: BLE001
            logger.info("matplotlib unavailable (%s)", exc)
            return None
