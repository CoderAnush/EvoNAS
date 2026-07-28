"""PSO convergence / fitness visualization (matplotlib optional)."""

from __future__ import annotations

import logging
from pathlib import Path

from evonas.domain.optimization.history import SwarmHistory

logger = logging.getLogger(__name__)


class PSOVisualizer:
    """Generate simple convergence plots from SwarmHistory."""

    def plot_convergence(self, history: SwarmHistory, path: str | Path) -> Path | None:
        """Plot global-best fitness over iterations. Returns path or None if skipped."""
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
        """Write standard plot set; missing matplotlib yields empty dict."""
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
        # Combined plot
        combined = self._plot_combined(history, out / "fitness_history.png")
        if combined is not None:
            written["fitness_history.png"] = str(combined)
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
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            logger.info("matplotlib not installed; skipping plot %s", path)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("matplotlib unavailable (%s); skipping plot %s", exc, path)
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
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            return None
        except Exception:
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
