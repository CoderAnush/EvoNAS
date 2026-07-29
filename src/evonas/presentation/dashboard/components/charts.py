"""Plotly chart helpers for the dashboard."""

from __future__ import annotations

from typing import Any


def _go() -> Any:
    import plotly.graph_objects as go  # type: ignore[import-untyped]

    return go


def line_chart(
    xs: list[Any],
    series: dict[str, list[Any]],
    *,
    title: str,
    x_title: str = "iteration",
    y_title: str = "value",
) -> Any:
    """Multi-series line chart."""
    go = _go()
    fig = go.Figure()
    for name, ys in series.items():
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=name))
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=360,
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def bar_chart(labels: list[str], values: list[float], *, title: str) -> Any:
    """Simple bar chart."""
    go = _go()
    fig = go.Figure(data=[go.Bar(x=labels, y=values)])
    fig.update_layout(title=title, template="plotly_dark", height=320, margin=dict(l=40, r=20, t=50, b=40))
    return fig


def fitness_from_history(history: dict[str, Any]) -> Any | None:
    """Build fitness chart from swarm history."""
    records = history.get("records") or []
    if not records:
        return None
    xs = [r.get("iteration") for r in records]
    series = {
        "gbest": [r.get("gbest_fitness") for r in records],
    }
    if any("mean_fitness" in r for r in records):
        series["mean"] = [r.get("mean_fitness") for r in records]
    return line_chart(xs, series, title="Fitness Convergence", y_title="fitness")


def coefficients_from_adaptive(adaptive: dict[str, Any]) -> Any | None:
    """w/c1/c2 chart."""
    records = adaptive.get("records") or []
    if not records:
        return None
    xs = [r.get("iteration") for r in records]
    return line_chart(
        xs,
        {
            "w": [r.get("w") for r in records],
            "c1": [r.get("c1") for r in records],
            "c2": [r.get("c2") for r in records],
        },
        title="SAPSO Coefficient Evolution",
    )


def diversity_from_adaptive(adaptive: dict[str, Any]) -> Any | None:
    """Diversity chart."""
    records = adaptive.get("records") or []
    if not records:
        return None
    xs = [r.get("iteration") for r in records]
    key = "normalized_diversity" if "normalized_diversity" in records[0] else "diversity"
    return line_chart(
        xs,
        {"diversity": [r.get(key) for r in records]},
        title="Swarm Diversity",
        y_title="diversity",
    )


def drift_chart(drift_reports: list[dict[str, Any]]) -> Any | None:
    """PSI drift history."""
    if not drift_reports:
        return None
    xs = list(range(len(drift_reports)))
    return line_chart(
        xs,
        {"psi": [float(d.get("psi", 0)) for d in drift_reports]},
        title="Drift History (PSI)",
        x_title="report",
        y_title="PSI",
    )


def training_curves(history: dict[str, Any]) -> Any | None:
    """Train/val curves."""
    epochs = history.get("epochs") or []
    if not epochs:
        return None
    xs = [e.get("epoch") for e in epochs]
    series: dict[str, list[Any]] = {}
    if "train_loss" in epochs[0]:
        series["train_loss"] = [e.get("train_loss") for e in epochs]
    if "val_loss" in epochs[0]:
        series["val_loss"] = [e.get("val_loss") for e in epochs]
    if "train_accuracy" in epochs[0]:
        series["train_acc"] = [e.get("train_accuracy") for e in epochs]
    if "val_accuracy" in epochs[0]:
        series["val_acc"] = [e.get("val_accuracy") for e in epochs]
    if not series:
        return None
    return line_chart(xs, series, title="Training Curves", x_title="epoch")
