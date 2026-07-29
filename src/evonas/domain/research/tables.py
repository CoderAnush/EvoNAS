"""Publication tables — CSV, Markdown, LaTeX (honest reporting)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence


def write_csv(rows: Sequence[dict[str, Any]], path: str | Path) -> Path:
    """Write list-of-dicts as CSV."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        file_path.write_text("", encoding="utf-8")
        return file_path
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})
    return file_path


def to_markdown(rows: Sequence[dict[str, Any]], *, title: str | None = None) -> str:
    """Render a GitHub-flavored markdown table."""
    if not rows:
        return (f"### {title}\n\n_(empty)_\n" if title else "_(empty)_\n")
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    lines: list[str] = []
    if title:
        lines.append(f"### {title}")
        lines.append("")
    lines.append("| " + " | ".join(keys) + " |")
    lines.append("| " + " | ".join("---" for _ in keys) + " |")
    for row in rows:
        cells = [_fmt(row.get(k)) for k in keys]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def to_latex(rows: Sequence[dict[str, Any]], *, caption: str = "Results", label: str = "tab:results") -> str:
    """Render a simple booktabs-style LaTeX table."""
    if not rows:
        return f"% empty table: {caption}\n"
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    cols = "l" * len(keys)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{_tex(caption)}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{cols}}}",
        r"\toprule",
        " & ".join(_tex(k) for k in keys) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(_tex(_fmt(row.get(k))) for k in keys) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def write_table_bundle(
    rows: Sequence[dict[str, Any]],
    out_dir: str | Path,
    *,
    stem: str,
    title: str,
) -> dict[str, str]:
    """Write CSV + Markdown + LaTeX for the same rows."""
    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv(rows, base / f"{stem}.csv")
    md = to_markdown(rows, title=title)
    md_path = base / f"{stem}.md"
    md_path.write_text(md, encoding="utf-8")
    tex = to_latex(rows, caption=title, label=f"tab:{stem}")
    tex_path = base / f"{stem}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return {"csv": str(csv_path), "markdown": str(md_path), "latex": str(tex_path)}


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _tex(text: str) -> str:
    return (
        str(text)
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )
