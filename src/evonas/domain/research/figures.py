"""Publication-quality figures (Matplotlib Agg) for research reports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)


def _pyplot() -> Any:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        logger.warning("matplotlib not installed — skipping publication figures")
        return None


def save_formats(fig: Any, path_stem: Path, *, formats: Sequence[str] = ("png", "svg", "pdf")) -> list[Path]:
    """Save a figure in multiple formats."""
    written: list[Path] = []
    for fmt in formats:
        out = path_stem.with_suffix(f".{fmt}")
        fig.savefig(out, dpi=200, bbox_inches="tight")
        written.append(out)
    return written


class PublicationFigures:
    """Generate consistent research figures without duplicating optimizer logic."""

    def __init__(self, *, style: str = "seaborn-v0_8-whitegrid") -> None:
        self._style = style

    def fitness_convergence(
        self,
        series: Mapping[str, Sequence[float]],
        out_dir: str | Path,
        *,
        title: str = "Fitness convergence",
        ylabel: str = "Best fitness",
        formats: Sequence[str] = ("png", "svg", "pdf"),
    ) -> list[Path]:
        """Multi-algorithm mean fitness curves (iteration index on x)."""
        plt = _pyplot()
        if plt is None:
            return []
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        try:
            plt.style.use(self._style)
        except Exception:  # noqa: BLE001
            pass
        fig, ax = plt.subplots(figsize=(6.4, 4.0))
        for name, values in series.items():
            ax.plot(range(1, len(values) + 1), list(values), label=name, linewidth=2)
        ax.set_xlabel("Iteration / trial")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        paths = save_formats(fig, out / "fitness_convergence", formats=formats)
        plt.close(fig)
        return paths

    def bar_comparison(
        self,
        labels: Sequence[str],
        values: Sequence[float],
        errors: Sequence[float] | None,
        out_dir: str | Path,
        *,
        title: str,
        ylabel: str,
        stem: str,
        formats: Sequence[str] = ("png", "svg", "pdf"),
    ) -> list[Path]:
        """Bar chart with optional error bars (e.g. mean ± std)."""
        plt = _pyplot()
        if plt is None:
            return []
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(6.4, 4.0))
        x = range(len(labels))
        ax.bar(x, list(values), yerr=list(errors) if errors else None, capsize=4, color="#2a6f97")
        ax.set_xticks(list(x))
        ax.set_xticklabels(list(labels), rotation=15)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.3)
        paths = save_formats(fig, out / stem, formats=formats)
        plt.close(fig)
        return paths

    def coefficient_evolution(
        self,
        records: Sequence[dict[str, Any]],
        out_dir: str | Path,
        *,
        formats: Sequence[str] = ("png", "svg", "pdf"),
    ) -> list[Path]:
        """Plot w/c1/c2 when present in adaptive history records."""
        plt = _pyplot()
        if plt is None or not records:
            return []
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        iters = [r.get("iteration", i + 1) for i, r in enumerate(records)]
        fig, ax = plt.subplots(figsize=(6.4, 4.0))
        for key, label in (("w", "w"), ("c1", "c1"), ("c2", "c2")):
            if any(key in r for r in records):
                ax.plot(iters, [r.get(key) for r in records], label=label, linewidth=2)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Coefficient")
        ax.set_title("SAPSO coefficient evolution")
        ax.legend()
        ax.grid(True, alpha=0.3)
        paths = save_formats(fig, out / "coefficient_evolution", formats=formats)
        plt.close(fig)
        return paths

    def diversity_evolution(
        self,
        records: Sequence[dict[str, Any]],
        out_dir: str | Path,
        *,
        key: str = "diversity",
        formats: Sequence[str] = ("png", "svg", "pdf"),
    ) -> list[Path]:
        """Swarm diversity over iterations."""
        plt = _pyplot()
        if plt is None or not records:
            return []
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        iters = [r.get("iteration", i + 1) for i, r in enumerate(records)]
        vals = [r.get(key, r.get("normalized_diversity")) for r in records]
        fig, ax = plt.subplots(figsize=(6.4, 4.0))
        ax.plot(iters, vals, color="#c1121f", linewidth=2)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Diversity")
        ax.set_title("Swarm diversity")
        ax.grid(True, alpha=0.3)
        paths = save_formats(fig, out / "diversity_evolution", formats=formats)
        plt.close(fig)
        return paths
