"""Research report markdown generator (methodology + honest results)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_report(payload: dict[str, Any], path: str | Path) -> Path:
    """Write a structured experiment report (no optimizer favoritism)."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    meta = payload.get("meta") or {}
    results = payload.get("results") or {}
    stats = payload.get("statistics") or {}
    threats = payload.get("threats_to_validity") or _default_threats()
    limitations = payload.get("limitations") or _default_limitations()
    future = payload.get("future_work") or _default_future()

    lines = [
        f"# Experiment Report — {meta.get('experiment_id', 'unnamed')}",
        "",
        "## Summary",
        "",
        f"- **EvoNAS version:** {meta.get('evonas_version', '—')}",
        f"- **Git commit:** {meta.get('git_commit', '—')}",
        f"- **Config hash:** {meta.get('config_hash', '—')}",
        f"- **Seeds:** {meta.get('seeds', '—')}",
        f"- **Algorithms:** {', '.join(meta.get('algorithms', []) or [])}",
        f"- **Search space / landscape:** {meta.get('space', '—')} / {meta.get('landscape', '—')}",
        f"- **Winner (by mean fitness):** {results.get('winner', '—')}",
        "",
        "> Reporting is unbiased: the winner is determined solely by configured "
        "fitness sense and recorded metrics.",
        "",
        "## Methodology",
        "",
        "1. Identical search space, evaluation budget, and seeds across algorithms.",
        "2. Independent multi-seed runs with frozen configuration snapshots.",
        "3. Descriptive statistics: mean, median, variance, std, confidence intervals "
        f"(method: `{stats.get('ci_method', 'normal_approx')}`).",
        "4. Optional paired Wilcoxon signed-rank tests when enabled and applicable.",
        "5. Effect size: Cliff's δ (non-parametric).",
        "",
        "## Results",
        "",
        "```json",
        _json_block(results),
        "```",
        "",
        "## Statistical Analysis",
        "",
        "```json",
        _json_block(stats),
        "```",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in limitations)
    lines.extend(["", "## Threats to Validity", ""])
    lines.extend(f"- {item}" for item in threats)
    lines.extend(["", "## Future Work", ""])
    lines.extend(f"- {item}" for item in future)
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Run directory: `{meta.get('run_dir', '—')}`",
            f"- Figures: `{meta.get('figures_dir', '—')}`",
            f"- Tables: `{meta.get('tables_dir', '—')}`",
            "",
        ]
    )
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def _json_block(data: Any) -> str:
    import json

    return json.dumps(data, indent=2, default=str)


def _default_limitations() -> list[str]:
    return [
        "Mock fitness landscapes do not capture full neural training noise.",
        "Evaluation budgets are modest by design for CI / Quick Mode.",
        "Hardware variability may affect wall-clock comparisons.",
    ]


def _default_threats() -> list[str]:
    return [
        "Internal: seed selection and budget choices may favor or disfavor some methods.",
        "External: results on Sphere/Rastrigin may not transfer to large CNN spaces.",
        "Construct: mock fitness may imperfectly proxy validation accuracy.",
        "Conclusion: optional significance tests assume paired identical seeds.",
    ]


def _default_future() -> list[str]:
    return [
        "Scale multi-seed counts (20–50) on larger spaces for publication tables.",
        "Add Grid Search baseline when discrete spaces are fixed for a paper.",
        "Publish full Replay packages alongside paper supplements.",
    ]
